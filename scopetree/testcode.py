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


def complex_function(x):
    y = 0
    z = []
    for i in range(10):
        if x % 2 == 0:
            y += i * 2
            z.append(y)
        else:
            y -= i
            z.append(-y)
        if y > 20:
            x += 1
        elif y < -10:
            x -= 1
        else:
            x *= 2
    for j in z:
        if j % 3 == 0:
            y += j // 3
        elif j % 5 == 0:
            y -= j // 5
        else:
            y += j % 7
    z = [a * 2 if a % 2 == 0 else a + 3 for a in z]
    if sum(z) > 100:
        x, y = y, x
    elif sum(z) < 0:
        x = -x
    else:
        y = -y
    while x > 0:
        if x % 2 == 0:
            x //= 2
        else:
            x -= 1
        y += 1
        if y % 10 == 0:
            break
    for k in range(5):
        z.append((x + y + k) % 7)
    if len(z) > 20:
        z = z[:20]
    return x, y, z
