
class Calc:
    @staticmethod
    def distance_sqr(a, b):
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2


class Vec2Double:
    def __init__(self, x, y):
        self.x = x
        self.y = y


incx = Vec2Double(3, 2)
incy = Vec2Double(2, 3)
dest = Vec2Double(8, 5)
print(Calc.distance_sqr(incx, dest))
print(Calc.distance_sqr(incy, dest))
