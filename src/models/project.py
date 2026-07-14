"""Project domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.base import JsonMixin, new_id, utc_now_iso


@dataclass
class Project(JsonMixin):
    """A colored container grouping related tasks."""

    id: str = field(default_factory=lambda: new_id("proj"))
    name: str = ""
    description: str = ""
    color: str = "#38BDF8"
    icon: str = "folder"
    deadline: str = ""
    archived: bool = False
    favorite: bool = False
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    # Denormalized counts refreshed by services
    task_count: int = 0
    completed_count: int = 0

    @property
    def progress_percent(self) -> float:
        if self.task_count <= 0:
            return 0.0
        return round(100.0 * self.completed_count / self.task_count, 1)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()


@dataclass
class ProjectCollection(JsonMixin):
    """Root document for ``projects.json``."""

    version: int = 1
    projects: list[Project] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "projects": [p.to_dict() for p in self.projects],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectCollection:
        projects = [Project.from_dict(p) for p in data.get("projects", [])]
        return cls(version=int(data.get("version", 1)), projects=projects)
