"""Portable session data and duration calculation."""
from datetime import datetime
from typing import Dict


class SessionInfo:
    """Informações de uma sessão RDP"""

    def __init__(self, username: str, session_id: str = "", ip_address: str = "",
                 port: int = 0, connected: bool = False, start_time: datetime = None,
                 memory_mb: float = 0.0, cpu_percent: float = 0.0,
                 process_count: int = 0):
        self.username = username
        self.session_id = session_id
        self.ip_address = ip_address
        self.port = port
        self.connected = connected
        self.start_time = start_time or datetime.now()
        self.memory_mb = memory_mb
        self.cpu_percent = cpu_percent
        self.process_count = process_count

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'username': self.username,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'port': self.port,
            'connected': self.connected,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'duration': self.get_duration(),
            'memory_mb': round(self.memory_mb, 2),
            'cpu_percent': round(self.cpu_percent, 2),
            'process_count': self.process_count,
        }

    def get_duration(self) -> int:
        """Retorna duração da sessão em segundos"""
        if self.start_time:
            return int((datetime.now() - self.start_time).total_seconds())
        return 0


