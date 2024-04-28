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
