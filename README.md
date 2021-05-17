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
