from __future__ import print_function

import sys
import traceback


_VALUE_LIMIT = 2000


def _bounded(value):
    if len(value) > _VALUE_LIMIT:
        return value[:_VALUE_LIMIT] + ' ... [truncated]'
    return value


def _safe_repr(value):
    try:
        return _bounded(repr(value))
    except Exception:
        return '<{}: repr unavailable>'.format(type(value).__name__)


def _value_details(value):
    # Multiline strings are easier to compare as text. display() transports
    # newlines inside a single escaped log event, including protocol-like text.
    return _bounded(value) if isinstance(value, str) else _safe_repr(value)


def _location(tb=None):
    if tb is not None:
        frames = traceback.extract_tb(tb)
    else:
        frames = traceback.extract_stack()[:-1]
    for frame in reversed(frames):
        if frame.filename != __file__:
            return '{}:{} in {}'.format(frame.filename, frame.lineno, frame.name)
    return ''


def _failure(message, allow_raise=False, details=(), tb=None):
    display('FAILED', message)
    for label, value in details:
        display('LOG', value, label=label, mode='ESC')
    location = _location(tb)
    if location:
        display('LOG', location, label='Location', mode='ESC')
    if allow_raise:
        raise AssertException(message)


class AssertException(Exception):
    pass


def format_message(message):
    return message.replace("\n", "<:LF:>")


def display(type, message, label="", mode=""):
    print("\n<{0}:{1}:{2}>{3}".format(
        type.upper(), mode.upper(), label, format_message(message))
        , flush=True)


def expect(passed=None, message=None, allow_raise=False):
    if passed:
        display('PASSED', 'Test Passed')
    else:
        message = message or "Value is not what was expected"
        _failure(message, allow_raise)


def assert_equals(actual, expected, message=None, allow_raise=False):
    equals_msg = "{0} should equal {1}".format(_safe_repr(actual), _safe_repr(expected))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    if actual == expected:
        pass_()
    else:
        _failure(message, allow_raise, (
            ('Expected', _value_details(expected)), ('Actual', _value_details(actual))))


def assert_not_equals(actual, expected, message=None, allow_raise=False):
    r_actual, r_expected = _safe_repr(actual), _safe_repr(expected)
    equals_msg = "{0} should not equal {1}".format(r_actual, r_expected)
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg

    if not (actual == expected):
        pass_()
    else:
        _failure(message, allow_raise, (('Unexpected value', _value_details(actual)),))


def expect_error(message, function, exception=Exception):
    passed = False
    try:
        function()
    except exception:
        passed = True
    except Exception as e:
        message = "{}: {} should be {}".format(message or "Unexpected exception", repr(e), repr(exception))
    expect(passed, message)


def expect_no_error(message, function, exception=BaseException):
    try:
        function()
    except exception as e:
        fail("{}: {}".format(message or "Unexpected exception", repr(e)))
        return
    except:
        pass
    pass_()


def pass_(): expect(True)


def fail(message): expect(False, message)


def assert_approx_equals(
        actual, expected, margin=1e-9, message=None, allow_raise=False):
    msg = "{0} should be close to {1} with absolute or relative margin of {2}"
    equals_msg = msg.format(_safe_repr(actual), _safe_repr(expected), _safe_repr(margin))
    if message is None:
        message = equals_msg
    else:
        message += ": " + equals_msg
    div = max(abs(actual), abs(expected), 1)
    if abs((actual - expected) / div) < margin:
        pass_()
    else:
        _failure(message, allow_raise, (
            ('Expected', _value_details(expected)), ('Actual', _value_details(actual))))


'''
Usage:
@describe('describe text')
def describe1():
    @it('it text')
    def it1():
        # some test cases...
'''


def _timed_block_factory(opening_text):
    from timeit import default_timer as timer

    def run_part(func, hook=None):
        try:
            func()
        except AssertException:
            # The assertion already emitted its failure and location.
            pass
        except AssertionError as error:
            message = str(error) or 'Assertion failed'
            if hook:
                message = '{} hook: {}'.format(hook, message)
            _failure(message, tb=sys.exc_info()[2])
        except Exception:
            if hook:
                display('ERROR', '{} hook raised an exception'.format(hook))
                display('LOG', ''.join(traceback.format_exception(*sys.exc_info())),
                        label='Traceback', mode='ESC')
            else:
                fail('Unexpected exception raised')
                display('ERROR', ''.join(traceback.format_exception(*sys.exc_info())))
        else:
            return True
        return False

    def _timed_block_decorator(s, before=None, after=None):
        display(opening_text, s)

        def wrapper(func):
            time = timer()
            try:
                if not callable(before) or run_part(before, 'before'):
                    run_part(func)
            finally:
                try:
                    if callable(after):
                        run_part(after, 'after')
                finally:
                    # Cleanup belongs to the open group, including when setup
                    # fails. Closing last prevents errors leaking into siblings.
                    display('COMPLETEDIN', '{:.2f}'.format((timer() - time) * 1000))
        return wrapper
    return _timed_block_decorator


describe = _timed_block_factory('DESCRIBE')
it = _timed_block_factory('IT')


'''
Timeout utility
Usage:
@timeout(sec)
def some_tests():
    any code block...
Note: Timeout value can be a float.
'''


def timeout(sec):
    def wrapper(func):
        from multiprocessing import get_context
        import os
        import signal

        msg = 'Should not throw any exceptions inside timeout'
        process = None
        receiver = sender = None

        def wrapped():
            receiver.close()
            try:
                try:
                    func()
                except AssertException:
                    # Preserve fail-fast behavior without reporting twice.
                    pass
                except BaseException as error:
                    fail('{}: {}'.format(msg, repr(error)))
                else:
                    # Retain the existing extra pass for normal completion.
                    pass_()
                sender.send_bytes(b'completed')
            finally:
                sender.close()

        try:
            # Codewars runs on Linux. Existing kata use nested functions, which
            # cannot be pickled by Python 3.14's default forkserver context.
            # A local context leaves user code's start-method selection intact.
            context = get_context('fork')
            receiver, sender = context.Pipe(duplex=False)
            process = context.Process(target=wrapped)
            process.start()
            sender.close()
            process.join(sec)
            if process.is_alive():
                fail('Exceeded time limit of {:.3f} seconds'.format(sec))
            elif process.exitcode != 0:
                fail('Timeout process exited with code {}'.format(process.exitcode))
            else:
                completed = False
                if receiver.poll():
                    try:
                        completed = receiver.recv_bytes() == b'completed'
                    except EOFError:
                        pass
                if not completed:
                    # os._exit(0) is not proof that the test body finished.
                    fail('Timeout process exited before completing the test block')
        except Exception as error:
            fail('Unable to run timed tests: {}'.format(repr(error)))
        finally:
            if process is not None and process.pid is not None:
                if process.is_alive():
                    process.terminate()
                    process.join(1)
                    if process.is_alive():
                        # A test can install or inherit a SIGTERM handler.
                        try:
                            os.kill(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                process.join()
            if receiver is not None:
                receiver.close()
            if sender is not None:
                sender.close()
    return wrapper
