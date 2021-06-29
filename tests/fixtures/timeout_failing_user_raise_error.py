import codewars_test as test


@test.describe("group 1")
def group_1():
    @test.timeout(0.2)
    def test_1():
        raise KeyError()
        test.pass_()
