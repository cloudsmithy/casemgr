"""Pages for AWS Case Manager."""
from .auth_page import AuthPage
from .case_list_page import CaseListPage
from .case_detail_page import CaseDetailPage
from .create_case_page import CreateCasePage
from .archived_cases_page import ArchivedCasesPage
from .settings_page import SettingsPage

__all__ = [
    "AuthPage",
    "CaseListPage",
    "CaseDetailPage",
    "CreateCasePage",
    "ArchivedCasesPage",
    "SettingsPage",
]
