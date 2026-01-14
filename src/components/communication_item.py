"""Communication item component for displaying messages."""
from datetime import datetime
from typing import Callable

import flet as ft

from models.communication import Communication, AttachmentInfo


def format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M")


def is_aws_reply(submitted_by: str) -> bool:
    """Check if the message is from AWS support."""
    return "amazon" in submitted_by.lower() or "aws" in submitted_by.lower()


class CommunicationItem(ft.Container):
    """通信记录项组件"""

    def __init__(
        self,
        communication: Communication,
        on_attachment_click: Callable[[AttachmentInfo], None] | None = None,
    ):
        self.communication = communication
        self._on_attachment_click = on_attachment_click
        
        is_aws = is_aws_reply(communication.submitted_by)
        
        # Message header
        header = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.SUPPORT_AGENT if is_aws else ft.Icons.PERSON,
                    size=20,
                    color=ft.Colors.BLUE if is_aws else ft.Colors.GREY_700,
                ),
                ft.Text(
                    communication.submitted_by,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.BLUE if is_aws else ft.Colors.GREY_700,
                ),
                ft.Text(
                    format_datetime(communication.time_created),
                    size=12,
                    color=ft.Colors.GREY_500,
                ),
            ],
            spacing=8,
        )
        
        # Message body
        body = ft.Text(
            communication.body,
            size=14,
            selectable=True,
        )
        
        # Attachments list
        attachments_controls = []
        if communication.attachments:
            for attachment in communication.attachments:
                attachments_controls.append(
                    ft.TextButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ATTACH_FILE, size=16),
                                ft.Text(attachment.file_name, size=12),
                            ],
                            spacing=4,
                        ),
                        on_click=lambda e, a=attachment: self._handle_attachment_click(a),
                    )
                )
        
        # Build content
        content_controls = [header, body]
        if attachments_controls:
            content_controls.append(
                ft.Row(
                    controls=attachments_controls,
                    wrap=True,
                    spacing=8,
                )
            )
        
        super().__init__(
            content=ft.Column(
                controls=content_controls,
                spacing=8,
            ),
            padding=16,
            border_radius=8,
            bgcolor=ft.Colors.BLUE_50 if is_aws else ft.Colors.GREY_100,
            margin=ft.Margin(
                left=0 if is_aws else 40,
                right=40 if is_aws else 0,
                top=0,
                bottom=8,
            ),
        )

    def _handle_attachment_click(self, attachment: AttachmentInfo):
        """Handle attachment click."""
        if self._on_attachment_click:
            self._on_attachment_click(attachment)
