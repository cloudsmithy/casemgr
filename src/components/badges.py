"""Badge components for status and severity display."""
import flet as ft

from models.case import CaseStatus


# Status color mapping
STATUS_COLORS = {
    CaseStatus.OPENED: ft.Colors.BLUE,
    CaseStatus.PENDING_CUSTOMER_ACTION: ft.Colors.ORANGE,
    CaseStatus.RESOLVED: ft.Colors.GREEN,
    CaseStatus.UNASSIGNED: ft.Colors.GREY,
    CaseStatus.WORK_IN_PROGRESS: ft.Colors.PURPLE,
}

# Status display names
STATUS_NAMES = {
    CaseStatus.OPENED: "已开启",
    CaseStatus.PENDING_CUSTOMER_ACTION: "等待客户操作",
    CaseStatus.RESOLVED: "已解决",
    CaseStatus.UNASSIGNED: "未分配",
    CaseStatus.WORK_IN_PROGRESS: "处理中",
}

# Severity color mapping
SEVERITY_COLORS = {
    "low": ft.Colors.GREEN,
    "normal": ft.Colors.BLUE,
    "high": ft.Colors.ORANGE,
    "urgent": ft.Colors.RED,
    "critical": ft.Colors.RED_900,
}

# Severity display names
SEVERITY_NAMES = {
    "low": "低",
    "normal": "普通",
    "high": "高",
    "urgent": "紧急",
    "critical": "严重",
}


class StatusBadge(ft.Container):
    """状态徽章组件"""

    def __init__(self, status: CaseStatus):
        self.status = status
        color = STATUS_COLORS.get(status, ft.Colors.GREY)
        name = STATUS_NAMES.get(status, status.value)

        super().__init__(
            content=ft.Text(
                name,
                size=12,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=color,
            padding=ft.Padding(left=8, right=8, top=4, bottom=4),
            border_radius=4,
        )


class SeverityBadge(ft.Container):
    """严重级别徽章组件"""

    def __init__(self, severity_code: str):
        self.severity_code = severity_code
        color = SEVERITY_COLORS.get(severity_code.lower(), ft.Colors.GREY)
        name = SEVERITY_NAMES.get(severity_code.lower(), severity_code)

        super().__init__(
            content=ft.Text(
                name,
                size=12,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_500,
            ),
            bgcolor=color,
            padding=ft.Padding(left=8, right=8, top=4, bottom=4),
            border_radius=4,
        )


class OfflineIndicator(ft.Container):
    """离线状态指示器组件"""

    def __init__(self, is_offline: bool = False):
        self._is_offline = is_offline

        super().__init__(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.CLOUD_OFF if is_offline else ft.Icons.CLOUD_DONE,
                        size=16,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "离线模式" if is_offline else "在线",
                        size=12,
                        color=ft.Colors.WHITE,
                    ),
                ],
                spacing=4,
            ),
            bgcolor=ft.Colors.ORANGE if is_offline else ft.Colors.GREEN,
            padding=ft.Padding(left=8, right=8, top=4, bottom=4),
            border_radius=4,
            visible=True,
        )

    @property
    def is_offline(self) -> bool:
        return self._is_offline

    @is_offline.setter
    def is_offline(self, value: bool):
        self._is_offline = value
        self.bgcolor = ft.Colors.ORANGE if value else ft.Colors.GREEN
        row = self.content
        if isinstance(row, ft.Row) and len(row.controls) >= 2:
            icon = row.controls[0]
            text = row.controls[1]
            if isinstance(icon, ft.Icon):
                icon.name = ft.Icons.CLOUD_OFF if value else ft.Icons.CLOUD_DONE
            if isinstance(text, ft.Text):
                text.value = "离线模式" if value else "在线"
