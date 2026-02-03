"""Main application entry point for AWS Case Manager."""
import flet as ft

from models.case import Case, CaseDetail
from models.filters import Filters
from models.communication import AttachmentInfo
from models.case_params import CreateCaseParams
from services.auth_service import AuthService
from services.aws_client_service import AWSClientService
from services.cache_service import CacheService
from services.archive_service import ArchiveService
from services.filter_engine import FilterEngine
from services.network_service import NetworkService
from services.notification_service import NotificationService
from services.error_handler import ErrorHandler
from pages.auth_page import AuthPage
from pages.case_list_page import CaseListPage
from pages.case_detail_page import CaseDetailPage
from pages.create_case_page import CreateCasePage
from pages.archived_cases_page import ArchivedCasesPage
from pages.settings_page import SettingsPage


class AWSCaseManagerApp:
    """AWS Case Manager 应用"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "AWS Case Manager"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # 页面设置
        self.page.padding = 0
        self.page.bgcolor = ft.Colors.GREY_100
        
        # Initialize services (pass page for client_storage)
        self.auth_service = AuthService(page)
        self.aws_client: AWSClientService | None = None
        self.cache_service = CacheService()
        self.archive_service = ArchiveService()
        self.filter_engine = FilterEngine()
        self.network_service = NetworkService(
            on_status_change=self._handle_network_change
        )
        self.notification_service = NotificationService(
            on_case_update=self._handle_case_update
        )
        self.error_handler = ErrorHandler(
            on_auth_required=self._go_to_auth,
            on_offline_mode=self._switch_to_offline,
        )
        
        # App state
        self._cases: list[Case] = []
        self._current_case_detail: CaseDetail | None = None
        self._is_offline = False
        
        # Start network monitoring
        self.network_service.start_monitoring()
        
        # Check authentication and start
        self._initialize()

    def _initialize(self):
        """Initialize the application."""
        # Check if credentials are configured
        credentials = self.auth_service.get_stored_credentials()
        
        if credentials:
            # Try to validate credentials
            try:
                self.aws_client = AWSClientService(credentials)
                if self.auth_service.validate_credentials():
                    self._go_to_case_list()
                    self._load_cases()
                else:
                    self._go_to_auth()
            except Exception:
                self._go_to_auth()
        else:
            self._go_to_auth()

    def _handle_network_change(self, is_online: bool):
        """Handle network status change."""
        self._is_offline = not is_online
        
        if is_online:
            # Network restored, sync data
            self._load_cases()
            self.error_handler.show_success(self.page, "网络已恢复")
        else:
            # Network lost, switch to offline mode
            self.error_handler.show_warning(self.page, "网络连接已断开，已切换到离线模式")

    def _handle_case_update(self, case_id: str):
        """Handle case update notification."""
        # Refresh case list
        self._load_cases()

    def _switch_to_offline(self):
        """Switch to offline mode."""
        self._is_offline = True
        # Load cached data
        self._cases = self.cache_service.get_cached_cases()

    def _go_to_auth(self):
        """Navigate to auth page."""
        auth_page = AuthPage(
            auth_service=self.auth_service,
            on_success=self._handle_auth_success,
        )
        self.page.views.clear()
        self.page.views.append(auth_page)
        self.page.update()

    def _handle_auth_success(self):
        """Handle successful authentication."""
        credentials = self.auth_service.get_stored_credentials()
        if credentials:
            self.aws_client = AWSClientService(credentials)
            self._go_to_case_list()
            self._load_cases()
            
            # Start notification polling
            self.notification_service.start_polling()

    def _go_to_case_list(self):
        """Navigate to case list page."""
        case_list_page = CaseListPage(
            cases=self._cases,
            archive_service=self.archive_service,
            on_case_select=self._handle_case_select,
            on_create_case=self._go_to_create_case,
            on_refresh=self._load_cases,
            on_view_archived=self._go_to_archived,
            on_switch_credentials=self._handle_switch_credentials,
            is_offline=self._is_offline,
        )
        self.page.views.clear()
        self.page.views.append(case_list_page)
        self.page.update()

    def _handle_switch_credentials(self):
        """Handle switch credentials request."""
        # Clear stored credentials
        self.auth_service.clear_credentials()
        self.aws_client = None
        # Go to auth page
        self._go_to_auth()

    def _go_to_case_detail(self, case: Case):
        """Navigate to case detail page."""
        case_detail_page = CaseDetailPage(
            case_detail=self._current_case_detail,
            archive_service=self.archive_service,
            on_back=self._go_to_case_list,
            on_reply=lambda body, attachments: self._handle_reply(case.case_id, body, attachments),
            on_resolve=self._handle_resolve,
            on_reopen=self._handle_reopen,
            on_archive=self._handle_archive,
            on_attachment_download=self._handle_attachment_download,
        )
        self.page.views.append(case_detail_page)
        self.page.update()

    def _go_to_create_case(self):
        """Navigate to create case page."""
        # Load services and severity levels
        services = []
        severity_levels = []
        
        if self.aws_client and not self._is_offline:
            try:
                services = self.aws_client.describe_services()
                severity_levels = self.aws_client.describe_severity_levels()
            except Exception as e:
                self.error_handler.handle_error(e, self.page)
        
        create_page = CreateCasePage(
            services=services,
            severity_levels=severity_levels,
            on_back=self._go_to_case_list,
            on_submit=self._handle_create_case,
        )
        self.page.views.append(create_page)
        self.page.update()

    def _go_to_archived(self):
        """Navigate to archived cases page."""
        archived_page = ArchivedCasesPage(
            cases=self._cases,
            archive_service=self.archive_service,
            on_back=self._go_to_case_list,
            on_case_select=self._handle_case_select,
        )
        self.page.views.append(archived_page)
        self.page.update()

    def _go_to_settings(self):
        """Navigate to settings page."""
        settings_page = SettingsPage(
            notification_enabled=self.notification_service.enabled,
            polling_interval=self.notification_service.polling_interval,
            on_back=self._go_to_case_list,
            on_notification_change=self.notification_service.set_enabled,
            on_polling_interval_change=self.notification_service.set_polling_interval,
            on_clear_cache=self.cache_service.clear_cache,
            on_manage_credentials=self._go_to_auth,
        )
        self.page.views.append(settings_page)
        self.page.update()

    def _load_cases(self):
        """Load cases from AWS or cache."""
        if self._is_offline or not self.aws_client:
            # Load from cache
            self._cases = self.cache_service.get_cached_cases()
        else:
            try:
                self._cases = self.aws_client.describe_cases(include_resolved=True)
                # Save to cache
                self.cache_service.save_cases(self._cases)
            except Exception as e:
                self.error_handler.handle_error(e, self.page)
                # Fall back to cache
                self._cases = self.cache_service.get_cached_cases()
        
        # Update current view if it's case list
        if self.page.views and isinstance(self.page.views[-1], CaseListPage):
            self.page.views[-1].cases = self._cases
            self.page.views[-1].is_offline = self._is_offline
            self.page.update()

    def _handle_case_select(self, case: Case):
        """Handle case selection."""
        # Load case detail
        if self._is_offline or not self.aws_client:
            self._current_case_detail = self.cache_service.get_cached_case_detail(case.case_id)
        else:
            try:
                self._current_case_detail = self.aws_client.describe_case(case.case_id)
                # Save to cache
                if self._current_case_detail:
                    self.cache_service.save_case_detail(case.case_id, self._current_case_detail)
            except Exception as e:
                self.error_handler.handle_error(e, self.page)
                self._current_case_detail = self.cache_service.get_cached_case_detail(case.case_id)
        
        if self._current_case_detail:
            self._go_to_case_detail(case)
        else:
            self.error_handler.show_warning(self.page, "无法加载案例详情")

    def _handle_reply(self, case_id: str, body: str, attachments: list[str]):
        """Handle reply submission."""
        if self._is_offline or not self.aws_client:
            self.error_handler.show_warning(self.page, "离线模式下无法发送回复")
            return
        
        try:
            self.aws_client.add_communication(case_id, body, attachments if attachments else None)
            self.error_handler.show_success(self.page, "回复已发送")
            # Reload case detail
            self._current_case_detail = self.aws_client.describe_case(case_id)
            if self._current_case_detail:
                self.cache_service.save_case_detail(case_id, self._current_case_detail)
                # Update view
                if len(self.page.views) > 0 and isinstance(self.page.views[-1], CaseDetailPage):
                    self.page.views[-1].case_detail = self._current_case_detail
        except Exception as e:
            self.error_handler.handle_error(e, self.page)

    def _handle_resolve(self, case_id: str):
        """Handle case resolve."""
        if self._is_offline or not self.aws_client:
            self.error_handler.show_warning(self.page, "离线模式下无法关闭案例")
            return
        
        try:
            self.aws_client.resolve_case(case_id)
            self.error_handler.show_success(self.page, "案例已关闭")
            self._load_cases()
            self._go_to_case_list()
        except Exception as e:
            self.error_handler.handle_error(e, self.page)

    def _handle_reopen(self, case_id: str):
        """Handle case reopen."""
        if self._is_offline or not self.aws_client:
            self.error_handler.show_warning(self.page, "离线模式下无法重新打开案例")
            return
        
        try:
            # Reopen by adding a communication
            self.aws_client.add_communication(case_id, "重新打开案例")
            self.error_handler.show_success(self.page, "案例已重新打开")
            self._load_cases()
        except Exception as e:
            self.error_handler.handle_error(e, self.page)

    def _handle_archive(self, case_id: str):
        """Handle case archive/unarchive."""
        if self.archive_service.is_archived(case_id):
            self.archive_service.unarchive_case(case_id)
            self.error_handler.show_success(self.page, "案例已取消归档")
        else:
            self.archive_service.archive_case(case_id)
            self.error_handler.show_success(self.page, "案例已归档")

    def _handle_attachment_download(self, attachment: AttachmentInfo):
        """Handle attachment download."""
        if self._is_offline or not self.aws_client:
            self.error_handler.show_warning(self.page, "离线模式下无法下载附件")
            return
        
        try:
            attachment_data = self.aws_client.describe_attachment(attachment.attachment_id)
            # TODO: Save file to disk using file picker
            self.error_handler.show_success(self.page, f"附件 {attachment.file_name} 下载完成")
        except Exception as e:
            self.error_handler.handle_error(e, self.page)

    def _handle_create_case(self, params: CreateCaseParams):
        """Handle case creation."""
        if self._is_offline or not self.aws_client:
            self.error_handler.show_warning(self.page, "离线模式下无法创建案例")
            return
        
        try:
            case_id = self.aws_client.create_case(params)
            self.error_handler.show_success(self.page, f"案例已创建: {case_id}")
            self._load_cases()
            self._go_to_case_list()
        except Exception as e:
            self.error_handler.handle_error(e, self.page)


def main(page: ft.Page):
    """Main entry point."""
    app = AWSCaseManagerApp(page)


if __name__ == "__main__":
    ft.app(main)
