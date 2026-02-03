"""Case detail page for displaying case information and communications."""
from typing import Callable

import flet as ft

from models.case import Case, CaseDetail, CaseStatus
from models.communication import AttachmentInfo
from components.badges import StatusBadge, SeverityBadge
from components.communication_item import CommunicationItem
from components.reply_form import ReplyForm
from services.archive_service import ArchiveService


class CaseDetailPage(ft.View):
    """案例详情页面"""

    def __init__(
        self,
        case_detail: CaseDetail | None = None,
        archive_service: ArchiveService | None = None,
        on_back: Callable[[], None] | None = None,
        on_reply: Callable[[str, list[str]], None] | None = None,
        on_resolve: Callable[[str], None] | None = None,
        on_reopen: Callable[[str], None] | None = None,
        on_archive: Callable[[str], None] | None = None,
        on_attachment_download: Callable[[AttachmentInfo], None] | None = None,
        on_attachment_add: Callable[[], list[str]] | None = None,
    ):
        self._case_detail = case_detail
        self._archive_service = archive_service or ArchiveService()
        self._on_back = on_back
        self._on_reply = on_reply
        self._on_resolve = on_resolve
        self._on_reopen = on_reopen
        self._on_archive = on_archive
        self._on_attachment_download = on_attachment_download
        self._on_attachment_add = on_attachment_add

        # Back button
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="返回",
            on_click=self._handle_back,
        )

        # App bar actions
        actions = []
        if case_detail:
            is_archived = self._archive_service.is_archived(case_detail.case_id)
            
            # Archive/Unarchive button
            archive_button = ft.IconButton(
                icon=ft.Icons.UNARCHIVE if is_archived else ft.Icons.ARCHIVE,
                tooltip="取消归档" if is_archived else "归档",
                on_click=self._handle_archive,
            )
            actions.append(archive_button)
            
            # Resolve/Reopen button
            if case_detail.status == CaseStatus.RESOLVED:
                reopen_button = ft.Button(
                    "重新打开",
                    icon=ft.Icons.REFRESH,
                    on_click=self._handle_reopen,
                )
                actions.append(reopen_button)
            else:
                resolve_button = ft.Button(
                    "关闭案例",
                    icon=ft.Icons.CHECK,
                    on_click=self._handle_resolve,
                )
                actions.append(resolve_button)

        # App bar
        appbar = ft.AppBar(
            leading=back_button,
            title=ft.Text(
                case_detail.subject if case_detail else "案例详情",
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
                weight=ft.FontWeight.W_500,
            ),
            center_title=False,
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE,
            actions=actions,
        )

        # Build content
        if case_detail:
            content = self._build_content(case_detail)
        else:
            content = ft.Container(
                content=ft.Text("加载中..."),
                alignment=ft.Alignment(0, 0),
                expand=True,
            )

        super().__init__(
            route=f"/cases/{case_detail.case_id}" if case_detail else "/cases/detail",
            appbar=appbar,
            controls=[content],
        )

    @property
    def case_detail(self) -> CaseDetail | None:
        """Get case detail."""
        return self._case_detail

    @case_detail.setter
    def case_detail(self, value: CaseDetail | None):
        """Set case detail and refresh."""
        self._case_detail = value
        if value:
            self.controls = [self._build_content(value)]
        if self.page:
            self.page.update()

    def _build_content(self, case_detail: CaseDetail) -> ft.Control:
        """Build page content."""
        # Case info section
        info_section = ft.Container(
            content=ft.Column(
                controls=[
                    # Title and badges
                    ft.Text(
                        case_detail.subject,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        controls=[
                            StatusBadge(case_detail.status),
                            SeverityBadge(case_detail.severity_code),
                            ft.Text(
                                f"ID: {case_detail.display_id}",
                                size=12,
                                color=ft.Colors.GREY_600,
                            ),
                        ],
                        spacing=8,
                    ),
                    # Service info
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"服务: {case_detail.service_code}",
                                size=14,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                f"类别: {case_detail.category_code}",
                                size=14,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        spacing=16,
                    ),
                    # Submitted info
                    ft.Text(
                        f"提交者: {case_detail.submitted_by}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Text(
                        f"创建时间: {case_detail.time_created.strftime('%Y-%m-%d %H:%M')}",
                        size=12,
                        color=ft.Colors.GREY_600,
                    ),
                ],
                spacing=8,
            ),
            padding=16,
            bgcolor=ft.Colors.GREY_100,
            border_radius=8,
        )

        # Communications section
        communications_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding(left=0, right=0, top=8, bottom=8),
        )
        
        # Sort communications by time (oldest first)
        sorted_communications = sorted(
            case_detail.communications,
            key=lambda c: c.time_created,
        )
        
        for comm in sorted_communications:
            item = CommunicationItem(
                communication=comm,
                on_attachment_click=self._handle_attachment_download,
            )
            communications_list.controls.append(item)

        # Reply form (only if case is not resolved)
        reply_section = None
        if case_detail.status != CaseStatus.RESOLVED:
            reply_section = ft.Container(
                content=ReplyForm(
                    on_submit=self._handle_reply,
                    on_attachment_add=self._on_attachment_add,
                ),
                padding=16,
                bgcolor=ft.Colors.GREY_50,
                border_radius=8,
            )

        # Build main content
        controls = [
            info_section,
            ft.Divider(),
            ft.Text("通信记录", size=16, weight=ft.FontWeight.W_500),
            communications_list,
        ]
        
        if reply_section:
            controls.append(ft.Divider())
            controls.append(reply_section)

        return ft.Column(
            controls=controls,
            expand=True,
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

    def _handle_back(self, e):
        """Handle back button click."""
        if self._on_back:
            self._on_back()

    def _handle_reply(self, body: str, attachments: list[str]):
        """Handle reply submission."""
        if self._on_reply and self._case_detail:
            self._on_reply(body, attachments)

    def _handle_resolve(self, e):
        """Handle resolve button click."""
        if self._on_resolve and self._case_detail:
            self._on_resolve(self._case_detail.case_id)

    def _handle_reopen(self, e):
        """Handle reopen button click."""
        if self._on_reopen and self._case_detail:
            self._on_reopen(self._case_detail.case_id)

    def _handle_archive(self, e):
        """Handle archive button click."""
        if self._on_archive and self._case_detail:
            self._on_archive(self._case_detail.case_id)

    def _handle_attachment_download(self, attachment: AttachmentInfo):
        """Handle attachment download."""
        if self._on_attachment_download:
            self._on_attachment_download(attachment)
