"""Composition root shared by GTK, CLI, and installed entry points."""
from functools import cached_property
from threading import RLock
from rdp_session_manager.application.dashboard import Dashboard
from rdp_session_manager.application.users import UserService
from rdp_session_manager.application.remediation import RemediationService
from rdp_session_manager.infrastructure.user_manager import UserManager as LinuxUsers
from rdp_session_manager.infrastructure.session_monitor import SessionMonitor
from rdp_session_manager.infrastructure.config import AppConfig
from rdp_session_manager.infrastructure.rdp_config import RDPConfig
from rdp_session_manager.infrastructure.de_installer import DEInstaller
from rdp_session_manager.infrastructure.system_deps import SystemDependencies
from rdp_session_manager.infrastructure.server_manager import ServerManager
from rdp_session_manager.infrastructure.health import HealthService
from rdp_session_manager.infrastructure.audit import AuditStore
from rdp_session_manager.infrastructure.windows_runtime import WindowsRuntimeMigrator
from rdp_session_manager.infrastructure.windows_app import (
    InstallRecipe, RecipeCatalog, WindowsAppError, WindowsAppManager, safe_app_id,
)


class Services:
    """Lazy composition keeps read-only CLI commands out of administrator settings."""
    @cached_property
    def account_lock(self):
        return RLock()

    @cached_property
    def app_config(self):
        return AppConfig()

    @cached_property
    def session_monitor(self):
        return SessionMonitor()

    @cached_property
    def user_manager(self):
        return UserService(LinuxUsers(self.app_config), self.session_monitor, self.account_lock)

    @cached_property
    def readonly_users(self):
        return UserService(LinuxUsers(app_config=None), self.session_monitor, self.account_lock)

    @cached_property
    def server_manager(self):
        return ServerManager()

    @cached_property
    def rdp_config(self):
        return RDPConfig()

    @cached_property
    def de_installer(self):
        return DEInstaller()

    @cached_property
    def system_deps(self):
        return SystemDependencies()

    @cached_property
    def health_service(self):
        return HealthService(self.server_manager, self.readonly_users, self.session_monitor)

    @cached_property
    def remediation_service(self):
        return RemediationService(self.readonly_users)

    @cached_property
    def audit_store(self):
        return AuditStore()

    @cached_property
    def dashboard(self):
        return Dashboard(self.user_manager, self.session_monitor, self.system_deps.is_xrdp_ready)
