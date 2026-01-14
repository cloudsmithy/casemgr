"""Reply form component for adding case communications."""
from typing import Callable

import flet as ft

from services.validation_service import validate_reply


class ReplyForm(ft.Column):
    """回复表单组件"""

    def __init__(
        self,
        on_submit: Callable[[str, list[str]], None] | None = None,
        on_attachment_add: Callable[[], list[str]] | None = None,
    ):
        self._on_submit = on_submit
        self._on_attachment_add = on_attachment_add
        self._attachments: list[str] = []

        # Reply text field
        self._reply_field = ft.TextField(
            label="回复内容",
            multiline=True,
            min_lines=3,
            max_lines=10,
            expand=True,
        )

        # Error text
        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=12,
            visible=False,
        )

        # Attachment list display
        self._attachment_list = ft.Row(
            controls=[],
            wrap=True,
            spacing=8,
        )

        # Attachment button
        self._attachment_button = ft.TextButton(
            content=ft.Text("添加附件"),
            icon=ft.Icons.ATTACH_FILE,
            on_click=self._handle_attachment_add,
        )

        # Submit button
        self._submit_button = ft.Button(
            "发送回复",
            icon=ft.Icons.SEND,
            on_click=self._handle_submit,
        )

        super().__init__(
            controls=[
                self._reply_field,
                self._error_text,
                self._attachment_list,
                ft.Row(
                    controls=[
                        self._attachment_button,
                        self._submit_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=8,
        )

    @property
    def reply_text(self) -> str:
        """Get reply text."""
        return self._reply_field.value or ""

    @property
    def attachments(self) -> list[str]:
        """Get attachments."""
        return self._attachments.copy()

    def clear(self):
        """Clear the form."""
        self._reply_field.value = ""
        self._attachments.clear()
        self._attachment_list.controls.clear()
        self._error_text.visible = False
        if self.page:
            self.page.update()

    def set_error(self, message: str):
        """Set error message."""
        self._error_text.value = message
        self._error_text.visible = bool(message)
        if self.page:
            self.page.update()

    def _handle_attachment_add(self, e):
        """Handle attachment add button click."""
        if self._on_attachment_add:
            new_attachments = self._on_attachment_add()
            if new_attachments:
                self._attachments.extend(new_attachments)
                self._update_attachment_list()

    def _update_attachment_list(self):
        """Update attachment list display."""
        self._attachment_list.controls.clear()
        for attachment in self._attachments:
            chip = ft.Chip(
                label=ft.Text(attachment.split("/")[-1]),
                delete_icon=ft.Icons.CLOSE,
                on_delete=lambda e, a=attachment: self._remove_attachment(a),
            )
            self._attachment_list.controls.append(chip)
        if self.page:
            self.page.update()

    def _remove_attachment(self, attachment: str):
        """Remove attachment from list."""
        if attachment in self._attachments:
            self._attachments.remove(attachment)
            self._update_attachment_list()

    def _handle_submit(self, e):
        """Handle submit button click."""
        reply_text = self.reply_text
        
        # Validate reply
        if not validate_reply(reply_text):
            self.set_error("回复内容不能为空")
            return
        
        self._error_text.visible = False
        
        if self._on_submit:
            self._on_submit(reply_text, self._attachments)
