"""Authentication page for AWS credentials configuration."""
import flet as ft

from models.credentials import AWSCredentials
from services.auth_service import AuthService


class AuthPage(ft.View):
    """认证配置页面"""

    def __init__(self, auth_service: AuthService, on_success: callable = None):
        super().__init__(route="/auth")
        self.auth_service = auth_service
        self._on_success = on_success
        
        # Form fields
        self.access_key_field = ft.TextField(
            label="Access Key ID",
            hint_text="输入 AWS Access Key ID",
            width=400,
        )
        
        self.secret_key_field = ft.TextField(
            label="Secret Access Key",
            hint_text="输入 AWS Secret Access Key",
            password=True,
            can_reveal_password=True,
            width=400,
        )
        
        self.region_dropdown = ft.Dropdown(
            label="Region",
            hint_text="选择 AWS Region",
            width=400,
            value="us-east-1",
            options=[
                ft.DropdownOption("us-east-1", "US East (N. Virginia)"),
                ft.DropdownOption("us-west-2", "US West (Oregon)"),
                ft.DropdownOption("ap-northeast-1", "Asia Pacific (Tokyo)"),
                ft.DropdownOption("ap-southeast-1", "Asia Pacific (Singapore)"),
            ],
        )
        
        # Profile dropdown
        self.profile_dropdown = ft.Dropdown(
            label="AWS Profile",
            hint_text="选择本地 AWS Profile",
            width=400,
        )
        self._load_profiles()
        
        # Status text
        self.status_text = ft.Text(value="", visible=False)
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False, width=20, height=20)
        
        # Build view
        self._build_view()

    def _load_profiles(self):
        profiles = self.auth_service.list_profiles()
        self.profile_dropdown.options = [
            ft.DropdownOption(p, p) for p in profiles
        ]

    def _build_view(self):
        self.appbar = ft.AppBar(
            title=ft.Text("AWS 凭证配置"),
            center_title=True,
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("配置 AWS 凭证", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("方式一：手动输入", size=16, color=ft.Colors.GREY_700),
                        self.access_key_field,
                        self.secret_key_field,
                        self.region_dropdown,
                        ft.TextButton(content=ft.Text("验证并保存"), on_click=self._on_manual_submit),
                        ft.Divider(),
                        ft.Text("方式二：使用 AWS Profile", size=16, color=ft.Colors.GREY_700),
                        self.profile_dropdown,
                        ft.TextButton(content=ft.Text("使用此 Profile"), on_click=self._on_profile_submit),
                        self.loading,
                        self.status_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=40,
                expand=True,
            ),
        ]

    def _show_status(self, message: str, is_error: bool = False):
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED_400 if is_error else ft.Colors.GREEN_400
        self.status_text.visible = True
        if self.page:
            self.page.update()

    def _on_manual_submit(self, e):
        access_key = self.access_key_field.value or ""
        secret_key = self.secret_key_field.value or ""
        
        if not access_key.strip() or not secret_key.strip():
            self._show_status("请输入 Access Key 和 Secret Key", True)
            return
        
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            credentials = AWSCredentials(
                access_key_id=access_key.strip(),
                secret_access_key=secret_key.strip(),
                region=self.region_dropdown.value or "us-east-1",
            )
            
            if self.auth_service.configure(credentials):
                self._show_status("凭证验证成功！")
                if self._on_success:
                    self._on_success()
            else:
                self._show_status("凭证验证失败", True)
        except Exception as ex:
            self._show_status(f"配置失败: {ex}", True)
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()

    def _on_profile_submit(self, e):
        profile = self.profile_dropdown.value
        if not profile:
            self._show_status("请选择一个 Profile", True)
            return
        
        self.loading.visible = True
        if self.page:
            self.page.update()
        
        try:
            if self.auth_service.configure_from_profile(profile):
                self._show_status(f"已使用 Profile: {profile}")
                if self._on_success:
                    self._on_success()
            else:
                self._show_status(f"无法使用 Profile '{profile}'", True)
        except Exception as ex:
            self._show_status(f"配置失败: {ex}", True)
        finally:
            self.loading.visible = False
            if self.page:
                self.page.update()
