Title: 高级Python编程：元类
Date: 2021-07-26 18:28:29
Modified: 2022-07-26 18:28:29
Category: Python
Tags: python,metaclass
Slug: metaclass
Figure: python.png

在正式开始之前，需要明确几个概念的中文和英文对照：

- 类(Class)
- 类型(Type)
- 类的实例(Instance)：在有些地方类的实例也可以叫对象，为与Python这个语境区分，本文用实例代替。
- 对象(Object)：在Python里，万物皆对象，类，类型、类的实例、函数或者一个字符串都是对象。

## 什么是元类
在Python里，万物皆对象。整数、字符串、元组、字典和类等都是对象，每个对象都有相对应的类型，对象的类型决定了对象在内存中的存储方式。可以使用type
查询任意对象的类型。

```python
string = "example"
print(type(string)) # <class 'str'>
```

```python
num = 23
print("Type of num is:", type(num))

lst = [1, 2, 4]
print("Type of lst is:", type(lst))

name = "Atul"
print("Type of name is:", type(name))
```

输出：
```shell
Type of num is: <class 'int'>
Type of lst is: <class 'list'>
Type of name is: <class 'str'>
```

在Python中，每个类型(type)都有对应的类(Class)。比如一个整型变量对应的类型就是int类。但类本身也是一个对象，是另一种类的实例，我们叫做元类。

元类是什么？我们知道类是对象（instance of class）的模版，描述对象的生成方式。那么元类就是控制类的生成方式，可修改、扩展类的功能和属性。
类的默认元类是什么？
```python
class a:
    pass

print(type(a)) # <class 'type'>
```
说明类的默认元类是type。
![Python:Object-Class-Metaclass]({static}/images/python_object_class_metaclass.jpeg)

## type的其他功能

type 经常用来查询一个对象的类型是什么。但也可以用来动态创建类（不通过class关键字来创建）。
```shell
>>> hello = type('hello', (), {})
>>> print(hello)
<class '__main__.hello'>
>>> print(hello())
<__main__.hello object at 0x1098f4610>
>>> hello = type('hello', (), {'world' : True})
>>> print(hello)
<class '__main__.hello'>
>>> print(hello.__dict__)
{'world': True, '__module__': '__main__', '__dict__': <attribute '__dict__' of 'hello' objects>, '__weakref__': <attribute '__weakref__' of 'hello' objects>, '__doc__': None}
```

type原型：type(name, superclass, attrs)

## 元类的应用
### 检查多重继承
创建一个元类，检查如果一个类继承了多个类，就抛出异常。
```python
# our metaclass
class MultiBases(type):
    # overriding __new__ method
    def __new__(cls, clsname, bases, clsdict):
        # if no of base classes is greater than 1
        # raise error
        if len(bases)>1:
            raise TypeError("Inherited multiple base classes!!!")
         
        # else execute __new__ method of super class, ie.
        # call __init__ of type class
        return super().__new__(cls, clsname, bases, clsdict)
 
# metaclass can be specified by 'metaclass' keyword argument
# now MultiBase class is used for creating classes
# this will be propagated to all subclasses of Base
class Base(metaclass=MultiBases):
    pass
 
# no error is raised
class A(Base):
    pass
 
# no error is raised
class B(Base):
    pass
 
# This will raise an error!
class C(A, B):
    pass
```

输出：
```shell
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "<stdin>", line 8, in __new__
TypeError: Inherited multiple base classes!!!
```

### 增加调试功能
比如我们需要调试类的方法，在方法执行前，打印方法的名字。将装饰器和元类相结合，可以比较简洁地完成这个特性。
```python
from functools import wraps
 
def debug(func):
    '''decorator for debugging passed function'''
     
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("Full name of this method:", func.__qualname__)
        return func(*args, **kwargs)
    return wrapper
 
def debugmethods(cls):
    '''class decorator make use of debug decorator
       to debug class methods '''
     
    for key, val in vars(cls).items():
        if callable(val):
            setattr(cls, key, debug(val))
    return cls
 
class debugMeta(type):
    '''meta class which feed created class object
       to debugmethod to get debug functionality
       enabled objects'''
     
    def __new__(cls, clsname, bases, clsdict):
        obj = super().__new__(cls, clsname, bases, clsdict)
        obj = debugmethods(obj)
        return obj
     
# base class with metaclass 'debugMeta'
# now all the subclass of this
# will have debugging applied
class Base(metaclass=debugMeta):pass
 
# inheriting Base
class Calc(Base):
    def add(self, x, y):
        return x+y
     
# inheriting Calc
class Calc_adv(Calc):
    def mul(self, x, y):
        return x*y
 
# Now Calc_adv object showing
# debugging behaviour
mycal = Calc_adv()
print(mycal.mul(2, 3))
```

输出：
```shell
Full name of this method: Calc_adv.mul
6
```

