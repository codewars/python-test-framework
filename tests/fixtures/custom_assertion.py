import codewars_test as test


def custom_assert_equal(a, b):
    if a != b:
        raise AssertionError("Expected {} to equal {}".format(a, b))


@test.describe("group 1")
def group_1():
    @test.it("test 1")
    def test_1():
        custom_assert_equal(1, 1)

    @test.it("test 2")
    def test_2():
        custom_assert_equal(1, 2)

    @test.it("test 3")
    def test_3():
        assert 1 == 2, "using assert"
