import codewars_test as test


@test.describe("group 1")
def group_1():
    @test.it("test 1")
    def test_1():
        test.assert_equals(1, 2)
