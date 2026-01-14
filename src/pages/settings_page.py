"""Settings page for application configuration."""
from typing import Callable

import flet as ft


class SettingsPage(ft.View):
    """设置页面"""

    def __init__(
        self,
        notification_enabled: bool = True,
        polling_interval: int = 300,
        on_back: Callable[[], None] | None = None,
        on_notification_change: Callable[[bool], None] | None = None,
        on_polling_interval_change: Callable[[int], None] | None = None,
        on_clear_cache: Callable[[], None] | None = None,
        on_manage_credentials: Callable[[], None] | None = None,
    ):
        self._notification_enabled = notification_enabled
        self._polling_interval = polling_interval
        self._on_back = on_back
        self._on_notification_change = on_notification_change
        self._on_polling_interval_change = on_polling_interval_change
        self._on_clear_cache = on_clear_cache
        self._on_manage_credentials = on_manage_credentials

        # Back button
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="返回",
            on_click=self._handle_back,
        )

        # App bar
        appbar = ft.AppBar(
            leading=back_button,
            title=ft.Text("设置"),
            center_title=False,
        )

        # Notification settings section
        notification_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "通知设置",
                        size=18,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("启用桌面通知", expand=True),
                            ft.Switch(
                                value=notification_enabled,
                            ),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("轮询间隔 (秒)", expand=True),
                            ft.Dropdown(
                                width=120,
                                value=str(polling_interval),
                                options=[
                                    ft.DropdownOption("60", "1 分钟"),
                                    ft.DropdownOption("180", "3 分钟"),
                                    ft.DropdownOption("300", "5 分钟"),
                                    ft.DropdownOption("600", "10 分钟"),
                                    ft.DropdownOption("900", "15 分钟"),
                                ],
                                on_select=self._handle_polling_change,
                            ),
                        ],
                    ),
                ],
                spacing=16,
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )

        # Cache settings section
        cache_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "缓存设置",
                        size=18,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("清除本地缓存数据", expand=True),
                            ft.TextButton(
                                content=ft.Text("清除缓存"),
                                icon=ft.Icons.DELETE_OUTLINE,
                                on_click=self._handle_clear_cache,
                            ),
                        ],
                    ),
                ],
                spacing=16,
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )

        # Credentials section
        credentials_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "凭证管理",
                        size=18,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("管理 AWS 凭证配置", expand=True),
                            ft.TextButton(
                                content=ft.Text("管理凭证"),
                                icon=ft.Icons.KEY,
                                on_click=self._handle_manage_credentials,
                            ),
                        ],
                    ),
                ],
                spacing=16,
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )

        # Content
        content = ft.Column(
            controls=[
                notification_section,
                cache_section,
                credentials_section,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

        container = ft.Container(
            content=content,
            padding=24,
            expand=True,
        )

        super().__init__(
            route="/settings",
            appbar=appbar,
            controls=[container],
        )

    def _handle_back(self, e):
        """Handle back button click."""
        if self._on_back:
            self._on_back()

    def _handle_notification_change(self, e):
        """Handle notification switch change."""
        self._notification_enabled = e.control.value
        if self._on_notification_change:
            self._on_notification_change(e.control.value)

    def _handle_polling_change(self, e):
        """Handle polling interval change."""
        self._polling_interval = int(e.control.value)
        if self._on_polling_interval_change:
            self._on_polling_interval_change(int(e.control.value))

    def _handle_clear_cache(self, e):
        """Handle clear cache button click."""
        if self._on_clear_cache:
            self._on_clear_cache()
            # Show confirmation
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("缓存已清除"),
                )
                self.page.snack_bar.open = True
                self.page.update()

    def _handle_manage_credentials(self, e):
        """Handle manage credentials button click."""
        if self._on_manage_credentials:
            self._on_manage_credentials()
