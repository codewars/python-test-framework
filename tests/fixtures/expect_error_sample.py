# https://www.codewars.com/kumite/5ab735bee7093b17b2000084?sel=5ab735bee7093b17b2000084
import codewars_test as test


def f0():
    pass


# BaseException >> Exception
def f1():
    raise Exception()


# BaseException >> Exception >> ArithmeticError >> ZeroDivisionError
def f2():
    return 1 // 0


# BaseException >> Exception >> LookupError >> KeyError
def f3():
    return {}[1]


excn = (
    "Exception",
    "ArithmeticError",
    "ZeroDivisionError",
    "LookupError",
    "KeyError",
    "OSError",
)
exc = (Exception, ArithmeticError, ZeroDivisionError, LookupError, KeyError, OSError)


@test.describe("expect_error, new version")
def d2():
    @test.it("f0 raises nothing")
    def i0():
        test.expect_error("f0 did not raise any exception", f0)
        for i in range(6):
            test.expect_error("f0 did not raise {}".format(excn[i]), f0, exc[i])

    @test.it("f1 raises Exception")
    def i1():
        test.expect_error("f1 did not raise Exception", f1)
        for i in range(6):
            test.expect_error("f1 did not raise {}".format(excn[i]), f1, exc[i])

    @test.it("f2 raises Exception >> ArithmeticError >> ZeroDivisionError")
    def i2():
        test.expect_error("f2 did not raise Exception", f2)
        for i in range(6):
            test.expect_error("f2 did not raise {}".format(excn[i]), f2, exc[i])

    @test.it("f3 raises Exception >> LookupError >> KeyError")
    def i3():
        test.expect_error("f3 did not raise Exception", f3)
        for i in range(6):
            test.expect_error("f3 did not raise {}".format(excn[i]), f3, exc[i])

