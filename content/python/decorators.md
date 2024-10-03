Title: 高级Python编程：装饰器
Date: 2021-07-18 14:12:52
Modified: 2022-07-05 15:17:53
Category: Python
Tags: python, decorator
Slug: decorator
Figure: python.png

装饰器是一种设计模式，在Python中是一个非常有用的特性。可以在不修改函数、方法、类的情况下，修改（扩展）它们的行为。常见的装饰器如classmethod、staticmethod等，以@开始 加以使用，其实@只是Python提供的一个语法糖。

一个使用装饰器的例子：
```python
class A(object):
    @classmethod
    def count_all(cls):
        pass
```

## 函数基础知识
要理解装饰器原理，需理解Python中的函数特性。在 Python 中，万物皆对象，变量名只是关联（引用）这些对象的标识符。函数也不例外，在Python中也是对象。与C++、Java等不同,函数在Python中是一等公民（First-class Citizen）。具有以下特性：

- 函数可以像变量一样，赋值给另一个变量
- 函数可作为参数传递给另一个函数
- 函数可作为另一个函数的返回值
- 函数里可以内嵌函数，并且内嵌函数可访问外层函数的变量

### 函数赋值
函数就像字符串(string)、整数(int)、列表(list)等可赋值给另一个变量。
```python
def first(msg):
    print(msg)


first("Hello")

second = first
second("Hello")
del first
second("Hello")
first("Hello")
```

输出：
```shell
Hello
Hello
Hello
NameError: name 'first' is not defined
```
从输出结果可知，first 和 second 关联（引用）了同一个函数对象，当使用del删除first时，second仍可调用。

### 参数
```python
def inc(x):
    return x + 1


def dec(x):
    return x - 1


def operate(func, x):
    result = func(x)
    return result

print(operate(inc,3))
print(operate(dec,3))
```

输出：
```shell
4
2
```
### 返回值
```python
def is_called():
    def is_returned():
        print("Hello")
    return is_returned


new = is_called()

new()
```

输出：
```shell
Hello
```
### 嵌套函数
```python
def dog():
    height = 40
    
    def profile():
        print("I'm a dog and my height is {}.".format(height))
        
    return profile

if __name__ == "__main__":
    dog_profile = dog()
    dog_profile()
```

输出：
```shell
I'm a dog and my height is 40.
```

内嵌函数profile 可以访问外层函数dog的局部变量height。height是闭包中的捕获变量（captured variable），捕获变量相互独立，互不影响。这是Python语言支持的特性。

```python
def dog():
    height = 40
    
    def grow_up():
        nonlocal height
        height = height + 1
        
        def show_height():
            print("Thanks for making me growing up. I'm now {} meters !!!!".format(height))

        return show_height

    return grow_up


if __name__ == "__main__":
    dog_1_grow_up = dog()
    dog_1_grow_up()
    dog_1_grow_up()
    dog_1_grow_up()()
    # > Thanks for making me growing up. I'm now 43 meters !!!!

    dog_2_grow_up = dog()
    dog_2_grow_up()()
    # > Thanks for making me growing up. I'm now 41 meters !!!!
```

## 装饰器实现
装饰器本身是一个函数，它的参数是一个函数并且返回一个函数，我们又把返回一个函数的函数称做高阶函数，所以装饰器就是一个高阶函数。

### 简单装饰器
一个简单的装饰器：
```python
def make_pretty(func):
    def inner():
        print("I got decorated")
        func()
    return inner


def ordinary():
    print("I am ordinary")
```
在shell中运行如下代码：
```shell
>>> ordinary()
I am ordinary

>>> # let's decorate this ordinary function
>>> pretty = make_pretty(ordinary)
>>> pretty()
I got decorated
I am ordinary
```

make_pretty 就是一个装饰器，ordinary被装饰器装饰。

@是Python提供的一个语法糖，代码：
```python
@make_pretty
def ordinary():
    print("I am ordinary")
```
与之等价的代码：
```python
def ordinary():
    print("I am ordinary")
ordinary = make_pretty(ordinary)
```

问题：运行如下代码输出为："inner"
```python
print(ordinary.__name__)
```
使用装饰器之后，函数的名字等属性被改变了，可使用functools.wrap修正这个问题：
```python
from functools import wraps
def make_pretty(func):
    @wraps(func)
    def inner():
        print("I got decorated")
        func()
    return inner
```

### 被装饰函数带有参数
上面实现的装饰器只能装饰无参数的函数，为实现一个可装饰带任意参数的函数的装饰器，可使用\*args和\*\*kwargs。
```python
from functools import wraps
def make_pretty(func):
    @wraps(func)
    def inner(*args, **kwargs):
        print("I got decorated")
        return func(*args, **kwargs)
    return inner

@make_pretty
def ordinary():
    print("I am ordinary")

@make_pretty
def divide(a, b):
    print(a/b)
    return a / b
```
在shell中运行代码：
```shell
>>> print(divide.__name__)
divide
>>> print(divide(4,2))
I got decorated
2.0
2.0
```
## 装饰器如何带参数？
装饰器可通过参数控制其行为，比如实现一个限制调用次数的装饰器：
```python
from functools import wraps
def limit_query(limit):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if wrapper.count < limit:
                wrapper.count += 1
                return func(*args, **kwargs)
            else:
                print(f'No queries left. All {wrapper.count} queries used.')
                return "No queries left"
        wrapper.count = 0
        return wrapper
    return decorator

@limit_query(3)
def echo(value):
    return f"{value}"

if __name__ == "__main__":
    print(echo(1))
    print(echo(2))
    print(echo(3))
    print(echo(4))
```
输出：
```shell
1
2
3
No queries left. All 3 queries used.
No queries left
```

