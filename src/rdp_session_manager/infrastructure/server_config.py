#!/usr/bin/env python3
"""System-wide configuration for server-oriented RDP deployments."""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Dict


from rdp_session_manager.domain.server import ServerSettings, RESOURCE_PROFILES


class ServerConfig:
    """Read system configuration without requiring write access to /etc."""

    def __init__(self, path: str | Path = "/etc/rdp-session-manager/server.ini"):
        self.path = Path(path)

    def load(self) -> ServerSettings:
        parser = configparser.ConfigParser()
        if self.path.exists():
            parser.read(self.path)
        return ServerSettings.from_parser(parser)

    def load_resource_profiles(self) -> Dict[str, Dict[str, int]]:
        parser = configparser.ConfigParser()
        if self.path.exists():
            parser.read(self.path)
        profiles = {name: dict(values) for name, values in RESOURCE_PROFILES.items()}
        for name, defaults in profiles.items():
            section = f"resource:{name}"
            if not parser.has_section(section):
                continue
            for key in defaults:
                try:
                    value = parser.getint(section, key)
                except (ValueError, configparser.Error):
                    continue
                if value > 0:
                    defaults[key] = value
        return profiles

    @staticmethod
    def render(
        settings: ServerSettings,
        resource_profiles: Dict[str, Dict[str, int]] | None = None,
    ) -> str:
        resource_profiles = resource_profiles or RESOURCE_PROFILES
        parser = configparser.ConfigParser()
        parser["server"] = {key: str(value) for key, value in settings.to_dict().items()}
        for name, values in resource_profiles.items():
            parser[f"resource:{name}"] = {
                key: str(value) for key, value in values.items()
            }
        from io import StringIO

        output = StringIO()
        parser.write(output)
        return output.getvalue()
