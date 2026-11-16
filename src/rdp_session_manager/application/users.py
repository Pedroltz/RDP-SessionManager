"""Shared account use cases, serializing reads against account mutations."""
from threading import RLock
from rdp_session_manager.application.ports import UserRepository, SessionRepository


class UserService:
    def __init__(self, repository: UserRepository, sessions: SessionRepository, lock=None):
        self.repository = repository
        self.sessions = sessions
        self._lock = lock or RLock()

    def _query(self, name, *args, **kwargs):
        with self._lock:
            return getattr(self.repository, name)(*args, **kwargs)

    def _mutate(self, name, *args, **kwargs):
        with self._lock:
            try:
                return getattr(self.repository, name)(*args, **kwargs)
            finally:
                # A failed helper can still have changed part of the system.
                self.sessions.invalidate()

    def create_user(self, *args, **kwargs):
        return self._mutate("create_user", *args, **kwargs)

    def enable_personal_rdp(self, *args, **kwargs):
        return self._mutate("enable_personal_rdp", *args, **kwargs)

    def get_current_username(self, *args, **kwargs):
        return self._query("get_current_username", *args, **kwargs)

    def diagnose_user(self, *args, **kwargs):
        return self._query("diagnose_user", *args, **kwargs)

    def repair_user(self, *args, **kwargs):
        return self._mutate("repair_user", *args, **kwargs)

    def get_user_processes(self, *args, **kwargs):
        return self._query("get_user_processes", *args, **kwargs)

    def kill_user_processes(self, *args, **kwargs):
        return self._mutate("kill_user_processes", *args, **kwargs)

    def delete_user(self, *args, **kwargs):
        return self._mutate("delete_user", *args, **kwargs)

    def lock_user(self, *args, **kwargs):
        return self._mutate("lock_user", *args, **kwargs)

    def unlock_user(self, *args, **kwargs):
        return self._mutate("unlock_user", *args, **kwargs)

    def grant_sudo(self, *args, **kwargs):
        return self._mutate("grant_sudo", *args, **kwargs)

    def revoke_sudo(self, *args, **kwargs):
        return self._mutate("revoke_sudo", *args, **kwargs)

    def is_superuser(self, *args, **kwargs):
        return self._query("is_superuser", *args, **kwargs)

    def user_exists(self, *args, **kwargs):
        return self._query("user_exists", *args, **kwargs)

    def list_users(self, *args, **kwargs):
        return self._query("list_users", *args, **kwargs)

    def load_profiles_for_user(self, *args, **kwargs):
        return self._query("load_profiles_for_user", *args, **kwargs)

    def save_profiles_for_user(self, *args, **kwargs):
        return self._mutate("save_profiles_for_user", *args, **kwargs)

    def export_rdp_file(self, *args, **kwargs):
        return self._query("export_rdp_file", *args, **kwargs)

    def get_user(self, *args, **kwargs):
        return self._query("get_user", *args, **kwargs)

    def change_password(self, *args, **kwargs):
        return self._mutate("change_password", *args, **kwargs)

    def rename_user(self, *args, **kwargs):
        return self._mutate("rename_user", *args, **kwargs)

    def change_user_fullname(self, *args, **kwargs):
        return self._mutate("change_user_fullname", *args, **kwargs)

    def list_user_executables(self, *args, **kwargs):
        return self._query("list_user_executables", *args, **kwargs)

    def update_winege_executable(self, *args, **kwargs):
        return self._mutate("update_winege_executable", *args, **kwargs)

    def change_user_session_type(self, *args, **kwargs):
        return self._mutate("change_user_session_type", *args, **kwargs)

