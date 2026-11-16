"""User and profile models, independent of Linux and GTK."""
import shlex
from typing import List, Dict, Optional


class ConnectionProfile:
    """Representa uma fonte de conexão específica de um usuário RDP"""

    def __init__(self, profile_id: str, name: str, profile_type: str = 'desktop',
                 desktop_env: str = 'xfce', app_command: str = '',
                 app_args: str = '', is_default: bool = False,
                 command_argv: Optional[List[str]] = None,
                 working_directory: str = '', environment: Optional[Dict[str, str]] = None,
                 runtime: str = '', resource_profile: str = '',
                 windows_app_id: str = ''):
        self.profile_id = profile_id
        self.name = name
        self.profile_type = profile_type  # 'desktop', 'remoteapp', 'winege-remoteapp'
        self.desktop_env = desktop_env
        self.app_command = app_command
        self.app_args = app_args
        self.is_default = is_default
        self.command_argv = command_argv or self._legacy_argv(app_command, app_args)
        self.working_directory = working_directory
        self.environment = environment or {}
        self.runtime = runtime or ('umu' if profile_type == 'winege-remoteapp' else 'native')
        self.resource_profile = resource_profile or (
            'windows-standard' if profile_type == 'winege-remoteapp' else 'linux-light'
        )
        self.windows_app_id = windows_app_id

    @staticmethod
    def _legacy_argv(app_command: str, app_args: str) -> List[str]:
        if not app_command:
            return []
        try:
            return [app_command] + shlex.split(app_args)
        except ValueError:
            return [app_command]

    def to_dict(self) -> Dict:
        return {
            'profile_id': self.profile_id,
            'name': self.name,
            'profile_type': self.profile_type,
            'desktop_env': self.desktop_env,
            'app_command': self.app_command,
            'app_args': self.app_args,
            'is_default': self.is_default,
            'command_argv': self.command_argv,
            'working_directory': self.working_directory,
            'environment': self.environment,
            'runtime': self.runtime,
            'resource_profile': self.resource_profile,
            'windows_app_id': self.windows_app_id,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ConnectionProfile':
        return cls(
            profile_id=data.get('profile_id', 'default'),
            name=data.get('name', 'Fonte de Conexão'),
            profile_type=data.get('profile_type', data.get('session_type', 'desktop')),
            desktop_env=data.get('desktop_env', 'xfce'),
            app_command=data.get('app_command', ''),
            app_args=data.get('app_args', ''),
            is_default=data.get('is_default', False),
            command_argv=data.get('command_argv'),
            working_directory=data.get('working_directory', ''),
            environment=data.get('environment', {}),
            runtime=data.get('runtime', ''),
            resource_profile=data.get('resource_profile', ''),
            windows_app_id=data.get('windows_app_id', '')
        )


class RDPUser:
    """Representa um usuário RDP com suporte a múltiplas fontes de conexão"""

    def __init__(self, username: str, uid: int, home_dir: str,
                 desktop_env: str = 'xfce', rdp_port: int = 3389, active: bool = False, enabled: bool = True,
                 is_superuser: bool = False, session_type: str = 'desktop',
                 app_command: str = '', app_args: str = '',
                 profiles: Optional[List[ConnectionProfile]] = None,
                 is_personal: bool = False):
        self.username = username
        self.uid = uid
        self.home_dir = home_dir
        self.rdp_port = rdp_port
        self.active = active
        self.enabled = enabled  # Se a conta está habilitada (não bloqueada)
        self.is_superuser = is_superuser  # Se o usuário tem privilégios sudo
        self.is_personal = is_personal  # Se é conta pessoal/existente fora de /opt/rdp-users
        self.profiles = profiles or []

        # Se profiles estiver vazio, gera o perfil padrão baseado em session_type
        if not self.profiles:
            def_name = "Área de Trabalho" if session_type == 'desktop' else (
                f"RemoteApp ({app_command})" if session_type == 'remoteapp' else "Windows App (umu)"
            )
            self.profiles = [
                ConnectionProfile(
                    profile_id="default",
                    name=def_name,
                    profile_type=session_type,
                    desktop_env=desktop_env,
                    app_command=app_command,
                    app_args=app_args,
                    is_default=True
                )
            ]

    @property
    def default_profile(self) -> ConnectionProfile:
        for p in self.profiles:
            if p.is_default:
                return p
        return self.profiles[0] if self.profiles else ConnectionProfile('default', 'Padrão')

    @property
    def session_type(self) -> str:
        return self.default_profile.profile_type

    @session_type.setter
    def session_type(self, val: str):
        self.default_profile.profile_type = val

    @property
    def desktop_env(self) -> str:
        return self.default_profile.desktop_env

    @desktop_env.setter
    def desktop_env(self, val: str):
        self.default_profile.desktop_env = val

    @property
    def app_command(self) -> str:
        return self.default_profile.app_command

    @app_command.setter
    def app_command(self, val: str):
        self.default_profile.app_command = val

    @property
    def app_args(self) -> str:
        return self.default_profile.app_args

    @app_args.setter
    def app_args(self, val: str):
        self.default_profile.app_args = val

    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'username': self.username,
            'uid': self.uid,
            'home_dir': self.home_dir,
            'desktop_env': self.desktop_env,
            'rdp_port': self.rdp_port,
            'active': self.active,
            'enabled': self.enabled,
            'is_superuser': self.is_superuser,
            'is_personal': self.is_personal,
            'session_type': self.session_type,
            'app_command': self.app_command,
            'app_args': self.app_args,
            'profiles': [p.to_dict() for p in self.profiles]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RDPUser':
        """Cria instância a partir de dicionário"""
        data_copy = dict(data)
        profiles_data = data_copy.pop('profiles', None)
        profiles = [ConnectionProfile.from_dict(p) for p in profiles_data] if profiles_data else None
        user = cls(**data_copy, profiles=profiles)
        return user


