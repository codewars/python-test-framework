"""Exercise the public decorators in isolated Python processes."""

import collections
import json
import multiprocessing
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import textwrap
import unittest


@unittest.skipUnless(sys.platform == "linux", "Codewars timeout runtime is Linux")
class TestCompatibility(unittest.TestCase):
    records = []

    def run_case(self, source, passed=0, failed=0, errors=0, exit_code=0):
        root = str(Path(__file__).resolve().parent.parent)
        env = dict(os.environ, PYTHONPATH=root, PYTHONDONTWRITEBYTECODE="1",
                   PYTHON_COLORS="0", NO_COLOR="1")
        process = subprocess.Popen(
            [sys.executable, "-c", textwrap.dedent(source)],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True, start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            # Kill the entire test process group, including a stuck timeout
            # child, so a timeout regression cannot hang the test harness.
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            self.fail("Fixture exceeded 10 seconds:\n" + stdout + stderr)
        self.records.append({"name": self.id().split(".")[-1],
                             "stdout": stdout, "stderr": stderr,
                             "exit_code": process.returncode})
        self.assertEqual(process.returncode, exit_code, stdout + stderr)
        markers = collections.Counter(re.findall(
            r"^<(PASSED|FAILED|ERROR)::>", stdout, flags=re.MULTILINE))
        self.assertEqual(dict(markers), {key: value for key, value in
                         (("PASSED", passed), ("FAILED", failed), ("ERROR", errors))
                         if value}, stdout + stderr)
        return stdout

    @classmethod
    def tearDownClass(cls):
        # Optional captured output can also be checked with the real Exo parser.
        destination = os.environ.get("CW10_RESULTS")
        if destination:
            Path(destination).write_text(json.dumps({
                "python": platform.python_version(), "machine": platform.machine(),
                "multiprocessing_default": multiprocessing.get_start_method(),
                "cases": cls.records,
            }, indent=2) + "\n")

    def test_timeout_preserves_closures_and_pass_count(self):
        self.run_case('''
            import codewars_test as test
            def parent():
                value = 42
                @test.timeout(2)
                def child():
                    test.assert_equals(value, 42)
            parent()
        ''', passed=2)

    def test_timeout_preserves_empty_success(self):
        self.run_case('''
            import codewars_test as test
            @test.timeout(2)
            def child():
                pass
        ''', passed=1)

    def test_timeout_does_not_change_global_start_method(self):
        self.run_case('''
            import multiprocessing as mp
            import codewars_test as test
            before = mp.get_start_method(allow_none=True)
            @test.timeout(2)
            def child():
                test.pass_()
            assert mp.get_start_method(allow_none=True) == before
            assert not mp.active_children()
        ''', passed=2)

    def test_timeout_works_with_explicit_forkserver(self):
        self.run_case('''
            import multiprocessing as mp
            import codewars_test as test
            mp.set_start_method("forkserver")
            @test.timeout(2)
            def child():
                test.pass_()
            assert mp.get_start_method() == "forkserver"
        ''', passed=2)

    def test_nested_timeouts(self):
        self.run_case('''
            import codewars_test as test
            @test.timeout(3)
            def outer():
                @test.timeout(2)
                def inner():
                    test.pass_()
        ''', passed=3)

    def test_timeout_keeps_assertion_failure_and_continuation(self):
        self.run_case('''
            import codewars_test as test
            @test.timeout(2)
            def child():
                test.assert_equals(1, 2)
                test.pass_()
        ''', passed=2, failed=1)

    def test_timeout_expiry_reaps_child(self):
        output = self.run_case('''
            import time
            import multiprocessing as mp
            import codewars_test as test
            @test.timeout(0.1)
            def child():
                time.sleep(5)
            assert not mp.active_children()
        ''', failed=1)
        self.assertIn("Exceeded time limit of 0.100 seconds", output)

    def test_timeout_kills_child_ignoring_termination(self):
        output = self.run_case('''
            import time
            import signal
            import multiprocessing as mp
            import codewars_test as test
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            @test.timeout(0.1)
            def child():
                while True:
                    time.sleep(1)
            assert not mp.active_children()
        ''', failed=1)
        self.assertIn("Exceeded time limit", output)

    def test_timeout_reports_nonzero_child_exit_after_pass(self):
        output = self.run_case('''
            import os
            import multiprocessing as mp
            import codewars_test as test
            @test.timeout(2)
            def child():
                test.pass_()
                os._exit(7)
            assert not mp.active_children()
        ''', passed=1, failed=1)
        self.assertIn("exited with code 7", output)

    def test_timeout_reports_early_zero_exit_after_pass(self):
        output = self.run_case('''
            import os
            import codewars_test as test
            @test.timeout(2)
            def child():
                test.pass_()
                os._exit(0)
        ''', passed=1, failed=1)
        self.assertIn("exited before completing", output)

    def test_timeout_reports_signal_exit(self):
        output = self.run_case('''
            import os
            import signal
            import codewars_test as test
            @test.timeout(2)
            def child():
                os.kill(os.getpid(), signal.SIGKILL)
        ''', failed=1)
        self.assertIn("exited with code -9", output)

    def test_timeout_reports_exception_once(self):
        output = self.run_case('''
            import codewars_test as test
            @test.timeout(2)
            def child():
                raise ValueError("child error")
        ''', failed=1)
        self.assertIn("ValueError('child error')", output)

    def test_timeout_preserves_system_exit_failure(self):
        output = self.run_case('''
            import codewars_test as test
            @test.timeout(2)
            def child():
                raise SystemExit(0)
        ''', failed=1)
        self.assertIn("SystemExit(0)", output)

    def test_timeout_start_failure_is_reported(self):
        output = self.run_case('''
            from unittest.mock import patch
            from multiprocessing.process import BaseProcess
            import codewars_test as test
            with patch.object(BaseProcess, "start", side_effect=OSError("start denied")):
                @test.timeout(2)
                def child():
                    test.pass_()
        ''', failed=1)
        self.assertIn("start denied", output)

    def test_allow_raise_closes_group_once_and_runs_after_hook(self):
        output = self.run_case('''
            import codewars_test as test
            @test.describe("outer")
            def group():
                @test.it("first", after=lambda: print("CLEANUP"))
                def first():
                    test.assert_equals(1, 2, "author context", allow_raise=True)
                    print("UNREACHABLE")
                @test.it("second")
                def second():
                    test.pass_()
        ''', passed=1, failed=1)
        self.assertIn("author context: 1 should equal 2", output)
        self.assertIn("CLEANUP", output)
        self.assertNotIn("UNREACHABLE", output)
        self.assertEqual(output.count("<COMPLETEDIN::>"), 3)

    def test_timeout_allow_raise_reports_once(self):
        output = self.run_case('''
            import codewars_test as test
            @test.timeout(2)
            def child():
                test.assert_equals(1, 2, "author context", allow_raise=True)
                print("UNREACHABLE")
        ''', failed=1)
        self.assertIn("author context: 1 should equal 2", output)
        self.assertNotIn("UNREACHABLE", output)

    def test_default_assertions_still_continue(self):
        self.run_case('''
            import codewars_test as test
            @test.it("continuation")
            def case():
                test.assert_equals(1, 2)
                test.pass_()
        ''', passed=1, failed=1)

    def test_top_level_allow_raise_still_propagates(self):
        output = self.run_case('''
            import codewars_test as test
            test.assert_equals(1, 2, allow_raise=True)
            print("UNREACHABLE")
        ''', failed=1, exit_code=1)
        self.assertNotIn("UNREACHABLE", output)


if __name__ == "__main__":
    unittest.main()
