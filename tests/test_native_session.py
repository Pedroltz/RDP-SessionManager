"""Regression coverage for X11 desktop startup and daemonizing RemoteApps."""

import itertools
import os
import signal
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tests.test_server_mode import load_session_helper


class NativeSessionTest(unittest.TestCase):
    def setUp(self):
        self.session = load_session_helper()
        self.app = Mock(pid=98765)
        self.app.poll.return_value = 0
        self.wm = Mock()
        self.wm.poll.return_value = None

    def supervise(self, windows):
        with (
            patch.object(self.session, "client_windows", side_effect=windows),
            patch.object(self.session.time, "sleep"),
            patch.object(self.session.time, "monotonic", side_effect=itertools.count(0, 0.25)),
        ):
            return self.session.wait_native_application(self.app, self.wm, {"DISPLAY": ":42"})

    def test_launcher_exit_keeps_delayed_window_alive_until_closed(self):
        result = self.supervise([set(), set(), {"0x1"}, {"0x1"}, *[set()] * 5])
        self.assertEqual(result, 0)
        self.assertEqual(self.app.poll.call_count, 9)

    def test_foreground_app_is_kept_while_window_exists(self):
        self.app.poll.return_value = None
        self.assertEqual(self.supervise([{"0x1"}, {"0x1"}, *[set()] * 5]), 0)

    def test_window_replacement_resets_close_grace(self):
        self.assertEqual(self.supervise([
            {"0x1"}, set(), set(), {"0x2"}, set(), set(), set(), set(), set(),
        ]), 0)
        self.assertEqual(self.app.poll.call_count, 9)

    def test_successful_launcher_without_window_has_bounded_wait(self):
        self.assertEqual(self.supervise(itertools.repeat(set())), 0)
        self.assertEqual(self.app.poll.call_count, 61)

    def test_launch_failure_preserves_error_without_waiting(self):
        self.app.poll.return_value = 23
        self.assertEqual(self.supervise([]), 23)

    def test_window_manager_failure_is_reported(self):
        self.wm.poll.return_value = 1
        with self.assertRaisesRegex(RuntimeError, "Openbox"):
            self.supervise([])

    def test_query_failure_is_reported_instead_of_empty_desktop(self):
        with self.assertRaisesRegex(RuntimeError, "Cannot monitor"):
            self.supervise([subprocess.TimeoutExpired("xprop", 2)])

    def test_window_query_uses_session_display_and_ignores_zero(self):
        environment = {"DISPLAY": ":42", "XAUTHORITY": "/example/.Xauthority"}
        with patch.object(self.session.subprocess, "run", return_value=Mock(
            stdout="_NET_CLIENT_LIST(WINDOW): window id # 0x0, 0xAb12, 0x32",
        )) as run:
            self.assertEqual(self.session.client_windows(environment), {"0xAb12", "0x32"})
        self.assertEqual(run.call_args.kwargs["env"], environment)
        self.assertEqual(run.call_args.args[0], ["xprop", "-root", "_NET_CLIENT_LIST"])

    def test_cleanup_signals_descendants_after_launcher_exits(self):
        with patch.object(self.session.os, "killpg", side_effect=[None, ProcessLookupError()]) as kill:
            self.session.terminate_group(self.app, descendants=True)
        self.assertEqual(kill.call_args_list[0].args, (self.app.pid, signal.SIGTERM))

    def test_desktops_receive_x11_environment(self):
        for desktop, current, session in (
            ("gnome", "GNOME-Flashback:GNOME", "gnome-flashback-metacity"),
            ("xfce", "XFCE", "xfce"),
            ("kde", "KDE", "plasma"),
        ):
            with (
                self.subTest(desktop=desktop),
                patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0", "XDG_SESSION_TYPE": "wayland"}),
                patch.object(self.session.Path, "is_file", return_value=True),
                patch.object(self.session.shutil, "which", return_value="/usr/bin/session"),
                patch.object(self.session, "update_activation_environment"),
                patch.object(self.session.os, "execvp") as execute,
            ):
                self.session.start_desktop({"desktop_env": desktop})
                self.assertEqual(os.environ["XDG_SESSION_TYPE"], "x11")
                self.assertEqual(os.environ["XDG_CURRENT_DESKTOP"], current)
                self.assertEqual(os.environ["DESKTOP_SESSION"], session)
                self.assertNotIn("WAYLAND_DISPLAY", os.environ)
                self.assertEqual(execute.call_args.args[1], self.session.desktop_argv({"desktop_env": desktop}))

    def test_missing_flashback_gives_repair_instruction(self):
        with (
            patch.dict(os.environ),
            patch.object(self.session.Path, "is_file", return_value=False),
            patch.object(self.session.os, "execvp") as execute,
        ):
            with self.assertRaisesRegex(RuntimeError, "rdpsm de install gnome"):
                self.session.start_desktop({"desktop_env": "gnome"})
            execute.assert_not_called()

    def test_activation_receives_only_display_and_desktop_variables(self):
        environment = {
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/5000/bus",
            "DISPLAY": ":42", "XDG_CURRENT_DESKTOP": "Openbox", "PRIVATE_TOKEN": "secret",
        }
        with (
            patch.object(self.session.shutil, "which", return_value="/usr/bin/dbus-update-activation-environment"),
            patch.object(self.session.subprocess, "run", return_value=Mock(returncode=0)) as run,
        ):
            self.session.update_activation_environment(environment)
        self.assertEqual(run.call_args.args[0], [
            "/usr/bin/dbus-update-activation-environment", "--systemd", "DISPLAY", "XDG_CURRENT_DESKTOP",
        ])
        self.assertEqual(run.call_args.kwargs["env"], environment)

    def test_native_supervision_does_not_change_windows_wait_behavior(self):
        for profile_type in ("remoteapp", "winege-remoteapp"):
            native = profile_type == "remoteapp"
            with (
                self.subTest(profile_type=profile_type),
                tempfile.TemporaryDirectory() as directory,
                patch.object(self.session.subprocess, "Popen", side_effect=[self.wm, self.app]) as launch,
                patch.object(self.session, "runtime_argv", return_value=["example", "hello world"]),
                patch.object(self.session, "wait_native_application", return_value=0) as supervise,
                patch.object(self.session, "terminate_group") as terminate,
                patch.object(self.session, "update_activation_environment"),
                patch.object(self.session, "promote_installed_executable", return_value=None),
                patch.object(self.session, "mark_runtime_validated"),
                patch.object(self.session.shutil, "which", side_effect=lambda name: "/usr/bin/xprop" if name == "xprop" else None),
                patch.object(self.session.time, "sleep"),
                patch.dict(os.environ, {"DISPLAY": ":42", "WAYLAND_DISPLAY": "wayland-0"}),
            ):
                self.app.wait.return_value = 0
                self.app.wait.reset_mock()
                profile = {"profile_type": profile_type, "command_argv": ["example", "hello world"]}
                self.assertEqual(self.session.run_remoteapp(profile, Path(directory)), 0)
                launched_environment = launch.call_args_list[1].kwargs["env"]
                if native:
                    supervise.assert_called_once_with(self.app, self.wm, launched_environment)
                    self.app.wait.assert_not_called()
                    self.assertNotIn("WAYLAND_DISPLAY", launched_environment)
                    self.assertEqual(launched_environment["XDG_SESSION_TYPE"], "x11")
                else:
                    supervise.assert_not_called()
                    self.app.wait.assert_called_once()
                self.assertEqual(launch.call_args_list[1].args[0], ["example", "hello world"])
                self.assertEqual(terminate.call_args_list[0].kwargs, {"descendants": native})


if __name__ == "__main__":
    unittest.main()
