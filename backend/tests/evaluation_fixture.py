"""Synthetic completed report with deliberate failed evidence and excluded routing cases."""

import uuid


def report(workspace_id):
    strategies = {}
    for name in ("vector", "bm25", "hybrid", "vector_rerank", "hybrid_rerank"):
        strategy = "cosine20-mmarco-rerank-v2" if name == "vector_rerank" else name + "-v1"

        def probe(question):
            return dict(
                question=question,
                trace=dict(id=str(uuid.uuid4()), query=question, status="succeeded", strategy=strategy),
                trace_valid=True,
                candidate_leakage=[],
                leakage=[],
                result_bound_violated=False,
            )

        cases = []
        for language in ("en", "ja", "zh"):
            for index in range(10):
                groups = [["Policy"]] if index < (8 if language == "en" else 9) else []
                if language == "ja" and index == 0:
                    groups.append(["Second policy"])
                failed = language == "ja" and index == 1 and name != "vector_rerank"
                cases.append(
                    dict(
                        **probe(f"Question {language}{index}"),
                        id=f"{language}{index}",
                        language=language,
                        groups=groups,
                        groups_found=0 if failed else len(groups),
                        retrieval_passed=(not failed) if groups else None,
                        fact_results=[not failed] if groups else [],
                        elapsed_seconds=1 + index / 10,
                    )
                )
        strategies[name] = dict(
            cases=cases,
            negative_probes=[probe("Withdrawal probe"), probe("Foreign probe")],
            foreign_request_status=404,
            scores={"untrusted_aggregate": "must not be displayed"},
        )
    return dict(
        experiment="retrieval-strategies-v1",
        status="completed",
        generation="not_verified",
        scorer_version="active-required-sections-v2",
        source_unchanged=True,
        runtime_unchanged=True,
        experiment_valid=True,
        source_state=dict(commit="a" * 40, source_sha256="b" * 64),
        frozen=dict(recall_at=5, files={"synthetic": "c" * 64}),
        workspaces=dict(primary=str(workspace_id), foreign=str(uuid.uuid4())),
        strategies=strategies,
        documents=[dict(private_document="DO_NOT_EXPOSE_FOREIGN_DATA")],
        runtime=dict(local_path="DO_NOT_EXPOSE_RUNTIME"),
    )