### 打印类的基本信息
```python
import logging

logging.basicConfig(level=logging.INFO)


class LittleMeta(type):
    def __new__(metacls, cls, bases, classdict):
        logging.info(f"classname: {cls}")
        logging.info(f"baseclasses: {bases}")
        logging.info(f"classdict: {classdict}")

        return super().__new__(metacls, cls, bases, classdict)


class Point(metaclass=LittleMeta):
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Point({self.x}, {self.y})"


p = Point(5, 10)
print(p)
```

输出：
```shell
INFO:root:classname: Point
INFO:root:baseclasses: ()
INFO:root:attrs: {'__module__': '__main__', '__qualname__': 'Point', '__init__': <function Point.__init__ at 0x7f436c2db790>, '__repr__': <function Point.__repr__ at 0x7f436c2db4c0>}


Point(5, 10)
```

### 添加一个属性
```python
from collections import OrderedDict


class AttrsListMeta(type):
    @classmethod
    def __prepare__(metacls, cls, bases):
        return OrderedDict()

    def __new__(metacls, cls, bases, classdict, **kwargs):
        attrs_names = [k for k in classdict.keys()]
        attrs_names_ordered = sorted(attrs_names)
        classdict["__attrs_ordered__"] = attrs_names_ordered

        return super().__new__(metacls, cls, bases, classdict, **kwargs)


class A(metaclass=AttrsListMeta):
    def __init__(self, x, y):
        self.y = y
        self.x = x


a = A(1, 2)
print(a.__attrs_ordered__)
```

输出：
```shell
['__init__', '__module__', '__qualname__']
```

### 单例
```python
class Singleton(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super().__call__(*args, **kwargs)
        return cls._instance[cls]


class A(metaclass=Singleton):
    pass


a = A()
b = A()

a is b
```


输出：
```shell
True
```

### 创建一个Final类
```python
class TerminateMeta(type):
    def __new__(metacls, cls, bases, classdict):
        type_list = [type(base) for base in bases]

        for typ in type_list:
            if typ is metacls:
                raise RuntimeError(
                    f"Subclassing a class that has "
                    + f"{metacls.__name__} metaclass is prohibited"
                )
        return super().__new__(metacls, cls, bases, classdict)


class A(metaclass=TerminateMeta):
    pass


class B(A):
    pass


a = A()
```

输出：
```shell
---------------------------------------------------------------------------

RuntimeError                              Traceback (most recent call last)

<ipython-input-438-ccba42f1f95b> in <module>
        20
        21
---> 22 class B(A):
        23     pass
        24

...

RuntimeError: Subclassing a class that has TerminateMeta metaclass is prohibited
```

### 创建抽象基类

```python
from abc import ABC, abstractmethod


class ICalc(ABC):
    """Interface for a simple calculator."""

    @abstractmethod
    def add(self, a, b):
        pass

    @abstractmethod
    def sub(self, a, b):
        pass

    @abstractmethod
    def mul(self, a, b):
        pass

    @abstractmethod
    def div(self, a, b):
        pass


intrf = ICalc()
```

输出：
```shell
---------------------------------------------------------------------------

TypeError                                 Traceback (most recent call last)

<ipython-input-21-7be58e3a2a92> in <module>
        21
        22
---> 23 intrf = ICalc()


TypeError: Can't instantiate abstract class ICalc with abstract methods add, div, mul, sub
```


### 性能测试
```python
import time
from functools import wraps
from types import FunctionType, MethodType


def timefunc(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        ret = func(*args, **kwargs)
        end_time = time.time()
        run_time = end_time - start_time
        print(f"Executing {func.__qualname__} took {run_time} seconds.")
        return ret

    return wrapper


class TimerMeta(type):
    def __new__(metacls, cls, bases, classdict):
        new_cls = super().__new__(metacls, cls, bases, classdict)

        # key is attribute name and val is attribute value in attribute dict
        for key, val in classdict.items():
            if isinstance(val, FunctionType) or isinstance(val, MethodType):
                setattr(new_cls, key, timefunc(val))
        return new_cls


class Shouter(metaclass=TimerMeta):
    def __init__(self):
        pass

    def intro(self):
        print("I shout!")


s = Shouter()
s.intro()
```

输出：
```shell
Executing Shouter.__init__ took 1.1920928955078125e-06 seconds.
I shout!
Executing Shouter.intro took 6.747245788574219e-05 seconds.
```

### 异常处理
```python
from functools import wraps
from types import FunctionType, MethodType


def exc_handler(func):
    """Decorator for custom exception handling."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except:
            print(f"Exception Occured!")
            print(f"Method name: {func.__qualname__}")
            print(f"Args: {args}, Kwargs: {kwargs}")
            raise
        return ret

    return wrapper


class ExceptionMeta(type):
    def __new__(metacls, cls, bases, classdict):
        new_cls = super().__new__(metacls, cls, bases, classdict)

        # key is attribute name and val is attribute value in attribute dict
        for key, val in classdict.items():
            if isinstance(val, FunctionType) or isinstance(val, MethodType):
                setattr(new_cls, key, exc_handler(val))
        return new_cls


class Base(metaclass=ExceptionMeta):
    pass


class Calc(Base):
    def add(self, x, y):
        return x + y


class CalcAdv(Calc):
    def div(self, x, y):
        return x / y


mycal = CalcAdv()
print(mycal.div(2, 0))
```

