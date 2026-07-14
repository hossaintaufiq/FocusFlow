"""Project management service."""

from __future__ import annotations

from src.models.project import Project, ProjectCollection
from src.services.history_service import HistoryService
from src.services.storage import JsonStorage
from src.services.task_service import TaskService


class ProjectService:
    def __init__(
        self,
        storage: JsonStorage,
        history: HistoryService,
        tasks: TaskService | None = None,
    ) -> None:
        self._storage = storage
        self._history = history
        self._tasks = tasks
        self._data = storage.load(
            "projects", ProjectCollection.from_dict, ProjectCollection
        )

    @property
    def projects(self) -> list[Project]:
        return [p for p in self._data.projects if not p.archived]

    def all(self) -> list[Project]:
        return list(self._data.projects)

    def save(self) -> None:
        self._storage.save("projects", self._data)

    def get(self, project_id: str) -> Project | None:
        for p in self._data.projects:
            if p.id == project_id:
                return p
        return None

    def add(self, **kwargs) -> Project:
        project = Project(**kwargs)
        self._data.projects.append(project)
        self.save()
        self._history.log(
            "project_created",
            entity_type="project",
            entity_id=project.id,
            summary=f"Created project: {project.name}",
        )
        return project

    def update(self, project_id: str, **kwargs) -> Project | None:
        project = self.get(project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key) and key != "id":
                setattr(project, key, value)
        project.touch()
        self.save()
        self._history.log(
            "project_edited",
            entity_type="project",
            entity_id=project.id,
            summary=f"Edited project: {project.name}",
        )
        return project

    def delete(self, project_id: str) -> bool:
        project = self.get(project_id)
        if not project:
            return False
        self._data.projects = [p for p in self._data.projects if p.id != project_id]
        self.save()
        self._history.log(
            "project_deleted",
            entity_type="project",
            entity_id=project_id,
            summary=f"Deleted project: {project.name}",
        )
        return True

    def refresh_counts(self) -> None:
        if not self._tasks:
            return
        for project in self._data.projects:
            related = [
                t
                for t in self._tasks.tasks
                if t.project_id == project.id and not t.archived
            ]
            project.task_count = len(related)
            project.completed_count = sum(1 for t in related if t.completed)
        self.save()

    def set_task_service(self, tasks: TaskService) -> None:
        self._tasks = tasks
