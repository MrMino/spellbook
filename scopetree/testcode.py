x = 0
y = 1
z = 2


class C1:
    def f1(self):
        x = 1

    def f1(self, a, b):
        x = 2

    def f2(self): ...


if x:

    class C2:
        def f1(self): ...

else:

    class C2:
        def f2(self): ...


def nest():
    def nest():
        def nest():
            def nest(): ...


def klas():
    class dew:
        pass


def comprehensions_and_generators():
    [x for x in x()]
    {k: v for k, v in x()}
    {i for i in x()}
    lambda y: 1 + y
    set(a for a in [1, 2, 3])

# Oh. My. God.
class CursedCode1:
    from inspect import isclass
    class PleaseStop(*[cls for cls in globals().values() if isclass(cls)]):
        pass
    print(PleaseStop.__mro__)


class CursedCode2:
    def what_the() -> lambda: "heck":
        pass


# Confusion.
# These lambdas switch places in the symtable scope list
class CursedCode3:
    @lambda func: None
    def same_lineno() -> lambda: None:
        pass


class CursedCode4:
    @lambda cls: None
    class Decorated((lambda: object)(), (lambda: C1)()):
        pass


class CursedCode5:
    class WhichLambdaIsWhich:
        @lambda d: None
        def confusing(arg=lambda x: None) -> lambda y: None:
            pass