输出：
```shell
Exception Occured!
Method name: CalcAdv.div
Args: (<__main__.CalcAdv object at 0x7febe692d1c0>, 2, 0), Kwargs: {}



---------------------------------------------------------------------------

ZeroDivisionError                         Traceback (most recent call last)

<ipython-input-467-accaebe919a8> in <module>
        43
        44 mycal = CalcAdv()
---> 45 print(mycal.div(2, 0))

...

ZeroDivisionError: division by zero
```





### 自动注册插件
```python
registry = {}


class RegisterMeta(type):
    def __new__(metacls, cls, bases, classdict):
        new_cls = super().__new__(metacls, cls, bases, classdict)
        registry[new_cls.__name__] = new_cls
        return new_cls


class A(metaclass=RegisterMeta):
    pass


class B(A):
    pass


class C(A):
    pass


class D(B):
    pass


b = B()
print(registry)
```

输出：
```shell
{'A': __main__.A, 'B': __main__.B, 'C': __main__.C, 'D': __main__.D}
```


### 元类 & 数据类
#### 创建多个数据类
```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(unsafe_hash=True, frozen=True)
class Event:
    created_at: datetime


@dataclass(unsafe_hash=True, frozen=True)
class InvoiceIssued(Event):
    invoice_uuid: int
    customer_uuid: int
    total_amount: float
    due_date: datetime


@dataclass(unsafe_hash=True, frozen=True)
class InvoiceOverdue(Event):
    invoice_uuid: int
    customer_uuid: int


inv = InvoiceIssued(
    **{
        "invoice_uuid": 22,
        "customer_uuid": 34,
        "total_amount": 100.0,
        "due_date": datetime(2020, 6, 19),
        "created_at": datetime.now(),
    }
)


print(inv)
```

输出：
```shell
InvoiceIssued(created_at=datetime.datetime(2020, 6, 20, 1, 3, 24, 967633), invoice_uuid=22, customer_uuid=34, total_amount=100.0, due_date=datetime.datetime(2020, 6, 19, 0, 0))
```

#### 运用元类避免多处使用数据类
```python
from dataclasses import dataclass
from datetime import datetime


class EventMeta(type):
    def __new__(metacls, cls, bases, classdict):
        """__new__ is a classmethod, even without @classmethod decorator

        Parameters
        ----------
        cls : str
            Name of the class being defined (Event in this example)
        bases : tuple
            Base classes of the constructed class, empty tuple in this case
        attrs : dict
            Dict containing methods and fields defined in the class
        """
        new_cls = super().__new__(metacls, cls, bases, classdict)

        return dataclass(unsafe_hash=True, frozen=True)(new_cls)


class Event(metaclass=EventMeta):
    created_at: datetime


class InvoiceIssued(Event):
    invoice_uuid: int
    customer_uuid: int
    total_amount: float
    due_date: datetime


class InvoiceOverdue(Event):
    invoice_uuid: int
    customer_uuid: int


inv = InvoiceIssued(
    **{
        "invoice_uuid": 22,
        "customer_uuid": 34,
        "total_amount": 100.0,
        "due_date": datetime(2020, 6, 19),
        "created_at": datetime.now(),
    }
)

print(inv)
```

输出：
```shell
InvoiceIssued(created_at=datetime.datetime(2020, 6, 24, 12, 57, 22, 543328), invoice_uuid=22, customer_uuid=34, total_amount=100.0, due_date=datetime.datetime(2020, 6, 19, 0, 0))
```


> Metaclasses are deeper magic that 99% of users should never worry about. If you wonder whether you need them, you don’t (the people who actually need them know with certainty that they need them, and don’t need an explanation about why). 
>
> Tim Peters

## 参考资料

- [Metaprogramming with Metaclasses in Python](https://www.geeksforgeeks.org/metaprogramming-metaclasses-python/)
- [Python Metaclasses](https://realpython.com/python-metaclasses/)
- [Metaprogramming in Python](https://developer.ibm.com/tutorials/ba-metaprogramming-python/)
- [Python Metaclasses and Metaprogramming](https://stackabuse.com/python-metaclasses-and-metaprogramming)
- [Metaprogramming](https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Metaprogramming.html)
- [Pythonic MetaProgramming With MetaClasses](https://towardsdatascience.com/pythonic-metaprogramming-with-metaclasses-19b0df1e1760)
- [Meta programming with Metaclasses in Python](https://www.tutorialspoint.com/meta-programming-with-metaclasses-in-python)
- [Complete Guide to Python Metaclasses](https://analyticsindiamag.com/complete-guide-to-python-metaclasses/)
- [Meta-Programming in Python](https://betterprogramming.pub/meta-programming-in-python-7fb94c8c7152)
- [Deciphering Python's Metaclasses](https://rednafi.github.io/digressions/python/2020/06/26/python-metaclasses.html)
- [Meta Programming in Python.](https://www.linkedin.com/pulse/meta-programming-python-vineet-singh?articleId=6621839938948300800)

