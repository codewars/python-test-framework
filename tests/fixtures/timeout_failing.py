import codewars_test as test


@test.describe("group 1")
def group_1():
    @test.timeout(0.01)
    def test_1():
        x = 0
        while x < 10 ** 9:
            x += 1
        test.pass_()
