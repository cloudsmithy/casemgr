"""Error handling service for the application."""
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import flet as ft

try:
    from botocore.exceptions import ClientError, BotoCoreError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False
    ClientError = Exception
    BotoCoreError = Exception


class ErrorType(Enum):
    """错误类型"""
    NETWORK = "network"
    AUTH = "auth"
    NOT_FOUND = "not_found"
    THROTTLING = "throttling"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class AppError:
    """应用错误"""
    error_type: ErrorType
    message: str
    retryable: bool = False
    original_error: Exception | None = None


class ErrorHandler:
    """全局错误处理器"""

    def __init__(
        self,
        on_auth_required: Callable[[], None] | None = None,
        on_offline_mode: Callable[[], None] | None = None,
    ):
        self._on_auth_required = on_auth_required
        self._on_offline_mode = on_offline_mode

    def handle_error(
        self,
        error: Exception,
        page: ft.Page | None = None,
    ) -> AppError:
        """
        处理错误并返回应用错误对象。
        
        Args:
            error: 原始异常
            page: Flet 页面对象（用于显示错误）
            
        Returns:
            AppError 对象
        """
        app_error = self._classify_error(error)
        
        if page:
            self._show_error(page, app_error)
        
        # Handle special cases
        if app_error.error_type == ErrorType.AUTH:
            if self._on_auth_required:
                self._on_auth_required()
        elif app_error.error_type == ErrorType.NETWORK:
            if self._on_offline_mode:
                self._on_offline_mode()
        
        return app_error

    def _classify_error(self, error: Exception) -> AppError:
        """Classify error into AppError."""
        # Network errors
        if isinstance(error, (ConnectionError, TimeoutError, OSError)):
            return AppError(
                error_type=ErrorType.NETWORK,
                message="网络连接失败，请检查网络设置",
                retryable=True,
                original_error=error,
            )
        
        # AWS errors
        if HAS_BOTO and isinstance(error, ClientError):
            return self._handle_aws_error(error)
        
        if HAS_BOTO and isinstance(error, BotoCoreError):
            return AppError(
                error_type=ErrorType.NETWORK,
                message="AWS 服务连接失败",
                retryable=True,
                original_error=error,
            )
        
        # Default unknown error
        return AppError(
            error_type=ErrorType.UNKNOWN,
            message=f"发生未知错误: {str(error)}",
            retryable=False,
            original_error=error,
        )

    def _handle_aws_error(self, error: ClientError) -> AppError:
        """Handle AWS ClientError."""
        error_code = error.response.get("Error", {}).get("Code", "")
        error_message = error.response.get("Error", {}).get("Message", str(error))
        
        if error_code == "AccessDeniedException":
            return AppError(
                error_type=ErrorType.AUTH,
                message="访问被拒绝，请检查 AWS 凭证",
                retryable=False,
                original_error=error,
            )
        
        if error_code == "InvalidAccessKeyId":
            return AppError(
                error_type=ErrorType.AUTH,
                message="无效的 Access Key，请重新配置凭证",
                retryable=False,
                original_error=error,
            )
        
        if error_code == "SignatureDoesNotMatch":
            return AppError(
                error_type=ErrorType.AUTH,
                message="凭证签名错误，请检查 Secret Key",
                retryable=False,
                original_error=error,
            )
        
        if error_code == "CaseIdNotFound":
            return AppError(
                error_type=ErrorType.NOT_FOUND,
                message="案例不存在或已被删除",
                retryable=False,
                original_error=error,
            )
        
        if error_code == "ThrottlingException":
            return AppError(
                error_type=ErrorType.THROTTLING,
                message="请求过于频繁，请稍后重试",
                retryable=True,
                original_error=error,
            )
        
        if error_code == "ValidationException":
            return AppError(
                error_type=ErrorType.VALIDATION,
                message=f"验证错误: {error_message}",
                retryable=False,
                original_error=error,
            )
        
        return AppError(
            error_type=ErrorType.UNKNOWN,
            message=f"AWS 错误: {error_message}",
            retryable=False,
            original_error=error,
        )

    def _show_error(self, page: ft.Page, error: AppError) -> None:
        """Show error to user."""
        # Create snack bar with error message
        snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        error.message,
                        color=ft.Colors.WHITE,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.RED_700,
            action="重试" if error.retryable else None,
        )
        
        page.snack_bar = snack_bar
        page.snack_bar.open = True
        page.update()

    def show_success(self, page: ft.Page, message: str) -> None:
        """Show success message."""
        snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        message,
                        color=ft.Colors.WHITE,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.GREEN_700,
        )
        
        page.snack_bar = snack_bar
        page.snack_bar.open = True
        page.update()

    def show_warning(self, page: ft.Page, message: str) -> None:
        """Show warning message."""
        snack_bar = ft.SnackBar(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.WARNING_AMBER,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        message,
                        color=ft.Colors.WHITE,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.Colors.ORANGE_700,
        )
        
        page.snack_bar = snack_bar
        page.snack_bar.open = True
        page.update()
