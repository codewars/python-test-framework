import codewars_test as test


@test.describe("group 1")
def group_1():
    # This outputs 2 PASSED
    @test.timeout(0.01)
    def test_1():
        test.assert_equals(1, 1)