## 装饰器可以是类！
使用类也可以实现一个装饰器，通过实现__call__方法，是类符合可调用(callable)对象的要求即可。函数调用次数统计实现：
```python
import functools
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.num_calls = 0

    def __call__(self, *args, **kwargs):
        self.num_calls += 1
        print(f"Call {self.num_calls} of {self.func.__name__!r}")
        return self.func(*args, **kwargs)

@CountCalls
def say_whee():
    print("Whee!")

if __name__ == "__main__":
    print(say_whee.__name__)
    say_whee()
    say_whee()
```
输出：
```shell
say_whee
Call 1 of 'say_whee'
Whee!
Call 2 of 'say_whee'
Whee!
```

可这样理解：
```python
say_whee = CountCalls(say_whee) # 调用__init__方法 返回类的实例
say_whee() # 调用CountCalls的__call__方法
say_whee()
```

装饰器本身带参数的实现：
```python
class LimitQuery:
    def __init__(self, limit):
        print("[LimitQuery]__init__")
        self.limit = limit
        self.count = 0

    def __call__(self, func):
        print("[LimitQuery]__call__")
        @wraps(func)
        def wrapper(*args, **kwargs):
          if self.count < self.limit:
            self.count += 1
            return func(*args, **kwargs)
          else:
            print(f'No queries left. All {self.count} queries used.')
            return "No queries left"
        return wrapper

@LimitQuery(limit=3)
def get_coin_price(value):
    return f"{value}"

if __name__ == "__main__":
    print(get_coin_price(1))
    print(get_coin_price(2))
    print(get_coin_price(3))
    print(get_coin_price(4))
```
输出：
```python
[LimitQuery]__init__
[LimitQuery]__call__
1
2
3
No queries left. All 3 queries used.
No queries left
```

可这样理解：
```python
limit_query = LimitQuery(3) # 装饰器参数 __init__
get_coin_price = limit_query(get_coin_price) # 调用__call__函数，并返回wrapper
get_coin_price(1) # 调用wrapper 函数
```

## 装饰器的有序性
一个函数可被多个装饰器装饰，装饰顺序从下到上，即从靠近函数的装饰器开始。代码示例：
```python
def star(func):
    def inner(*args, **kwargs):
        print("*" * 30)
        func(*args, **kwargs)
        print("*" * 30)
    return inner


def percent(func):
    def inner(*args, **kwargs):
        print("%" * 30)
        func(*args, **kwargs)
        print("%" * 30)
    return inner


@star
@percent
def printer(msg):
    print(msg)


printer("Hello")
```

输出：
```shell
******************************
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
Hello
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
******************************
```

可以这样理解：
```python
star(percent(printer))("Hello")
```

## 实用的装饰器

### @call_counter

统计函数调用次数

```python
def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(*args, **kwargs)
    helper.calls = 0

    return helper
```

### @dataclass
```python
from dataclasses import dataclass
@dataclass
class InventoryItem:
    """Class for keeping track of an item in inventory."""
    name: str = ""
    unit_price: float = 1.0
    quantity_on_hand: int = 0

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand

if __name__ == "__main__":
    obj = InventoryItem("test",2.0, 3)
    print(obj.__dict__)
```

输出：

```shell
{'name': 'test', 'unit_price': 2.0, 'quantity_on_hand': 3}
```

dataclass 自动为类添加特殊函数和成员变量。

### @singleton

```python
def singleton(cls):
    instances = {}
    def wrapper(*args, **kwargs):
        if cls not in instances:
          instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return wrapper

@singleton
class A:
    def __init__(self, name):
        self.name = name

if __name__ == "__main__":
    a = A('hello')
    b = A('world')
    print(a)
    print(b)
    print(a.name)
    print(b.name)
    print(type(A))
```

输出：

```shell
<__main__.A object at 0x1020e2f70>
<__main__.A object at 0x1020e2f70>
hello
hello
<class 'function'>
```
从输出结果可以看到，a和b代表同一个对象（类A的实例），经过singleton装饰之后，类A的类型变成了函数。

## 参考资料
- [Python Advanced: Easy Introduction into Decorators and Decoration](https://www.python-course.eu/python3_decorators.php)
- [Python Decorators – How to Create and Use Decorators in Python With Examples](https://www.freecodecamp.org/news/python-decorators-explained-with-examples/)
- [7. Decorators &mdash; Python Tips 0.1 documentation](https://book.pythontips.com/en/latest/decorators.html)
- [Decorators in Python](https://www.datacamp.com/community/tutorials/decorators-python)
- [Python進階技巧 (3) — 神奇又美好的 Decorator ，嗷嗚！](https://medium.com/citycoddee/python%E9%80%B2%E9%9A%8E%E6%8A%80%E5%B7%A7-3-%E7%A5%9E%E5%A5%87%E5%8F%88%E7%BE%8E%E5%A5%BD%E7%9A%84-decorator-%E5%97%B7%E5%97%9A-6559edc87bc0)
- [10 Fabulous Python Decorators](https://towardsdatascience.com/10-fabulous-python-decorators-ab674a732871)
- [PEP 318 -- Decorators for Functions and Methods](https://www.python.org/dev/peps/pep-0318/)
- [Python Decorators](https://www.programiz.com/python-programming/decorator)
- [Decorators in Python](https://www.geeksforgeeks.org/decorators-in-python/)
- [Primer on Python Decorators](https://realpython.com/primer-on-python-decorators/)
