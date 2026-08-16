"""Layer 5 — long-term memory."""

from __future__ import annotations

import os

os.environ["FIGUREITOUT_MOCK"] = "1"

from figureitout.memory import get_similar_past_tasks, save_task_result
from figureitout.planner import Task


def test_save_and_recall_similar_task():
    task = Task(
        name="build_todo",
        description="build a todo app with local storage",
        success_criteria="CRUD works",
        task_type="code",
    )
    save_task_result(task, "Implemented todo CRUD with sqlite", 88.0, "")
    similar = Task(
        name="todo_v2",
        description="build a todo application",
        success_criteria="Works offline",
        task_type="code",
    )
    recalled = get_similar_past_tasks(similar)
    assert "todo" in recalled.lower()
    assert "sqlite" in recalled.lower() or "CRUD" in recalled or "Implemented" in recalled


def test_empty_search_returns_string():
    task = Task(
        name="unique_xyz_no_match_zzz",
        description="unique_xyz_no_match_zzz obscure query",
        success_criteria="n/a",
        task_type="analyse",
    )
    assert isinstance(get_similar_past_tasks(task), str)
