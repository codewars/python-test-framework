# Codewars Test Framework for Python

### Installation

```bash
pip install git+https://github.com/codewars/python-test-framework.git#egg=codewars_test
```

### Basic Example

```python
import codewars_test as test
from solution import add

@test.describe('Example Tests')
def example_tests():

    @test.it('Example Test Case')
    def example_test_case():
        test.assert_equals(add(1, 1), 2, 'Optional Message on Failure')
```

### Assertion control flow and timeouts

Assertions report a failure and continue by default. With `allow_raise=True`,
the assertion stops the current decorated block and reports its failure once.
The enclosing `it` or `describe` still closes normally, and its `after` hook
runs. At top level, the framework's assertion exception still propagates.

`@test.timeout(seconds)` executes immediately in a child process. On the
Codewars Linux runtime it uses a local `fork` context so existing nested test
functions work on Python 3.14 without changing the process-wide start method.
Normal completion retains the existing additional passing assertion. An expired
timeout, abnormal exit or exit before the wrapper completes reports a failure;
timed-out children are terminated and joined, including children that ignore
`SIGTERM`. Previously printed assertions remain visible.

The fork context preserves the existing Linux execution model. Tests that start
threads or import libraries with background threads still require validation in
the full runner image. This compatibility change does not make fork safe for
arbitrary multithreaded programs.

### Development tests

Run the output fixtures and compatibility tests with the interpreter under test:

```bash
python -m unittest discover -v
```

The timeout regression tests run on Linux and check success/failure counts,
nested functions, unchanged global start-method selection, early exits, signals,
startup errors, child cleanup and `allow_raise` behavior. Other platforms skip
these Linux-specific checks. Set `CW10_RESULTS` to a writable JSON file path to
capture their raw outputs for integration checks with the Exo result parser.

<!--

### Using Other Assertions

> NOTE: This is not ready for production because the passed test case is not reported correctly.
> See [#9](https://github.com/codewars/python-test-framework/issues/9).

Any function that raises an `AssertionError` can be used instead of `codewars_test` assertions:

```python
import numpy as np
import pandas as pd
import codewars_test as test

@test.describe('Example Tests')
def test_custom_assertions():

    @test.it('Test something in numpy')
    def test_numpy_assertion():
        actual = np.reshape(range(16), [4, 4])
        expected = np.reshape(range(16, 0, -1), [4, 4])
        np.testing.assert_equal(expected, actual)

    @test.it('Test something in pandas')
    def test_pandas_assertion():
        actual = pd.DataFrame({'foo': [1, 2, 3]})
        expected = pd.DataFrame({'foo': [1, 42, 3]})
        pd.testing.assert_frame_equal(expected, actual)

    @test.it('Test something using a custom assertion')
    def test_custom_assertion():
        def custom_assert_eq(actual, expected, msg=None):
            if actual != expected:
                default_msg = f'`{actual}` did not equal expected `{expected}`'
                raise AssertionError(default_msg if msg is None else msg)

        actual = 2
        expected = 1
        custom_assert_eq(actual, expected)
```

-->
