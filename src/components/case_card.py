"""Case card component for displaying case summary."""
from datetime import datetime, timezone
from typing import Callable

import flet as ft

from models.case import Case
from components.badges import StatusBadge, SeverityBadge


def format_time(dt: datetime) -> str:
    """Format datetime for display."""
    # 确保使用 UTC 时区进行比较
    now = datetime.now(timezone.utc)
    # 如果 dt 是 naive 的，假设它是 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "刚刚"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60} 分钟前"
        else:
            return f"{diff.seconds // 3600} 小时前"
    elif diff.days == 1:
        return "昨天"
    elif diff.days < 7:
        return f"{diff.days} 天前"
    else:
        return dt.strftime("%Y-%m-%d")


class CaseCard(ft.Card):
    """案例卡片组件"""

    def __init__(
        self,
        case: Case,
        on_click: Callable[[Case], None] | None = None,
        on_archive: Callable[[Case], None] | None = None,
        is_archived: bool = False,
    ):
        self.case = case
        self._on_click = on_click
        self._on_archive = on_archive
        self._is_archived = is_archived

        # Archive button
        archive_button = ft.IconButton(
            icon=ft.Icons.UNARCHIVE if is_archived else ft.Icons.ARCHIVE,
            tooltip="取消归档" if is_archived else "归档",
            on_click=self._handle_archive,
        )

        # Card content
        content = ft.Container(
            content=ft.Column(
                controls=[
                    # Title row
                    ft.Row(
                        controls=[
                            ft.Text(
                                case.subject,
                                size=16,
                                weight=ft.FontWeight.W_500,
                                expand=True,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            archive_button,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Badges row
                    ft.Row(
                        controls=[
                            StatusBadge(case.status),
                            SeverityBadge(case.severity_code),
                        ],
                        spacing=8,
                    ),
                    # Info row
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"ID: {case.display_id}",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                            ft.Text(
                                format_time(case.time_created),
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            on_click=self._handle_click,
        )

        super().__init__(
            content=content,
            elevation=2,
        )

    def _handle_click(self, e):
        """Handle card click."""
        if self._on_click:
            self._on_click(self.case)

    def _handle_archive(self, e):
        """Handle archive button click."""
        if self._on_archive:
            self._on_archive(self.case)
