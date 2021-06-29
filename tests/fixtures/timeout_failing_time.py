import codewars_test as test


@test.describe("group 1")
def group_1():
    @test.timeout(0.01)
    def test_1():
        while True:
            pass
        test.pass_()
