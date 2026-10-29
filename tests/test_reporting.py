import unittest

from . import test_compatibility


class TestReporting(unittest.TestCase):
    records = []
    run_case = test_compatibility.TestCompatibility.run_case

    def test_multiline_unicode_and_protocol_text_are_escaped(self):
        output = self.run_case(r'''
            import codewars_test as test
            test.assert_equals('café\n<FAILED::>literal', 'café\nexpected', 'random seed 42')
        ''', failed=1)
        self.assertIn('random seed 42:', output)
        self.assertIn('<LOG:ESC:Expected>café<:LF:>expected', output)
        self.assertIn('<LOG:ESC:Actual>café<:LF:><FAILED::>literal', output)
        self.assertIn('<LOG:ESC:Location><string>:3', output)

    def test_large_values_have_bounded_output(self):
        output = self.run_case('''
            import codewars_test as test
            test.assert_equals('a' * 100000, 'b' * 100000)
        ''', failed=1)
        self.assertIn('[truncated]', output)
        self.assertLess(len(output), 8500)

    def test_unprintable_value_still_reports_original_failure(self):
        output = self.run_case('''
            import codewars_test as test
            class Unprintable:
                def __repr__(self):
                    raise ValueError('broken repr')
            test.assert_equals(Unprintable(), 42)
        ''', failed=1)
        self.assertIn('Unprintable: repr unavailable', output)

    def test_nested_containers_and_custom_message(self):
        output = self.run_case('''
            import codewars_test as test
            test.assert_equals({'a': [1, {'b': 2}]}, {'a': [1, {'b': 3}]}, 'case 7')
        ''', failed=1)
        self.assertIn('case 7:', output)
        self.assertIn("<LOG:ESC:Expected>{'a': [1, {'b': 3}]}", output)

    def test_bare_assertion_has_message_and_user_location(self):
        output = self.run_case('''
            import codewars_test as test
            @test.it('bare assert')
            def case():
                assert False
        ''', failed=1)
        self.assertIn('<FAILED::>Assertion failed', output)
        self.assertIn('<string>:5 in case', output)
        self.assertEqual(output.count('<COMPLETEDIN::>'), 1)

    def test_passing_bare_assertion_and_empty_group_add_no_success(self):
        self.run_case('''
            import codewars_test as test
            @test.it('bare assert')
            def case():
                assert True
            @test.it('empty')
            def empty():
                pass
        ''')

    def test_before_failure_skips_body_runs_cleanup_and_closes_group(self):
        output = self.run_case('''
            import codewars_test as test
            def before():
                raise ValueError('setup failed')
            @test.it('first', before=before, after=lambda: print('CLEANUP'))
            def first():
                print('UNREACHABLE')
            @test.it('next')
            def next_case():
                test.pass_()
        ''', passed=1, errors=1)
        self.assertIn('before hook', output)
        self.assertIn('setup failed', output)
        self.assertNotIn('UNREACHABLE', output)
        self.assertEqual(output.count('<COMPLETEDIN::>'), 2)
        self.assertLess(output.index('CLEANUP'), output.index('<COMPLETEDIN::>'))

    def test_cleanup_failure_does_not_hide_body_failure(self):
        output = self.run_case('''
            import codewars_test as test
            def after():
                raise ValueError('cleanup failed')
            @test.it('both', after=after)
            def case():
                test.assert_equals(1, 2, 'original failure', allow_raise=True)
        ''', failed=1, errors=1)
        self.assertIn('original failure', output)
        self.assertIn('cleanup failed', output)
        self.assertLess(output.index('after hook'), output.index('<COMPLETEDIN::>'))

    def test_before_allow_raise_reports_once_and_runs_cleanup(self):
        output = self.run_case('''
            import codewars_test as test
            def before():
                test.assert_equals(1, 2, allow_raise=True)
            @test.it('setup', before=before, after=lambda: print('CLEANUP'))
            def case():
                print('UNREACHABLE')
        ''', failed=1)
        self.assertIn('CLEANUP', output)
        self.assertNotIn('UNREACHABLE', output)

    def test_body_exception_and_cleanup_exception_are_both_visible(self):
        output = self.run_case('''
            import codewars_test as test
            def after():
                raise RuntimeError('cleanup error')
            @test.it('errors', after=after)
            def case():
                raise ValueError('body error')
        ''', failed=1, errors=2)
        self.assertIn('body error', output)
        self.assertIn('cleanup error', output)

    def test_approximate_and_negative_assertions_keep_counts(self):
        self.run_case('''
            import codewars_test as test
            test.assert_approx_equals(1, 1.0000000001)
            test.assert_approx_equals(1, 2)
            test.assert_not_equals(1, 2)
            test.assert_not_equals(1, 1)
        ''', passed=2, failed=2)
