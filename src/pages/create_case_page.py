"""Create case page for submitting new support cases."""
from typing import Callable

import flet as ft

from models.case_params import CreateCaseParams
from models.service import Service, SeverityLevel
from services.validation_service import validate_create_case_form


class CreateCasePage(ft.View):
    """创建案例页面"""

    def __init__(
        self,
        services: list[Service] | None = None,
        severity_levels: list[SeverityLevel] | None = None,
        on_back: Callable[[], None] | None = None,
        on_submit: Callable[[CreateCaseParams], None] | None = None,
        on_attachment_add: Callable[[], list[str]] | None = None,
    ):
        self._services = services or []
        self._severity_levels = severity_levels or []
        self._on_back = on_back
        self._on_submit = on_submit
        self._on_attachment_add = on_attachment_add
        self._attachments: list[str] = []
        self._selected_service: Service | None = None

        # Back button
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="返回",
            on_click=self._handle_back,
        )

        # App bar
        appbar = ft.AppBar(
            leading=back_button,
            title=ft.Text("创建新案例", weight=ft.FontWeight.W_500),
            center_title=False,
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE,
        )

        # Service dropdown
        self._service_dropdown = ft.Dropdown(
            label="服务类别 *",
            width=400,
            options=[
                ft.DropdownOption(key=s.code, text=s.name)
                for s in self._services
            ],
            on_select=self._handle_service_change,
        )

        # Category dropdown (populated based on service selection)
        self._category_dropdown = ft.Dropdown(
            label="类别 *",
            width=400,
            options=[],
            disabled=True,
        )

        # Severity dropdown
        self._severity_dropdown = ft.Dropdown(
            label="严重级别 *",
            width=400,
            options=[
                ft.DropdownOption(key=s.code, text=s.name)
                for s in self._severity_levels
            ],
        )

        # Subject field
        self._subject_field = ft.TextField(
            label="主题 *",
            width=400,
            max_length=140,
        )

        # Description field
        self._description_field = ft.TextField(
            label="描述 *",
            width=400,
            multiline=True,
            min_lines=5,
            max_lines=15,
        )

        # CC emails field
        self._cc_field = ft.TextField(
            label="抄送邮箱 (可选，多个用逗号分隔)",
            width=400,
        )

        # Attachment list
        self._attachment_list = ft.Row(
            controls=[],
            wrap=True,
            spacing=8,
        )

        # Attachment button
        attachment_button = ft.TextButton(
            content=ft.Text("添加附件"),
            icon=ft.Icons.ATTACH_FILE,
            on_click=self._handle_attachment_add,
        )

        # Error text
        self._error_text = ft.Text(
            "",
            color=ft.Colors.RED,
            size=14,
            visible=False,
        )

        # Submit button
        submit_button = ft.Button(
            "提交案例",
            icon=ft.Icons.SEND,
            on_click=self._handle_submit,
        )

        # Form content
        form = ft.Column(
            controls=[
                self._service_dropdown,
                self._category_dropdown,
                self._severity_dropdown,
                self._subject_field,
                self._description_field,
                self._cc_field,
                ft.Text("附件", size=14, color=ft.Colors.GREY_700),
                self._attachment_list,
                attachment_button,
                self._error_text,
                ft.Container(height=16),
                submit_button,
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
        )

        content = ft.Container(
            content=form,
            padding=24,
            expand=True,
        )

        super().__init__(
            route="/cases/create",
            appbar=appbar,
            controls=[content],
        )

    @property
    def services(self) -> list[Service]:
        """Get services."""
        return self._services.copy()

    @services.setter
    def services(self, value: list[Service]):
        """Set services and update dropdown."""
        self._services = value
        self._service_dropdown.options = [
            ft.DropdownOption(key=s.code, text=s.name)
            for s in value
        ]
        if self.page:
            self.page.update()

    @property
    def severity_levels(self) -> list[SeverityLevel]:
        """Get severity levels."""
        return self._severity_levels.copy()

    @severity_levels.setter
    def severity_levels(self, value: list[SeverityLevel]):
        """Set severity levels and update dropdown."""
        self._severity_levels = value
        self._severity_dropdown.options = [
            ft.DropdownOption(key=s.code, text=s.name)
            for s in value
        ]
        if self.page:
            self.page.update()

    def _handle_service_change(self, e):
        """Handle service selection change."""
        service_code = self._service_dropdown.value
        self._selected_service = next(
            (s for s in self._services if s.code == service_code),
            None
        )
        
        if self._selected_service:
            self._category_dropdown.options = [
                ft.DropdownOption(key=c.code, text=c.name)
                for c in self._selected_service.categories
            ]
            self._category_dropdown.disabled = False
            self._category_dropdown.value = None
        else:
            self._category_dropdown.options = []
            self._category_dropdown.disabled = True
        
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

    def _handle_back(self, e):
        """Handle back button click."""
        if self._on_back:
            self._on_back()

    def _handle_submit(self, e):
        """Handle submit button click."""
        # Build params
        cc_emails = None
        if self._cc_field.value:
            cc_emails = [
                email.strip()
                for email in self._cc_field.value.split(",")
                if email.strip()
            ]

        params = CreateCaseParams(
            subject=self._subject_field.value or "",
            service_code=self._service_dropdown.value or "",
            category_code=self._category_dropdown.value or "",
            severity_code=self._severity_dropdown.value or "",
            communication_body=self._description_field.value or "",
            cc_email_addresses=cc_emails,
        )

        # Validate
        errors = validate_create_case_form(params)
        if errors:
            error_messages = [f"{e.field}: {e.message}" for e in errors]
            self._error_text.value = "\n".join(error_messages)
            self._error_text.visible = True
            if self.page:
                self.page.update()
            return

        self._error_text.visible = False

        if self._on_submit:
            self._on_submit(params)
