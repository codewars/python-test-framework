from __future__ import print_function
import functools
import sys
from multiprocessing import Process
from timeit import default_timer
from traceback import format_exception


class AssertException(Exception):
    pass


def format_message(message):
    return message.replace("\n", "<:LF:>")


def display(type, message, label="", mode=""):
    print("\n<{0}:{1}:{2}>{3}".format(
        type.upper(), mode.upper(), label, format_message(message)))


def expect(passed=None, message=None, allow_raise=False):
    if passed:
        display('PASSED', 'Test Passed')
    else:
        message = message or "Value is not what was expected"
        display('FAILED', message)
        if allow_raise:
            raise AssertException(message)


def assert_equals(actual, expected, message=None, allow_raise=False):
    equals_msg = "{0} should equal {1}".format(repr(actual), repr(expected))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    expect(actual == expected, message, allow_raise)


def assert_not_equals(actual, expected, message=None, allow_raise=False):
    r_actual, r_expected = repr(actual), repr(expected)
    equals_msg = "{0} should not equal {1}".format(r_actual, r_expected)
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    expect(not (actual == expected), message, allow_raise)


def expect_error(message, function, exception=Exception):
    passed = False
    try:
        function()
    except exception:
        passed = True
    except Exception:
        pass
    expect(passed, message)


def expect_no_error(message, function, exception=BaseException):
    try:
        function()
    except exception as e:
        fail("{}: {}".format(message or "Unexpected exception", repr(e)))
        return
    except Exception:
        pass
    pass_()


def pass_(): expect(True)


def fail(message): expect(False, message)


def assert_approx_equals(
        actual, expected, margin=1e-9, message=None, allow_raise=False):
    msg = "{0} should be close to {1} with absolute or relative margin of {2}"
    equals_msg = msg.format(repr(actual), repr(expected), repr(margin))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg
    div = max(abs(actual), abs(expected), 1)
    expect(abs((actual - expected) / div) < margin, message, allow_raise)


def make_assertion(func):
    '''
    Wraps an assertion function to emit pass/failure stdout prints.
    The function should raise an AssertionError to cause a failure.

    @test.make_assertion
    def custom_assert_eq(actual, expected, msg=None):
        if actual != expected:
            default_msg = f'`{actual}` did not equal expected `{expected}`'
            raise AssertionError(default_msg if msg is None else msg)

    # or decorate with a normal function call:
    custom_assert_eq = make_assertion(custom_assert_eq)
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
            pass_()
        except AssertionError as e:
            fail(str(e))
    return wrapper


def _timed_block_factory(opening_text):
    def _timed_block_decorator(s, before=None, after=None):
        display(opening_text, s)

        def wrapper(func):
            if callable(before):
                before()
            time = default_timer()
            try:
                func()
            except Exception:
                fail('Unexpected exception raised')
                tb_str = ''.join(format_exception(*sys.exc_info()))
                display('ERROR', tb_str)
            display('COMPLETEDIN', '{:.2f}'.format((default_timer() - time) * 1000))
            if callable(after):
                after()
        return wrapper
    return _timed_block_decorator


'''
Usage:
@describe('describe text')
def describe1():
    @it('it text')
    def it1():
        # some test cases...
'''
describe = _timed_block_factory('DESCRIBE')
it = _timed_block_factory('IT')


def timeout(sec):
    '''
    Timeout utility
    Usage:
    @timeout(sec)
    def some_tests():
        any code block...
    Note: Timeout value can be a float.
    '''
    def wrapper(func):
        msg = 'Should not throw any exceptions inside timeout'

        def wrapped():
            expect_no_error(msg, func)
        process = Process(target=wrapped)
        process.start()
        process.join(sec)
        if process.is_alive():
            fail('Exceeded time limit of {:.3f} seconds'.format(sec))
            process.terminate()
            process.join()
    return wrapper

