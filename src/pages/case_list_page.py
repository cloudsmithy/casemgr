"""Case list page for displaying all cases."""
from typing import Callable

import flet as ft

from models.case import Case
from models.filters import Filters
from components.case_card import CaseCard
from components.filter_bar import FilterBar
from components.badges import OfflineIndicator
from services.filter_engine import FilterEngine
from services.archive_service import ArchiveService


class CaseListPage(ft.View):
    """案例列表页面"""

    def __init__(
        self,
        cases: list[Case] | None = None,
        archive_service: ArchiveService | None = None,
        on_case_select: Callable[[Case], None] | None = None,
        on_create_case: Callable[[], None] | None = None,
        on_refresh: Callable[[], None] | None = None,
        on_view_archived: Callable[[], None] | None = None,
        on_switch_credentials: Callable[[], None] | None = None,
        is_offline: bool = False,
    ):
        self._cases = cases or []
        self._filtered_cases = self._cases.copy()
        self._archive_service = archive_service or ArchiveService()
        self._on_case_select = on_case_select
        self._on_create_case = on_create_case
        self._on_refresh = on_refresh
        self._on_view_archived = on_view_archived
        self._on_switch_credentials = on_switch_credentials
        self._filter_engine = FilterEngine()
        self._filters = Filters()

        # Offline indicator
        self._offline_indicator = OfflineIndicator(is_offline)

        # Filter bar
        self._filter_bar = FilterBar(
            on_filter_change=self._handle_filter_change,
        )

        # Case list
        self._case_list = ft.ListView(
            expand=True,
            spacing=8,
            padding=16,
        )

        # Refresh button
        refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH,
            tooltip="刷新",
            on_click=self._handle_refresh,
        )

        # Settings button (switch credentials)
        settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip="切换凭证",
            on_click=self._handle_switch_credentials,
        )

        # Create case button
        create_button = ft.Button(
            "创建案例",
            icon=ft.Icons.ADD,
            on_click=self._handle_create_case,
        )

        # View archived button
        archived_button = ft.TextButton(
            content=ft.Text("查看已归档"),
            icon=ft.Icons.ARCHIVE,
            on_click=self._handle_view_archived,
        )

        # App bar
        appbar = ft.AppBar(
            title=ft.Text("AWS Case Manager", weight=ft.FontWeight.W_500),
            center_title=False,
            bgcolor=ft.Colors.ORANGE_700,
            color=ft.Colors.WHITE,
            actions=[
                self._offline_indicator,
                refresh_button,
                settings_button,
                archived_button,
                create_button,
            ],
        )

        # Build page content
        content = ft.Column(
            controls=[
                ft.Container(
                    content=self._filter_bar,
                    padding=16,
                ),
                self._case_list,
            ],
            expand=True,
        )

        super().__init__(
            route="/cases",
            appbar=appbar,
            controls=[content],
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
        self._apply_filters()

    @property
    def is_offline(self) -> bool:
        """Get offline status."""
        return self._offline_indicator.is_offline

    @is_offline.setter
    def is_offline(self, value: bool):
        """Set offline status."""
        self._offline_indicator.is_offline = value

    def _apply_filters(self):
        """Apply current filters to cases."""
        # Get archived case IDs
        archived_ids = self._archive_service.get_archived_case_ids()
        
        # Filter by archive status first
        if self._filters.archived_only:
            cases_to_filter = [c for c in self._cases if c.case_id in archived_ids]
        elif self._filters.include_archived:
            cases_to_filter = self._cases
        else:
            cases_to_filter = [c for c in self._cases if c.case_id not in archived_ids]
        
        # Apply other filters
        self._filtered_cases = self._filter_engine.filter_cases(
            cases_to_filter, self._filters
        )
        
        # Apply search if present
        if self._filters.search_text:
            self._filtered_cases = self._filter_engine.search_cases(
                self._filtered_cases, self._filters.search_text
            )
        
        self._update_case_list()

    def _update_case_list(self):
        """Update case list display."""
        self._case_list.controls.clear()
        
        if not self._filtered_cases:
            self._case_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "没有找到案例",
                        size=16,
                        color=ft.Colors.GREY_500,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=32,
                )
            )
        else:
            archived_ids = self._archive_service.get_archived_case_ids()
            for case in self._filtered_cases:
                card = CaseCard(
                    case=case,
                    on_click=self._handle_case_click,
                    on_archive=self._handle_archive,
                    is_archived=case.case_id in archived_ids,
                )
                self._case_list.controls.append(card)

    def _handle_filter_change(self, filters: Filters):
        """Handle filter change."""
        self._filters = filters
        self._apply_filters()
        if self.page:
            self.page.update()

    def _handle_case_click(self, case: Case):
        """Handle case card click."""
        if self._on_case_select:
            self._on_case_select(case)

    def _handle_archive(self, case: Case):
        """Handle archive button click."""
        if self._archive_service.is_archived(case.case_id):
            self._archive_service.unarchive_case(case.case_id)
        else:
            self._archive_service.archive_case(case.case_id)
        self._apply_filters()
        if self.page:
            self.page.update()

    def _handle_refresh(self, e):
        """Handle refresh button click."""
        if self._on_refresh:
            self._on_refresh()

    def _handle_create_case(self, e):
        """Handle create case button click."""
        if self._on_create_case:
            self._on_create_case()

    def _handle_view_archived(self, e):
        """Handle view archived button click."""
        if self._on_view_archived:
            self._on_view_archived()

    def _handle_switch_credentials(self, e):
        """Handle switch credentials button click."""
        if self._on_switch_credentials:
            self._on_switch_credentials()
