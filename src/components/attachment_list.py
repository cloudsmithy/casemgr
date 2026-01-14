"""Attachment list component for displaying and downloading attachments."""
from typing import Callable

import flet as ft

from models.communication import AttachmentInfo


class AttachmentList(ft.Column):
    """附件列表组件"""

    def __init__(
        self,
        attachments: list[AttachmentInfo],
        on_download: Callable[[AttachmentInfo], None] | None = None,
    ):
        self._attachments = attachments
        self._on_download = on_download

        # Build attachment items
        items = []
        for attachment in attachments:
            item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            self._get_file_icon(attachment.file_name),
                            size=20,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Text(
                            attachment.file_name,
                            size=14,
                            expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD,
                            tooltip="下载",
                            on_click=lambda e, a=attachment: self._handle_download(a),
                        ),
                    ],
                    spacing=8,
                ),
                padding=8,
                border_radius=4,
                bgcolor=ft.Colors.GREY_100,
            )
            items.append(item)

        super().__init__(
            controls=items,
            spacing=4,
        )

    @property
    def attachments(self) -> list[AttachmentInfo]:
        """Get attachments."""
        return self._attachments.copy()

    def _get_file_icon(self, filename: str) -> str:
        """Get icon based on file extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        
        icon_map = {
            "pdf": ft.Icons.PICTURE_AS_PDF,
            "doc": ft.Icons.DESCRIPTION,
            "docx": ft.Icons.DESCRIPTION,
            "xls": ft.Icons.TABLE_CHART,
            "xlsx": ft.Icons.TABLE_CHART,
            "png": ft.Icons.IMAGE,
            "jpg": ft.Icons.IMAGE,
            "jpeg": ft.Icons.IMAGE,
            "gif": ft.Icons.IMAGE,
            "zip": ft.Icons.FOLDER_ZIP,
            "rar": ft.Icons.FOLDER_ZIP,
            "txt": ft.Icons.TEXT_SNIPPET,
            "log": ft.Icons.TEXT_SNIPPET,
        }
        
        return icon_map.get(ext, ft.Icons.ATTACH_FILE)

    def _handle_download(self, attachment: AttachmentInfo):
        """Handle download button click."""
        if self._on_download:
            self._on_download(attachment)
