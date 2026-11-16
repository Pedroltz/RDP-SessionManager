"""Read profile schemas and persist them through the privileged helper."""
import json
import logging
from pathlib import Path
import tempfile
from typing import List
from rdp_session_manager.domain.users import ConnectionProfile
from rdp_session_manager.infrastructure.commands import run_command
from rdp_session_manager.infrastructure.paths import helper_dir
from rdp_session_manager.infrastructure.polkit import get_privilege_command

logger = logging.getLogger(__name__)


class ProfileRepository:
    def load_profiles_for_user(self, home_dir: str, default_session_type: str = 'desktop',
                               default_de: str = 'xfce', default_cmd: str = '',
                               default_args: str = '') -> List[ConnectionProfile]:
        """Carrega lista de ConnectionProfile da home do usuário ou migra a sessão existente"""
        profiles_file = Path(home_dir) / '.rdp_profiles.json'
        content = None
        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    content = f.read()
            except Exception as e:
                # Listing users must never trigger an authentication dialog.
                # Provisioning and repair keep this non-secret metadata
                # readable by the management application.
                logger.warning(
                    "Could not read %s without elevation: %s",
                    profiles_file,
                    e,
                )

        if content:
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    data = data.get('profiles', [])
                if isinstance(data, list) and len(data) > 0:
                    return [ConnectionProfile.from_dict(item) for item in data]
            except Exception as e:
                logger.error(f"Erro ao parsear .rdp_profiles.json em {home_dir}: {e}")

        # Fallback para perfil legado único
        def_name = "Área de Trabalho" if default_session_type == 'desktop' else (
            f"RemoteApp ({default_cmd})" if default_session_type == 'remoteapp' else "Windows App (umu)"
        )
        return [
            ConnectionProfile(
                profile_id="default",
                name=def_name,
                profile_type=default_session_type,
                desktop_env=default_de,
                app_command=default_cmd,
                app_args=default_args,
                is_default=True
            )
        ]

    def save_profiles_for_user(self, username, profiles):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as stream:
                temporary = Path(stream.name)
                json.dump({'schema_version': 2, 'profiles': [profile.to_dict() for profile in profiles]}, stream, indent=2)
            _, privilege = get_privilege_command()
            result = run_command(
                privilege + [str(helper_dir() / 'update-rdp-user-profiles.sh'), username, str(temporary)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode:
                logger.error('Could not save profiles for %s: %s', username, result.stderr)
                return False
            return True
        except Exception as exc:
            logger.error('Could not save profiles for %s: %s', username, exc)
            return False
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
