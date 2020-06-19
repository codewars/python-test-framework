# Codewars Test Framework for Python

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

### Using Other Assertions

Any function that raises an `AssertionError` can be used alongside built-in `codewars_test` assertions. Decorate the function using `codewars_test.make_assertion` before calling it. This ensures that test output is correctly formatted as expected by the runner. In the following example, the tests are intended to fail in order to show the custom output.

```python
import numpy as np
import pandas as pd
import codewars_test as test

@test.describe('Example Tests')
def test_custom_assertions():
    np.testing.assert_equal = test.make_assertion(np.testing.assert_equal)
    pd.testing.assert_frame_equal = test.make_assertion(pd.testing.assert_frame_equal)

    @test.make_assertion
    def custom_assert_eq(actual, expected, msg=None):
        if actual != expected:
            default_msg = f'`{actual}` did not equal expected `{expected}`'
            raise AssertionError(default_msg if msg is None else msg)

    @test.it('Test something in numpy')
    def test_numpy_assertion():
        actual = np.reshape(range(16), [4, 4])
        expected = np.reshape(range(16, 0, -1), [4, 4])
        np.testing.assert_equal(actual, expected)

    @test.it('Test something in pandas')
    def test_pandas_assertion():
        actual = pd.DataFrame({'foo': [1, 2, 3]})
        expected = pd.DataFrame({'foo': [1, 42, 3]})
        pd.testing.assert_frame_equal(actual, expected)

    @test.it('Test something using a custom assertion')
    def test_custom_assertion():
        actual = 2
        expected = 1
        custom_assert_eq(actual, expected)
```

