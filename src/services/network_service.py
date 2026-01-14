"""Network service for connectivity detection and offline mode."""
import socket
import threading
from typing import Callable


class NetworkService:
    """网络服务 - 检测网络连接状态"""

    def __init__(
        self,
        on_status_change: Callable[[bool], None] | None = None,
        check_interval: int = 30,
    ):
        self._is_online = True
        self._on_status_change = on_status_change
        self._check_interval = check_interval
        self._stop_event = threading.Event()
        self._monitoring_thread: threading.Thread | None = None

    @property
    def is_online(self) -> bool:
        """Get current online status."""
        return self._is_online

    def check_connectivity(self) -> bool:
        """
        检测网络连接状态。
        
        尝试连接到 AWS 服务端点来验证网络可用性。
        
        Returns:
            True 如果网络可用，False 如果网络不可用
        """
        hosts_to_check = [
            ("support.us-east-1.amazonaws.com", 443),
            ("aws.amazon.com", 443),
            ("8.8.8.8", 53),  # Google DNS as fallback
        ]
        
        for host, port in hosts_to_check:
            try:
                socket.create_connection((host, port), timeout=5)
                return True
            except (socket.timeout, socket.error, OSError):
                continue
        
        return False

    def update_status(self) -> bool:
        """
        更新网络状态并触发回调。
        
        Returns:
            当前网络状态
        """
        was_online = self._is_online
        self._is_online = self.check_connectivity()
        
        # Notify if status changed
        if was_online != self._is_online and self._on_status_change:
            self._on_status_change(self._is_online)
        
        return self._is_online

    def start_monitoring(self) -> None:
        """开始监控网络状态。"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            return
        
        self._stop_event.clear()
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
        )
        self._monitoring_thread.start()

    def stop_monitoring(self) -> None:
        """停止监控网络状态。"""
        self._stop_event.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
            self._monitoring_thread = None

    def _monitoring_loop(self) -> None:
        """Monitoring loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                self.update_status()
            except Exception:
                # Silently fail and continue monitoring
                pass
            
            # Wait for interval or stop event
            self._stop_event.wait(self._check_interval)

    def set_on_status_change(self, callback: Callable[[bool], None]) -> None:
        """
        设置状态变化回调。
        
        Args:
            callback: 状态变化时调用的回调函数，参数为新的在线状态
        """
        self._on_status_change = callback
