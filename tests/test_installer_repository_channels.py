import unittest
from installer.core import validate_arch_repository_channels, InstallerError

class RepositoryChannelTests(unittest.TestCase):
    def test_reject_partial_testing(self):
        with self.assertRaisesRegex(InstallerError, 'Inconsistent Arch repositories'):
            validate_arch_repository_channels('[core]\n[extra]\n[multilib-testing]\n[multilib]\n')

    def test_accept_stable_and_commented_testing(self):
        validate_arch_repository_channels('[core]\n[extra]\n#[multilib-testing]\n[multilib]\n')

    def test_accept_complete_testing(self):
        validate_arch_repository_channels('[core-testing]\n[extra-testing]\n[multilib-testing]\n')
