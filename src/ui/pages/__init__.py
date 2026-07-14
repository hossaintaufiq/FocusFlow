"""UI pages package."""

from src.ui.pages.calendar_page import CalendarPage
from src.ui.pages.dashboard_page import DashboardPage
from src.ui.pages.extras_page import ExtrasPage
from src.ui.pages.habits_page import HabitsPage
from src.ui.pages.history_page import HistoryPage
from src.ui.pages.notes_page import NotesPage
from src.ui.pages.pomodoro_page import PomodoroPage
from src.ui.pages.projects_page import ProjectsPage
from src.ui.pages.settings_page import SettingsPage
from src.ui.pages.statistics_page import StatisticsPage
from src.ui.pages.today_page import TodayPage

__all__ = [
    "DashboardPage",
    "TodayPage",
    "ProjectsPage",
    "HabitsPage",
    "CalendarPage",
    "PomodoroPage",
    "NotesPage",
    "StatisticsPage",
    "HistoryPage",
    "ExtrasPage",
    "SettingsPage",
]
