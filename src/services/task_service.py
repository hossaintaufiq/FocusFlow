"""Task CRUD, search, filter, sort, and archive operations."""

from __future__ import annotations

import logging
from datetime import date
from typing import Callable, Iterable

from src.models.task import Task, TaskCollection
from src.services.history_service import HistoryService
from src.services.storage import JsonStorage
from src.models.base import today_iso, utc_now_iso

logger = logging.getLogger("FocusFlow.tasks")


class TaskService:
    def __init__(self, storage: JsonStorage, history: HistoryService) -> None:
        self._storage = storage
        self._history = history
        self._data = storage.load("tasks", TaskCollection.from_dict, TaskCollection)

    @property
    def tasks(self) -> list[Task]:
        return list(self._data.tasks)

    def save(self) -> None:
        self._storage.save("tasks", self._data)

    def get(self, task_id: str) -> Task | None:
        for t in self._data.tasks:
            if t.id == task_id:
                return t
        return None

    def add(self, **kwargs) -> Task:
        task = Task(**kwargs)
        if not task.date:
            task.date = today_iso()
        task.sync_estimated_minutes()
        if task.status == "completed":
            task.completed = True
            if not task.completion_time:
                task.completion_time = utc_now_iso()
        self._data.tasks.append(task)
        self.save()
        self._history.log(
            "task_created",
            entity_type="task",
            entity_id=task.id,
            summary=f"Created task: {task.title}",
        )
        return task

    def update(self, task_id: str, **kwargs) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if hasattr(task, key) and key != "id":
                setattr(task, key, value)
        task.sync_estimated_minutes()
        if task.status == "completed" and not task.completed:
            task.mark_completed()
        elif task.status != "completed" and task.completed and "completed" in kwargs:
            if not kwargs.get("completed"):
                task.mark_incomplete()
                task.status = kwargs.get("status", "not_started")
        task.touch()
        self.save()
        self._history.log(
            "task_edited",
            entity_type="task",
            entity_id=task.id,
            summary=f"Edited task: {task.title}",
        )
        return task

    def delete(self, task_id: str) -> bool:
        task = self.get(task_id)
        if not task:
            return False
        self._data.tasks = [t for t in self._data.tasks if t.id != task_id]
        self.save()
        self._history.log(
            "task_deleted",
            entity_type="task",
            entity_id=task_id,
            summary=f"Deleted task: {task.title}",
        )
        return True

    def duplicate(self, task_id: str) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        copy = task.duplicate()
        self._data.tasks.append(copy)
        self.save()
        self._history.log(
            "task_duplicated",
            entity_type="task",
            entity_id=copy.id,
            summary=f"Duplicated task: {copy.title}",
        )
        return copy

    def archive(self, task_id: str) -> Task | None:
        task = self.update(task_id, archived=True)
        if task:
            self._history.log(
                "task_archived",
                entity_type="task",
                entity_id=task_id,
                summary=f"Archived task: {task.title}",
            )
        return task

    def restore(self, task_id: str) -> Task | None:
        task = self.update(task_id, archived=False)
        if task:
            self._history.log(
                "task_restored",
                entity_type="task",
                entity_id=task_id,
                summary=f"Restored task: {task.title}",
            )
        return task

    def toggle_favorite(self, task_id: str) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        return self.update(task_id, favorite=not task.favorite)

    def toggle_complete(self, task_id: str) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        if task.completed:
            task.mark_incomplete()
            action = "task_uncompleted"
        else:
            task.mark_completed()
            action = "task_completed"
        self.save()
        self._history.log(
            action,
            entity_type="task",
            entity_id=task.id,
            summary=f"{'Completed' if task.completed else 'Reopened'}: {task.title}",
        )
        return task

    def add_time(self, task_id: str, seconds: int, *, persist: bool = True) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        task.actual_seconds = max(0, task.actual_seconds + seconds)
        task.touch()
        if persist:
            self.save()
        return task

    def today(self, include_archived: bool = False) -> list[Task]:
        today = today_iso()
        return [
            t
            for t in self._data.tasks
            if (include_archived or not t.archived)
            and (t.date == today or (t.deadline[:10] == today if t.deadline else False))
        ]

    def upcoming(self, limit: int = 10) -> list[Task]:
        today = date.today()
        items = []
        for t in self._data.tasks:
            if t.archived or t.completed:
                continue
            raw = t.deadline or t.date
            if not raw:
                continue
            try:
                d = date.fromisoformat(raw[:10])
            except ValueError:
                continue
            if d >= today:
                items.append((d, t))
        items.sort(key=lambda x: x[0])
        return [t for _, t in items[:limit]]

    def search(self, query: str, *, include_archived: bool = False) -> list[Task]:
        q = query.lower().strip()
        result = []
        for t in self._data.tasks:
            if not include_archived and t.archived:
                continue
            hay = " ".join(
                [
                    t.title,
                    t.description,
                    t.category,
                    t.project_id,
                    " ".join(t.tags),
                    t.date,
                    t.notes,
                ]
            ).lower()
            if not q or q in hay:
                result.append(t)
        return result

    def filter(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        project_id: str | None = None,
        category: str | None = None,
        completed: bool | None = None,
        favorite: bool | None = None,
        archived: bool = False,
        tag: str | None = None,
    ) -> list[Task]:
        out = []
        for t in self._data.tasks:
            if t.archived != archived:
                continue
            if status and t.status != status:
                continue
            if priority and t.priority != priority:
                continue
            if project_id and t.project_id != project_id:
                continue
            if category and t.category != category:
                continue
            if completed is not None and t.completed != completed:
                continue
            if favorite is not None and t.favorite != favorite:
                continue
            if tag and tag not in t.tags:
                continue
            out.append(t)
        return out

    def sort_tasks(
        self,
        tasks: Iterable[Task],
        key: str = "updated_at",
        reverse: bool = True,
    ) -> list[Task]:
        priority_rank = {"urgent": 0, "high": 1, "medium": 2, "low": 3}

        def sorter(t: Task):
            if key == "priority":
                return priority_rank.get(t.priority, 9)
            if key == "title":
                return t.title.lower()
            if key == "deadline":
                return t.deadline or "9999"
            if key == "date":
                return t.date or "9999"
            return getattr(t, key, "")

        return sorted(list(tasks), key=sorter, reverse=reverse)

    def group_by(self, tasks: Iterable[Task], key: str = "category") -> dict[str, list[Task]]:
        groups: dict[str, list[Task]] = {}
        for t in tasks:
            k = str(getattr(t, key, "") or "Ungrouped")
            groups.setdefault(k, []).append(t)
        return groups

    def reorder(self, ordered_ids: list[str]) -> None:
        index = {tid: i for i, tid in enumerate(ordered_ids)}
        for t in self._data.tasks:
            if t.id in index:
                t.order = index[t.id]
        self._data.tasks.sort(key=lambda t: t.order)
        self.save()

    def counts_today(self) -> dict[str, int]:
        today_tasks = self.today()
        completed = sum(1 for t in today_tasks if t.completed)
        pending = sum(1 for t in today_tasks if not t.completed)
        return {
            "total": len(today_tasks),
            "completed": completed,
            "pending": pending,
        }
