"""Supported-library persistence contract; this is not the application's support workflow."""

import uuid
from typing import TypedDict

import psycopg
import pytest
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from psycopg.rows import dict_row


class State(TypedDict, total=False):
    original: str
    prepared: str
    response: str


def connection(system):
    # Keep the test fixture's isolated schema; never initialize app/public checkpoint tables.
    url = system["engine"].url
    # libpq does not decode '+' as spaces in SQLAlchemy-rendered URI query parameters.
    return psycopg.connect(
        **url.translate_connect_args(username="user", database="dbname"),
        options=url.query["options"],
        autocommit=True,
        row_factory=dict_row,
    )


def builder(generate):
    graph = StateGraph(State)
    graph.add_node("prepare", lambda state: {"prepared": state["original"]})
    graph.add_node("generate", generate)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "generate")
    graph.add_edge("generate", END)
    return graph


def wait_for_development_response(state):
    answer = interrupt({"reason": "development_generation", "original": state["prepared"]})
    return {"response": answer}


def test_interrupt_survives_closed_connection_and_rebuilt_graph(system):
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    original = "返金について / 关于退款 / refund question"
    with connection(system) as db:
        saver = PostgresSaver(db)
        saver.setup()
        saver.setup()  # Explicit initialization is idempotent on this dedicated schema.
        graph = builder(wait_for_development_response).compile(checkpointer=saver)
        paused = graph.invoke({"original": original}, config, durability="sync")
        assert paused["__interrupt__"][0].value == {
            "reason": "development_generation",
            "original": original,
        }
        assert graph.get_state(config).next == ("generate",)
    assert db.closed

    with connection(system) as reopened:
        saver = PostgresSaver(reopened)
        restored = builder(wait_for_development_response).compile(checkpointer=saver)
        assert restored.get_state(config).values["original"] == original
        unrelated = {"configurable": {"thread_id": str(uuid.uuid4())}}
        assert restored.get_state(unrelated).values == {}  # Storage separation, not authorization proof.
        completed = restored.invoke(Command(resume="Explicit synthetic response"), config, durability="sync")
        assert completed["response"] == "Explicit synthetic response"
        assert restored.get_state(config).next == ()

    with connection(system) as reopened:
        final = builder(wait_for_development_response).compile(checkpointer=PostgresSaver(reopened))
        assert final.get_state(config).values["response"] == "Explicit synthetic response"
        assert len(list(final.get_state_history(config))) >= 3


def test_failed_node_resumes_from_persisted_predecessor(system):
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    def broken(state):
        raise RuntimeError("synthetic provider failure")

    with connection(system) as db:
        saver = PostgresSaver(db)
        saver.setup()
        graph = builder(broken).compile(checkpointer=saver)
        with pytest.raises(RuntimeError, match="synthetic provider failure"):
            graph.invoke({"original": "Preserve this customer input"}, config, durability="sync")
        snapshot = graph.get_state(config)
        assert snapshot.values["prepared"] == "Preserve this customer input"
        assert snapshot.next == ("generate",)
        assert snapshot.tasks[0].error is not None

    with connection(system) as reopened:
        recovered = builder(lambda state: {"response": state["prepared"]}).compile(
            checkpointer=PostgresSaver(reopened)
        )
        assert recovered.invoke(None, config, durability="sync")["response"] == "Preserve this customer input"
        assert recovered.get_state(config).next == ()
