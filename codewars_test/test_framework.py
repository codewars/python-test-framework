from __future__ import print_function
import inspect


class AssertException(Exception):
    pass


def format_message(message):
    return message.replace("\n", "<:LF:>")


def display(type, message, label="", mode=""):
    print(
        "\n<{0}:{1}:{2}>{3}".format(
            type.upper(), mode.upper(), label, format_message(message)
        )
    )


# TODO Currently this only works if assertion functions are written directly in the test case.
def _is_in_test_case():
    frame = inspect.currentframe()
    caller_frame = frame.f_back
    test_case_frame = caller_frame.f_back
    decorator_frame = test_case_frame.f_back
    if not decorator_frame:
        return False
    if not "func" in decorator_frame.f_locals:
        return False
    func = decorator_frame.f_locals["func"]
    code = test_case_frame.f_code
    if func and func.__code__ == code and func.test_case_func:
        return True
    return False


def _handle_test_result(passed, message=None, allow_raise=False, in_test_case=False):
    if passed:
        if not in_test_case:
            display("PASSED", "Test Passed")
    else:
        if not message:
            message = "Value is not what was expected"
        if in_test_case:
            raise AssertionError(message)
        else:
            display("FAILED", message)
            if allow_raise:
                # TODO Use AssertionError?
                raise AssertException(message)


def expect(passed=None, message=None, allow_raise=False):
    _handle_test_result(
        passed, message, allow_raise, _is_in_test_case(),
    )


def assert_equals(actual, expected, message=None, allow_raise=False):
    equals_msg = "{0} should equal {1}".format(repr(actual), repr(expected))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    _handle_test_result(
        actual == expected, message, allow_raise, _is_in_test_case(),
    )


def assert_not_equals(actual, expected, message=None, allow_raise=False):
    r_actual, r_expected = repr(actual), repr(expected)
    equals_msg = "{0} should not equal {1}".format(r_actual, r_expected)
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    _handle_test_result(
        not (actual == expected), message, allow_raise, _is_in_test_case(),
    )


def expect_error(message, function, exception=Exception):
    passed = False
    try:
        function()
    except exception:
        passed = True
    except Exception:
        pass
    _handle_test_result(
        passed, message, False, _is_in_test_case(),
    )


def expect_no_error(message, function, exception=BaseException):
    passed = True
    try:
        function()
    except exception as e:
        passed = False
        message = "{}: {}".format(message or "Unexpected exception", repr(e))
    except Exception:
        pass
    _handle_test_result(
        passed, message, False, _is_in_test_case(),
    )


def pass_():
    if not _is_in_test_case():
        display("PASSED", "Test Passed")


def fail(message):
    if _is_in_test_case():
        raise AssertionError(message)
    else:
        display("FAILED", message)


def assert_approx_equals(
    actual, expected, margin=1e-9, message=None, allow_raise=False
):
    msg = "{0} should be close to {1} with absolute or relative margin of {2}"
    equals_msg = msg.format(repr(actual), repr(expected), repr(margin))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg
    div = max(abs(actual), abs(expected), 1)
    _handle_test_result(
        abs((actual - expected) / div) < margin,
        message,
        allow_raise,
        _is_in_test_case(),
    )


"""
Usage:
@describe('describe text')
def describe1():
    @it('it text')
    def it1():
        # some test cases...
"""


def _timed_block_factory(opening_text):
    from timeit import default_timer as timer
    from traceback import format_exception
    from sys import exc_info

    def _timed_block_decorator(s, before=None, after=None):
        display(opening_text, s)
        is_test_case = opening_text == "IT"

        def wrapper(func):
            if callable(before):
                before()
            time = timer()
            if is_test_case:
                func.test_case_func = True
            try:
                func()
                if is_test_case:
                    display("PASSED", "Test Passed")
            except AssertionError as e:
                display("FAILED", str(e))
            except Exception:
                fail("Unexpected exception raised")
                tb_str = "".join(format_exception(*exc_info()))
                display("ERROR", tb_str)
            display("COMPLETEDIN", "{:.2f}".format((timer() - time) * 1000))
            if callable(after):
                after()

        return wrapper

    return _timed_block_decorator


describe = _timed_block_factory("DESCRIBE")
it = _timed_block_factory("IT")


"""
Timeout utility
Usage:
@timeout(sec)
def some_tests():
    any code block...
Note: Timeout value can be a float.
"""


def timeout(sec):
    def wrapper(func):
        from multiprocessing import Process

        msg = "Should not throw any exceptions inside timeout"

        def wrapped():
            expect_no_error(msg, func)

        process = Process(target=wrapped)
        process.start()
        process.join(sec)
        if process.is_alive():
            fail("Exceeded time limit of {:.3f} seconds".format(sec))
            process.terminate()
            process.join()

    return wrapper
