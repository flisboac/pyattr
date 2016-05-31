import sys
from pyattr import attr

sys.path.append('../')

# Examples below

@attr(locked = True)
class A(object):
    # This is just a helper object
    attr = attr()

    # A single method implementing both get and set
    @attr.accessor(value = 0)
    def x(self, v = None):
        if v is not None:
            self._x = v
            self._w = self._w + self._x * 2.0
        else:
            return self._x
    
    # Separate methods declared together, where the setter is not trivial
    @attr.setter(value = 0, readable = True)
    def y(self, v = None):
        if v is not None:
            self._y = v
            self._w = self._w + self._y / 2.0
        else:
            return self._y

    # Separate methods declared together, where the getter is not trivial
    @attr.getter(value = None, writable = True)
    def z(self):
        if self._z is None:
            return "oops"
        return self._z

    @attr.getter(value = 0)
    def w(self):
        """
        Accepts functions with empty bodies and with/without documentation.
        """ 
        pass

a = A()
print(a.x, A.x.raw_get(a))
print(a.y, A.y.raw_get(a))
print(a.z, A.z.raw_get(a))
print(a.w, A.w.raw_get(a))
a.x = 10
print(a.x)
a.x = None
print(a.x)
a.y = a.x * 65
print(a.y)
a.z = 101
print(a.z)
try:
    a.w = 2**10 + 0.5
except:
    print("can not do")
print(a.w)
try:
    a.b = "hello"
    print(a.b, "(lock not working)")
except:
    print("(lock is working)", sys.exc_info())
print("documentation for A.w", A.w.__doc__)