"""Notification service for desktop notifications and polling."""
import asyncio
import threading
from datetime import datetime
from typing import Callable

try:
    from plyer import notification as plyer_notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False


class NotificationService:
    """通知服务"""

    def __init__(
        self,
        on_case_update: Callable[[str], None] | None = None,
    ):
        self._enabled = True
        self._polling_interval = 300  # 5 minutes default
        self._polling_task: asyncio.Task | None = None
        self._stop_event = threading.Event()
        self._on_case_update = on_case_update
        self._last_check_time: datetime | None = None
        self._check_callback: Callable[[], list[str]] | None = None

    @property
    def enabled(self) -> bool:
        """Get notification enabled status."""
        return self._enabled

    @property
    def polling_interval(self) -> int:
        """Get polling interval in seconds."""
        return self._polling_interval

    def set_enabled(self, enabled: bool) -> None:
        """
        设置通知开关。
        
        Args:
            enabled: 是否启用通知
        """
        self._enabled = enabled
        if not enabled:
            self.stop_polling()

    def set_polling_interval(self, interval_seconds: int) -> None:
        """
        设置轮询间隔。
        
        Args:
            interval_seconds: 轮询间隔（秒）
        """
        self._polling_interval = max(60, interval_seconds)  # Minimum 1 minute

    def set_check_callback(self, callback: Callable[[], list[str]]) -> None:
        """
        设置检查更新的回调函数。
        
        回调函数应返回有更新的案例 ID 列表。
        
        Args:
            callback: 检查更新的回调函数
        """
        self._check_callback = callback

    def show_notification(
        self,
        title: str,
        body: str,
        case_id: str | None = None,
    ) -> None:
        """
        显示桌面通知。
        
        Args:
            title: 通知标题
            body: 通知内容
            case_id: 关联的案例 ID（可选）
        """
        if not self._enabled:
            return

        if HAS_PLYER:
            try:
                plyer_notification.notify(
                    title=title,
                    message=body,
                    app_name="AWS Case Manager",
                    timeout=10,
                )
            except Exception:
                # Silently fail if notification fails
                pass

    def start_polling(self, interval_seconds: int | None = None) -> None:
        """
        开始轮询检查更新。
        
        Args:
            interval_seconds: 轮询间隔（秒），如果不指定则使用当前设置
        """
        if interval_seconds is not None:
            self._polling_interval = max(60, interval_seconds)

        self._stop_event.clear()
        
        # Start polling in a background thread
        thread = threading.Thread(target=self._polling_loop, daemon=True)
        thread.start()

    def stop_polling(self) -> None:
        """停止轮询。"""
        self._stop_event.set()

    def _polling_loop(self) -> None:
        """Polling loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                self._check_for_updates()
            except Exception:
                # Silently fail and continue polling
                pass
            
            # Wait for interval or stop event
            self._stop_event.wait(self._polling_interval)

    def _check_for_updates(self) -> None:
        """Check for case updates."""
        if not self._enabled or not self._check_callback:
            return

        self._last_check_time = datetime.now()
        
        try:
            updated_case_ids = self._check_callback()
            
            for case_id in updated_case_ids:
                self.show_notification(
                    title="案例更新",
                    body=f"案例 {case_id} 有新的更新",
                    case_id=case_id,
                )
                
                if self._on_case_update:
                    self._on_case_update(case_id)
        except Exception:
            # Silently fail
            pass

    def get_last_check_time(self) -> datetime | None:
        """
        获取最后检查时间。
        
        Returns:
            最后检查时间，如果从未检查过则返回 None
        """
        return self._last_check_time
