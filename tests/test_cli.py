import sys
import unittest
from contextlib import contextmanager

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

from vpk import cli


@contextmanager
def capture_stdout():
    new_out = StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield sys.stdout
    finally:
        sys.stdout = old_out


class testcase_cli(unittest.TestCase):
    def setUp(self):
        self.vpk_path = './tests/test_dir.vpk'
        self.parser = cli.make_argparser()
        self.vpk_content = ['testfile1.txt', 'testdir/testfile2.txt', 'a/b/c/d/testfile3.bin']

    def run_cli_with_args(self, args):
        args = self.parser.parse_args(args)
        with capture_stdout() as stdout:
            cli.run(args)
        stdout = stdout.getvalue().split()
        return stdout

    def test_cli_list(self):
        stdout = self.run_cli_with_args([self.vpk_path, '--list'])
        self.assertEqual(len(stdout), len(self.vpk_content))
        for expected_content in self.vpk_content:
            self.assertIn(expected_content, stdout)

    def test_cli_list_filter_filter(self):
        # filter on file name
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '--filter',  '*file2*'])
        self.assertEqual(len(stdout), 1)
        self.assertIn(self.vpk_content[1], stdout)

        # filter on dir name
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '--filter', 'testdir*'])
        self.assertEqual(len(stdout), 1)
        self.assertIn(self.vpk_content[1], stdout)

        # use filter as exclusion
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '--filter', '*file2*', '-v'])
        self.assertEqual(len(stdout), 2)
        self.assertIn(self.vpk_content[0], stdout)
        self.assertIn(self.vpk_content[2], stdout)

    def test_cli_list_filter_name(self):
        # filter on file name
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '-name',  '*file2*'])
        self.assertEqual(len(stdout), 1)
        self.assertIn(self.vpk_content[1], stdout)

        # filter on dir name (should not work)
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '-name', 'testdir*'])
        self.assertEqual(len(stdout), 0)

        # use filter as exclusion
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '-name',  '*file2*', '-v'])
        self.assertEqual(len(stdout), 2)
        self.assertIn(self.vpk_content[0], stdout)
        self.assertIn(self.vpk_content[2], stdout)

    def test_cli_list_filter_regex(self):
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '--regex',  r'file2\.t[tx]{2}$'])
        self.assertEqual(len(stdout), 1)
        self.assertIn(self.vpk_content[1], stdout)

        # use filter as exclusion
        stdout = self.run_cli_with_args([self.vpk_path, '--list', '--regex',  r'file2\.t[tx]{2}$', '-v'])
        self.assertEqual(len(stdout), 2)
        self.assertIn(self.vpk_content[0], stdout)
        self.assertIn(self.vpk_content[2], stdout)
