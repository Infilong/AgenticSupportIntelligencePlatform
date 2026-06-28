from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.language import LanguageDetectionError, detect_language_for_messages
from app.models.dataset import (
    ConversationExample,
    Dataset,
    ExampleStatus,
    ImportBatch,
    ImportSourceType,
    ImportStatus,
    Label,
    LabelSource,
    LabelType,
    Message,
)
from app.models.user import User
from app.services.folder_service import ResourceFolderService
from app.services.import_parser import ImportParseError, parse_import_content


class DatasetNotFoundError(ValueError):
    pass


class ExampleNotFoundError(ValueError):
    pass


class DatasetImportError(ValueError):
    pass


@dataclass(frozen=True)
class DatasetImportResult:
    dataset: Dataset
    import_batch: ImportBatch
    imported_examples: int


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    def import_dataset(
        self,
        *,
        workspace_id: UUID,
        dataset_name: str,
        description: str | None,
        source_type: ImportSourceType,
        content: str,
        folder_id: UUID | None = None,
    ) -> DatasetImportResult:
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="dataset"
        )
        dataset = Dataset(
            workspace_id=workspace_id,
            name=dataset_name.strip(),
            description=description,
            folder_id=folder_id,
        )
        self.db.add(dataset)
        self.db.flush()

        import_batch = ImportBatch(
            workspace_id=workspace_id,
            dataset_id=dataset.id,
            source_type=source_type,
            status=ImportStatus.completed,
        )
        self.db.add(import_batch)
        self.db.flush()

        try:
            parsed_examples = parse_import_content(source_type.value, content)
            for parsed_example in parsed_examples:
                language = detect_language_for_messages(
                    [message.content for message in parsed_example.messages]
                )
                example = ConversationExample(
                    workspace_id=workspace_id,
                    dataset_id=dataset.id,
                    import_batch_id=import_batch.id,
                    external_id=parsed_example.external_id,
                    language=language,
                    status=ExampleStatus.imported,
                )
                self.db.add(example)
                self.db.flush()

                for parsed_message in parsed_example.messages:
                    message_language = detect_language_for_messages([parsed_message.content])
                    self.db.add(
                        Message(
                            workspace_id=workspace_id,
                            conversation_example_id=example.id,
                            role=parsed_message.role,
                            language=message_language,
                            content=parsed_message.content,
                        )
                    )

                for label_type, value in parsed_example.labels.items():
                    self.db.add(
                        Label(
                            workspace_id=workspace_id,
                            conversation_example_id=example.id,
                            label_type=label_type,
                            value=value,
                            source=LabelSource.import_,
                        )
                    )
        except (ImportParseError, LanguageDetectionError) as exc:
            import_batch.status = ImportStatus.failed
            import_batch.error_message = str(exc)
            self.db.commit()
            self.db.refresh(dataset)
            self.db.refresh(import_batch)
            raise DatasetImportError(str(exc)) from exc

        self.db.commit()
        self.db.refresh(dataset)
        self.db.refresh(import_batch)
        return DatasetImportResult(
            dataset=dataset,
            import_batch=import_batch,
            imported_examples=len(parsed_examples),
        )

    def list_datasets(self, *, workspace_id: UUID, folder_id: UUID | None = None) -> list[Dataset]:
        conditions = [Dataset.workspace_id == workspace_id]
        if folder_id is not None:
            ResourceFolderService(self.db).validate_folder(
                workspace_id=workspace_id, folder_id=folder_id, resource_type="dataset"
            )
            conditions.append(Dataset.folder_id == folder_id)
        statement = select(Dataset).where(*conditions).order_by(Dataset.created_at.desc())
        return list(self.db.scalars(statement).all())

    def list_examples(self, *, workspace_id: UUID, dataset_id: UUID) -> list[ConversationExample]:
        if self.get_dataset(workspace_id=workspace_id, dataset_id=dataset_id) is None:
            raise DatasetNotFoundError("Dataset was not found.")
        statement = (
            select(ConversationExample)
            .options(
                selectinload(ConversationExample.messages),
                selectinload(ConversationExample.labels),
            )
            .where(
                ConversationExample.workspace_id == workspace_id,
                ConversationExample.dataset_id == dataset_id,
            )
            .order_by(ConversationExample.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def upsert_human_label(
        self,
        *,
        workspace_id: UUID,
        example_id: UUID,
        label_type: LabelType,
        value: str,
        current_user: User,
    ) -> Label:
        example = self.get_example(workspace_id=workspace_id, example_id=example_id)
        if example is None:
            raise ExampleNotFoundError("Example was not found.")

        statement = select(Label).where(
            Label.workspace_id == workspace_id,
            Label.conversation_example_id == example.id,
            Label.label_type == label_type,
            Label.source == LabelSource.human,
        )
        label = self.db.scalar(statement)
        if label is None:
            label = Label(
                workspace_id=workspace_id,
                conversation_example_id=example.id,
                label_type=label_type,
                value=value.strip(),
                source=LabelSource.human,
                created_by_user_id=current_user.id,
            )
            self.db.add(label)
        else:
            label.value = value.strip()
            label.created_by_user_id = current_user.id

        self.db.commit()
        self.db.refresh(label)
        return label

    def move_dataset(
        self, *, workspace_id: UUID, dataset_id: UUID, folder_id: UUID | None
    ) -> Dataset:
        dataset = self.get_dataset(workspace_id=workspace_id, dataset_id=dataset_id)
        if dataset is None:
            raise DatasetNotFoundError("Dataset was not found.")
        ResourceFolderService(self.db).validate_folder(
            workspace_id=workspace_id, folder_id=folder_id, resource_type="dataset"
        )
        dataset.folder_id = folder_id
        self.db.commit()
        self.db.refresh(dataset)
        return dataset

    def delete_dataset(self, *, workspace_id: UUID, dataset_id: UUID) -> None:
        dataset = self.get_dataset(workspace_id=workspace_id, dataset_id=dataset_id)
        if dataset is None:
            raise DatasetNotFoundError("Dataset was not found.")
        self.db.delete(dataset)
        self.db.commit()

    def get_dataset(self, *, workspace_id: UUID, dataset_id: UUID) -> Dataset | None:
        statement = select(Dataset).where(
            Dataset.workspace_id == workspace_id,
            Dataset.id == dataset_id,
        )
        return self.db.scalar(statement)

    def get_example(
        self, *, workspace_id: UUID, example_id: UUID
    ) -> ConversationExample | None:
        statement = select(ConversationExample).where(
            ConversationExample.workspace_id == workspace_id,
            ConversationExample.id == example_id,
        )
        return self.db.scalar(statement)
