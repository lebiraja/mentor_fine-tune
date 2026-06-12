"""Persona registry + persona-scoped pipeline behavior (greeting, memory)."""

import asyncio

import numpy as np
import pytest

from backend.core.personas import PersonaRegistry
from tests.conftest import FakeLLM, FakePersonaRegistry


# ---- registry (loads real config/personas/*.yaml) ----


def test_registry_loads_all_personas():
    reg = PersonaRegistry()
    ids = {p["id"] for p in reg.list()}
    assert {"clarity", "engineer", "general", "coach", "friend"} <= ids


def test_registry_default_is_clarity():
    reg = PersonaRegistry()
    assert reg.get(None).id == "clarity"
    assert reg.get("nonexistent").id == "clarity"


def test_registry_clarity_listed_first():
    reg = PersonaRegistry()
    assert reg.list()[0]["id"] == "clarity"


def test_friend_has_memory_and_proactive_flags():
    reg = PersonaRegistry()
    friend = reg.get("friend")
    assert friend.proactive and friend.cross_session_memory
    clarity = reg.get("clarity")
    assert not clarity.proactive and not clarity.cross_session_memory


def test_render_prompt_injects_memory():
    reg = PersonaRegistry()
    friend = reg.get("friend")
    rendered = friend.render_prompt("- They were stressed about a demo.")
    assert "stressed about a demo" in rendered
    assert "{memory}" not in rendered
    # first-time fallback when no memory
    assert "first time" in friend.render_prompt(None).lower()


# ---- pipeline: persona is locked per session ----


async def test_new_session_adopts_chosen_persona(make_pipeline, db):
    pipeline = make_pipeline()
    sid = await pipeline.set_session(None, "friend")
    assert pipeline.persona.id == "friend"
    assert await db.get_session_persona(sid) == "friend"


async def test_resumed_session_keeps_stored_persona(make_pipeline, db):
    pipeline = make_pipeline()
    sid = await pipeline.set_session(None, "friend")

    # Resume asking for a different persona — stored one wins.
    other = make_pipeline()
    resumed = await other.set_session(sid, "clarity")
    assert resumed == sid
    assert other.persona.id == "friend"


# ---- Friend: proactive greeting ----


async def test_friend_greets_on_fresh_session(make_pipeline, collector):
    pipeline = make_pipeline(llm=FakeLLM(deltas=["Hey, you're back. "]))
    await pipeline.set_session(None, "friend")
    assert pipeline._turn_task is not None
    await pipeline._turn_task

    greetings = collector.events("assistant_greeting")
    assert greetings, "Friend should greet proactively"
    assert "".join(g["text"] for g in greetings).startswith("Hey")


async def test_clarity_does_not_greet(make_pipeline, collector):
    pipeline = make_pipeline()
    await pipeline.set_session(None, "clarity")
    assert pipeline._turn_task is None
    assert collector.events("assistant_greeting") == []


# ---- Friend: cross-session memory ----


async def test_friend_summarizes_on_shutdown(make_pipeline, db):
    pipeline = make_pipeline(llm=FakeLLM(deltas=["They seem tired but hopeful."]))
    sid = await pipeline.set_session(None, "friend")
    # skip the greeting task
    if pipeline._turn_task:
        await pipeline._turn_task
    await db.add_message(sid, "user", "work was rough today")
    await db.add_message(sid, "assistant", "that sounds heavy")

    await pipeline.shutdown()

    memories = await db.get_memories("friend")
    assert memories and "tired but hopeful" in memories[0]


async def test_memory_loaded_into_next_friend_session(make_pipeline, db):
    await db.save_memory("friend", "old-session", "They are learning to cook.")
    pipeline = make_pipeline()
    await pipeline.set_session(None, "friend")
    assert "learning to cook" in pipeline.system_prompt


async def test_no_memory_for_short_conversations(make_pipeline, db):
    pipeline = make_pipeline()
    sid = await pipeline.set_session(None, "friend")
    if pipeline._turn_task:
        pipeline._turn_task.cancel()
        try:
            await pipeline._turn_task
        except asyncio.CancelledError:
            pass
    # Only the (cancelled) greeting, nothing real said
    await pipeline.shutdown()
    # Greeting may have persisted 0-1 messages; a <2-message convo isn't summarized
    history = await db.get_messages(sid)
    if len(history) < 2:
        assert await db.get_memories("friend") == []
