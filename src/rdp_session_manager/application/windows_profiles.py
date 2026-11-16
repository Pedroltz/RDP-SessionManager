"""Bind a managed Windows application without retaining stale native argv."""
def bind_windows_application(profile, app_id, executable, launcher_argv):
    profile.profile_type = 'winege-remoteapp'
    profile.windows_app_id = app_id
    profile.app_command = executable
    profile.app_args = ''
    profile.command_argv = [*launcher_argv, app_id]
    profile.runtime = 'managed'
    profile.resource_profile = 'windows-standard'
