import unittest
import subprocess
import os
import re
from pathlib import Path


class TestOutputs(unittest.TestCase):
    pass


def test_against_expected(test_file, expected_file, env):
    def test(self):
        # Using `stdout=PIPE, stderr=PIPE` for Python 3.6 compatibility instead of `capture_output=True`
        result = subprocess.run(
            ["python", test_file],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with open(expected_file, "r", encoding="utf-8") as r:
            # Allow duration to change
            expected = re.sub(r"([()])", r"\\\1", r.read())
            expected = re.sub(
                r"(?<=<COMPLETEDIN::>)\d+(?:\.\d+)?", r"\\d+(?:\\.\\d+)?", expected
            )

            self.assertRegex(result.stdout.decode("utf-8"), expected)

    return test


def get_commands(output):
    return re.findall(r"<(?:DESCRIBE|IT|PASSED|FAILED|ERROR|COMPLETEDIN)::>", output)


def test_against_sample(test_file, sample_file, env):
    def test(self):
        # Using `stdout=PIPE, stderr=PIPE` for Python 3.6 compatibility instead of `capture_output=True`
        result = subprocess.run(
            ["python", test_file],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        with open(sample_file, "r", encoding="utf-8") as r:
            # Ensure that it contains the same output structure
            self.assertEqual(
                get_commands(result.stdout.decode("utf-8")), get_commands(r.read())
            )

    return test


def define_tests():
    fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")
    package_dir = Path(fixtures_dir).parent.parent
    files = (f for f in os.listdir(fixtures_dir) if f.endswith(".py"))
    for f in files:
        expected_file = os.path.join(fixtures_dir, f.replace(".py", ".expected.txt"))
        if os.path.exists(expected_file):
            test_func = test_against_expected(
                os.path.join(fixtures_dir, f),
                expected_file,
                {"PYTHONPATH": package_dir},
            )
        else:
            # Use `.sample.txt` when testing against outputs with more variables.
            # This version only checks for the basic structure.
            test_func = test_against_sample(
                os.path.join(fixtures_dir, f),
                os.path.join(fixtures_dir, f.replace(".py", ".sample.txt")),
                {"PYTHONPATH": package_dir},
            )
        setattr(TestOutputs, "test_{0}".format(f.replace(".py", "")), test_func)


define_tests()

if __name__ == "__main__":
    unittest.main()
