"""Archived cases page for viewing and managing archived cases."""
from typing import Callable

import flet as ft

from models.case import Case
from components.case_card import CaseCard
from services.archive_service import ArchiveService


class ArchivedCasesPage(ft.View):
    """已归档案例页面"""

    def __init__(
        self,
        cases: list[Case] | None = None,
        archive_service: ArchiveService | None = None,
        on_back: Callable[[], None] | None = None,
        on_case_select: Callable[[Case], None] | None = None,
    ):
        self._cases = cases or []
        self._archive_service = archive_service or ArchiveService()
        self._on_back = on_back
        self._on_case_select = on_case_select

        # Back button
        back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="返回",
            on_click=self._handle_back,
        )

        # App bar
        appbar = ft.AppBar(
            leading=back_button,
            title=ft.Text("已归档案例"),
            center_title=False,
        )

        # Case list
        self._case_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=16,
        )

        super().__init__(
            route="/cases/archived",
            appbar=appbar,
            controls=[self._case_list],
        )

        # Initial render
        self._update_case_list()

    @property
    def cases(self) -> list[Case]:
        """Get all cases."""
        return self._cases.copy()

    @cases.setter
    def cases(self, value: list[Case]):
        """Set cases and refresh list."""
        self._cases = value
        self._update_case_list()

    def _get_archived_cases(self) -> list[Case]:
        """Get only archived cases."""
        archived_ids = self._archive_service.get_archived_case_ids()
        return [c for c in self._cases if c.case_id in archived_ids]

    def _update_case_list(self):
        """Update case list display."""
        self._case_list.controls.clear()
        
        archived_cases = self._get_archived_cases()
        
        if not archived_cases:
            self._case_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "没有已归档的案例",
                        size=16,
                        color=ft.Colors.GREY_500,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=32,
                )
            )
        else:
            for case in archived_cases:
                card = CaseCard(
                    case=case,
                    on_click=self._handle_case_click,
                    on_archive=self._handle_unarchive,
                    is_archived=True,
                )
                self._case_list.controls.append(card)

    def _handle_back(self, e):
        """Handle back button click."""
        if self._on_back:
            self._on_back()

    def _handle_case_click(self, case: Case):
        """Handle case card click."""
        if self._on_case_select:
            self._on_case_select(case)

    def _handle_unarchive(self, case: Case):
        """Handle unarchive button click."""
        self._archive_service.unarchive_case(case.case_id)
        self._update_case_list()
        if self.page:
            self.page.update()
