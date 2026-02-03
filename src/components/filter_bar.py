"""Filter bar component for case filtering."""
from typing import Callable

import flet as ft

from models.case import CaseStatus
from models.filters import Filters


# Status options for dropdown
STATUS_OPTIONS = [
    ("all", "全部状态"),
    (CaseStatus.OPENED.value, "已开启"),
    (CaseStatus.PENDING_CUSTOMER_ACTION.value, "等待客户操作"),
    (CaseStatus.RESOLVED.value, "已解决"),
    (CaseStatus.UNASSIGNED.value, "未分配"),
    (CaseStatus.WORK_IN_PROGRESS.value, "处理中"),
]

# Severity options for dropdown
SEVERITY_OPTIONS = [
    ("all", "全部级别"),
    ("low", "低"),
    ("normal", "普通"),
    ("high", "高"),
    ("urgent", "紧急"),
    ("critical", "严重"),
]


class FilterBar(ft.Row):
    """过滤栏组件"""

    def __init__(
        self,
        on_filter_change: Callable[[Filters], None] | None = None,
        initial_filters: Filters | None = None,
    ):
        self._on_filter_change = on_filter_change
        self._filters = initial_filters or Filters()

        # Status dropdown
        self._status_dropdown = ft.Dropdown(
            label="状态",
            width=160,
            options=[ft.DropdownOption(key=k, text=v) for k, v in STATUS_OPTIONS],
            value="all",
            on_select=self._handle_status_change,
        )

        # Severity dropdown
        self._severity_dropdown = ft.Dropdown(
            label="严重级别",
            width=140,
            options=[ft.DropdownOption(key=k, text=v) for k, v in SEVERITY_OPTIONS],
            value="all",
            on_select=self._handle_severity_change,
        )

        # Search input
        self._search_field = ft.TextField(
            label="搜索",
            width=200,
            prefix_icon=ft.Icons.SEARCH,
            on_submit=self._handle_search_submit,
        )

        # Archive toggle
        self._archive_checkbox = ft.Checkbox(
            label="显示已归档",
            value=self._filters.include_archived,
            on_change=self._handle_archive_click,
        )

        # Clear button
        self._clear_button = ft.TextButton(
            content=ft.Text("清除过滤"),
            icon=ft.Icons.CLEAR_ALL,
            on_click=self._handle_clear,
        )

        super().__init__(
            controls=[
                self._status_dropdown,
                self._severity_dropdown,
                self._search_field,
                self._archive_checkbox,
                self._clear_button,
            ],
            spacing=16,
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            wrap=True,
        )

    @property
    def filters(self) -> Filters:
        """Get current filters."""
        return self._filters

    def _notify_change(self):
        """Notify filter change."""
        if self._on_filter_change:
            self._on_filter_change(self._filters)

    def _handle_status_change(self, e):
        """Handle status dropdown change."""
        value = self._status_dropdown.value
        if value == "all":
            self._filters.status = None
        else:
            self._filters.status = [CaseStatus(value)]
        self._notify_change()

    def _handle_severity_change(self, e):
        """Handle severity dropdown change."""
        value = self._severity_dropdown.value
        if value == "all":
            self._filters.severity = None
        else:
            self._filters.severity = [value]
        self._notify_change()

    def _handle_search_submit(self, e):
        """Handle search submit."""
        value = self._search_field.value
        self._filters.search_text = value if value else None
        self._notify_change()

    def _handle_clear(self, e):
        """Handle clear button click."""
        self._filters = Filters()
        self._status_dropdown.value = "all"
        self._severity_dropdown.value = "all"
        self._search_field.value = ""
        self._archive_checkbox.value = False
        self._notify_change()
        if self.page:
            self.page.update()

    def _handle_archive_click(self, e):
        """Handle archive checkbox click."""
        self._filters.include_archived = self._archive_checkbox.value
        self._notify_change()
