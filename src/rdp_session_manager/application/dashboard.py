"""One consistent refresh for every dashboard consumer."""
from dataclasses import dataclass
from typing import List, Optional
from rdp_session_manager.application.ports import UserRepository, SessionRepository
from rdp_session_manager.domain.users import RDPUser
from rdp_session_manager.domain.sessions import SessionInfo


@dataclass(frozen=True)
class DashboardSnapshot:
    users: List[RDPUser]
    sessions: List[SessionInfo]
    ip_address: str
    xrdp_ready: Optional[bool] = None

    @property
    def active_usernames(self):
        return {session.username for session in self.sessions}

    @property
    def enabled_session_count(self):
        enabled = {user.username for user in self.users if user.enabled}
        return sum(session.username in enabled for session in self.sessions)


class Dashboard:
    def __init__(self, users: UserRepository, sessions: SessionRepository, readiness=None):
        self.users = users
        self.sessions = sessions
        self.readiness = readiness

    def collect(self, check_readiness=False):
        return DashboardSnapshot(
            users=self.users.list_users(),
            sessions=self.sessions.get_active_sessions(),
            ip_address=self.sessions.get_ip_address(),
            xrdp_ready=self.readiness() if check_readiness and self.readiness else None,
        )
