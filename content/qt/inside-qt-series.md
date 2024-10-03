Title: 深入理解Qt
Date: 2024-05-05 21:35:23
Modified: 2024-05-05 21:35:23
Category: Qt
Tags: Qt, C++
Slug: inside-qt-series
Figure: qt.png

## QObject


QObject类是Qt对象模型的核心，绝大部分的Qt类都是从这个类继承而来。这个模型的中心特征就是一个叫做信号和槽的机制来实现对象间的通讯，你可以把一个信号和另一个槽通过 ***connect*** 方法连接起来，并可以使用 ***disconnect*** 方法来断开这种连接，你还可以通过调用 ***blockSignal*** 这个方法来临时的阻塞信号。

QObject把它们组织在对象树中。当你创建一个QObject并使用其它对象作为父对象时，这个对象会自动添加到父对象的 ***children*** 列表中。父对象拥有这个对象。比如，它将在它的析构函数中自动删除它所有的子对象。你可以通过 ***findChild*** 或者 ***findChildren*** 函数来查找一个对象。

每个对象都有一个对象名称和类名称, 他们都可以通过相应的 ***metaObject*** 对象来获得。你还可以通过 ***inherits*** 方法来判断一个对象的类是不是从另一个类继承而来。

当对象被删除时，它发出 ***destroyed*** 信号。你可以捕获这个信号来避免对QObject的无效引用。

QObject 可以通过 ***event*** 接收事件并且过滤其它对象的事件。详细情况请参考 ***installEventFilter*** 和 ***eventFilter***。

对于每一个实现了信号、槽和属性的对象来说，Q_OBJECT 宏都是必须要加上的。QObject 实现了这么多功能，那么，它是如何做到的呢？让我们通过它的源码来解开这个秘密吧。

QObject 类的实现文件一共有四个:

- qobject.h，QObject类 的基本定义，也是我们一般定义一个类的头文件
- qobject.cpp，QObject类的实现代码基本上都在这个文件
- qobjectdefs.h，这个文件中最重要的东西就是定义了 QMetaObject 类，这个类是为了实现信号、槽和属性的核心部分。
- qobject_p.h，这个文件中的代码是辅助实现 QObject 类 的，这里面最重要的东西是定义了一个 QObjectPrivate 类来存储 QOjbect 对象的成员数据。

理解这个 QObjectPrivate 类 又是我们理解 Qt 核心源码的基础，这个对象包含了每一个 Qt 对象中的数据成员，好了，让我们首先从理解 QObject 的数据存储代码开始我们的 Qt 核心源码之旅。

## 对象数据存储（A）

我们知道，在C++中，几乎每一个类中都需要有一些类的成员变量，通常情况下的做法如下：

```c++
class Person
{
private:
    string mszName; // 姓名
    bool mbSex;    // 性别
    int mnAge;     // 年龄
};
```

就是在类定义的时候，直接把类成员变量定义在这里，甚至于，把这些成员变量的存取范围直接定义成是 public 的，您是不是也是这样做的呢？

在Qt中，却几乎都不是这样做的，那么，Qt是怎么做的呢？

几乎每一个C++的类中都会保存许多的数据，要想读懂别人写的C++代码，就一定需要知道每一个类的的数据是如何存储的，是什么含义，否则，我们不可能读懂别人的C++代码。在这里也就是说，要想读懂Qt的代码，第一步就必须先搞清楚Qt的类成员数据是如何保存的。

为了更容易理解Qt是如何定义类成员变量的，我们先说一下Qt 2.x 版本中的类成员变量定义方法，因为在 2.x 中的方法非常容易理解。然后在介绍 Qt 4.6 中的类成员变量定义方法。

Qt 2.x 中的方法

在定义类的时候(在.h文件中)，只包含有一个类成员变量，只是定义一个成员数据指针，然后由这个指针指向一个数据成员对象，这个数据成员对象包含所有这个类的成员数据，然后在类的实现文件(.cpp文件)中，定义这个私有数据成员对象。示例代码如下：

```c++
//————————————————————————————————————–
// File name:  person.h

struct PersonalDataPrivate; // 声明私有数据成员类型

class Person
{
public:

    Person ();   // constructor
    virtual ~Person ();  // destructor
    void setAge(const int);
    int getAge();

private:

    PersonalDataPrivate* d;
};

 

//————————————————————————————————————–
// File name:  person.cpp

struct PersonalDataPrivate  // 定义私有数据成员类型
{
    string mszName; // 姓名
    bool mbSex;    // 性别
    int mnAge;     // 年龄
};

// constructor
Person::Person ()
{
    d = new PersonalDataPrivate;
};

// destructor
Person::~Person ()
{
    delete d;
};

void Person::setAge(const int age)
{
    if (age != d->mnAge)
        d->mnAge = age;
}

int Person::getAge()
{
    return d->mnAge;
}
```

在最初学习Qt的时候，我也觉得这种方法很麻烦，但是随着使用的增多，我开始很喜欢这个方法了，而且，现在我写的代码，基本上都会用这种方法。具体说来，它有如下优点：

- 减少头文件的依赖性：把具体的数据成员都放到cpp文件中去，这样，在需要修改数据成员的时候，只需要改cpp文件而不需要头文件，这样就可以避免一次因为头文件的修改而导致所有包含了这个文件的文件全部重新编译一次，尤其是当这个头文件是非常底层的头文件和项目非常庞大的时候，优势明显。同时，也减少了这个头文件对其它头文件的依赖性。可以把只在数据成员中需要用到的在cpp文件中include一次就可以，在头文件中就可以尽可能的减少include语句
- 增强类的封装性：这种方法增强了类的封装性，无法再直接存取类成员变量，而必须写相应的 get/set 成员函数来做这些事情。关于这个问题，仁者见仁，智者见智，每个人都有不同的观点。有些人就是喜欢把类成员变量都定义成public的，在使用的时候方便。只是我个人不喜欢这种方法，当项目变得很大的时候，有非常多的人一起在做这个项目的时候，自己所写的代码处于底层有非常多的人需要使用(#include)的时候，这个方法的弊端就充分的体现出来了。

还有，我不喜欢 Qt 2.x 中把数据成员的变量名都定义成只有一个字母 ***d***，看起来很不直观，尤其是在search的时候，很不方便。但是，Qt源码中的确就是这么干的。

那么，在 Qt4.6 里面是如何实现的呢？

## 对象数据存储（B）

在 Qt 4.6 中，类成员变量定义方法的出发点没有变化，只是在具体的实现手段上发生了非常大的变化，下面具体来看。
在 Qt 4.6 中，使用了非常多的宏来做事，这凭空的增加了理解Qt源码的难度，不知道他们是不是从MFC学来的。就连在定义类成员数据变量这件事情上，也大量的使用了宏。
在这个版本中，类成员变量不再是给每一个类都定义一个私有的成员，而是把这一项common的工作放到了最基础的基类 ***QObject*** 中，然后定义了一些相关的方法来存取，好了，让我们进入具体的代码吧。

```c++
//————————————————————————————————————–
// file name: qobject.h

class QObjectData
{
public:
    virtual ~QObjectData() = 0;
    // 省略
};

class QObject
{
    Q_DECLARE_PRIVATE(QObject)

public:

    QObject(QObject *parent=0);

protected:

    QObject(QObjectPrivate &dd, QObject *parent = 0);
    QObjectData *d_ptr;
}
```

这些代码就是在 qobject.h 这个头文件中的。在 QObject class 的定义中，我们看到，数据员的定义为：QObjectData *d_ptr; 定义成 protected 类型的就是要让所有的派生类都可以存取这个变量，而在外部却不可以直接存取这个变量。而 QObjectData 的定义却放在了这个头文件中，其目的就是为了要所有从QObject继承出来的类的成员变量也都相应的要在QObjectData这个class继承出来。而纯虚的析构函数又决定了两件事：

- 这个class不能直接被实例化。换句话说就是，如果你写了这么一行代码，new QObjectData， 这行代码一定会出错，compile的时候是无法过关的。
- 当 delete 这个指针变量的时候，这个指针变量是指向的任意从QObjectData继承出来的对象的时候，这个对象都能被正确delete，而不会产生错误，诸如，内存泄漏之类的。

我们再来看看这个宏做了什么，Q_DECLARE_PRIVATE(QObject)

```c++
#define Q_DECLARE_PRIVATE(Class) \
    inline Class##Private* d_func() { return reinterpret_cast<Class##Private *>(d_ptr); } \
    inline const Class##Private* d_func() const { return reinterpret_cast<const Class##Private *>(d_ptr); } \
    friend class Class##Private;
```

这个宏主要是定义了两个重载的函数，d_func()，作用就是把在QObject这个class中定义的数据成员变量d_ptr安全的转换成为每一个具体的class的数据成员类型指针。我们看一下在QObject这个class中，这个宏展开之后的情况，就一目了然了。

Q_DECLARE_PRIVATE(QObject) 展开后，就是下面的代码：

```c++
inline QObjectPrivate* d_func() { return reinterpret_cast<QObjectPrivate *>(d_ptr); }
inline const QObjectPrivate* d_func() const
{ return reinterpret_cast<const QObjectPrivate *>(d_ptr); } \
friend class QObjectPrivate;
```

宏展开之后，新的问题又来了，这个QObjectPrivate是从哪里来的？在QObject这个class中，为什么不直接使用QObjectData来数据成员变量的类型？

还记得我们刚才说过吗，QObjectData这个class的析构函数的纯虚函数，这就说明这个class是不能实例化的，所以，QObject这个class的成员变量的实际类型，这是从QObjectData继承出来的，它就是QObjectPrivate !

这个 class 中保存了许多非常重要而且有趣的东西，其中包括 Qt 最核心的信号和槽的数据，属性数据，等等，我们将会在后面详细讲解，现在我们来看一下它的定义：

下面就是这个class的定义：

```c++
class QObjectPrivate : public QObjectData
{
    Q_DECLARE_PUBLIC(QObject)

public:

    QObjectPrivate(int version = QObjectPrivateVersion);
    virtual ~QObjectPrivate();
    // 省略
}
```

那么，这个 QObjectPrivate 和 QObject 是什么关系呢？他们是如何关联在一起的呢？

## 对象数据存储（C）

接上节，让我们来看看这个 QObjectPrivate 和 QObject 是如何关联在一起的。

```c++
//————————————————————————————————————–
// file name: qobject.cpp

QObject::QObject(QObject *parent)
    : d_ptr(new QObjectPrivate)
{
  // ………………………
}

QObject::QObject(QObjectPrivate &dd, QObject *parent)
    : d_ptr(&dd)
{
   // …………………
}
```

怎么样，是不是一目了然呀？从第一个构造函数可以很清楚的看出来，QObject class 中的 ***d_ptr*** 指针将指向一个 **QObjectPrivate** 的对象，而QObjectPrivate这个class是从QObjectData继承出来的。
这第二个构造函数干什么用的呢？从 QObject class 的定义中，我们可以看到，这第二个构造函数是被定义为 protected 类型的，这说明，这个构造函数只能被继承的class使用，而不能使用这个构造函数来直接构造一个QObject对象，也就是说，如果写一条下面的语句，编译的时候是会失败的。
```c++
new QObject(*new QObjectPrivate, NULL)
```

为了看的更清楚，我们以QWidget这个class为例说明。QWidget是QT中所有UI控件的基类，它直接从QObject继承而来，
```c++
class QWidget : public QObject, public QPaintDevice
{
    Q_OBJECT
    Q_DECLARE_PRIVATE(QWidget)
    // …………………
}
```

我们看一个这个class的构造函数的代码：
```c++
QWidget::QWidget(QWidget *parent, Qt::WindowFlags f)
    : QObject(*new QWidgetPrivate, 0), QPaintDevice()
{
    d_func()->init(parent, f);
}
```

非常清楚，它调用了基类QObject的保护类型的构造函数，并且以 **new QWidgetPrivate* 作为第一个参数传递进去。也就是说，基类(QObject)中的d_ptr指针将会指向一个QWidgetPrivate类型的对象。再看QWidgetPrivate这个class的定义：

```c++
class QWidgetPrivate : public QObjectPrivate
{
    Q_DECLARE_PUBLIC(QWidget)
    // …………………
}
```

好了，这就把所有的事情都串联起来了。

关于QWidget构造函数中的唯一的语句 d_func()->init(parent, f) 我们注意到在class的定义中有这么一句话： Q_DECLARE_PRIVATE(QWidget)
我们前面讲过这个宏，当把这个宏展开之后，就是这样的：

```c++
inline QWidgetPrivate* d_func() { return reinterpret_cast<QWidgetPrivate *>(d_ptr); }
inline const QWidgetPrivate* d_func() const
{ return reinterpret_cast<const QWidgetPrivate *>(d_ptr); } \
friend class QWidgetPrivate;
```

很清楚，它就是把QObject中定义的d_ptr指针转换为QWidgetPrivate类型的指针。

小结：
要理解Qt源码，就必须要知道Qt中每一个Object内部的数据是如何保存的，而Qt没有象我们平时写代码一样，把所有的变量直接定义在类中，所以，不搞清楚这个问题，我们就无法理解一个相应的类。其实，在Qt4.6中的类成员数据的保存方法在本质是与Qt2.x中的是一样的，就是在类中定义一个成员数据的指针，指向成员数据集合对象(这里是一个QObjectData或者是其派生类)。初始化这个成员变量的办法是定义一个保护类型的构造函数，然后在派生类的构造函数new 一个派生类的数据成员，并将这个新对象赋值给QObject的数据指针。在使用的时候，通过预先定义个宏里面的一个内联函数来把数据指针在安全类型转换，就可以使用了。

## 元对象系统

在使用 Qt 开发的过程中，大量的使用了 signal 和 slot. 比如，响应一个 button 的 click 事件，我们一般都写如下的代码：
```c++
class MyWindow : public QWidget
{
    Q_OBJECT
public:
    MyWindow(QWidget* parent) : QWidget(parent)
    {
      QPushButton* btnStart = new QPushButton(“start”, this);
      connect(btnStart, SIGNAL(clicked()), SLOT(slotStartClicked()));
    }

private slots:
    void slotStartClicked();
};

void MyWindow:: slotStartClicked()
{
    // 省略
}
```
在这段代码中，我们把 btnStart 这个 button 的clicked() 信号和 MyWindow 的 slotStartClicked() 这个槽相连接，当 btnStart 这个 button 被用户按下(click)的时候，就会发出一个 clicked() 的信号，然后，MyWindow:: slotStartClicked() 这个 slot 函数就会被调用用来响应 button 的 click 事件。这段代码是最为典型的 signal/slot 的应用实例，在实际的工作过程中，signal/slot 还有更为广泛的应用。准确的说，signal/slot 是QT提供的一种在对象间进行通讯的技术，那么，这个技术在QT 中是如何实现的呢？这就是 Qt 中的元对象系统(Meta Object System)的作用，为了更好的理解它，让我先来对它的功能做一个回顾，让我们一起来揭开它神秘的面纱。

Meta-Object System 的基本功能
Meta Object System 的设计基于以下几个基础设施：
-  QObject 类 ：作为每一个需要利用元对象系统的类的基类
- Q_OBJECT 宏 ：定义在每一个类的私有数据段，用来启用元对象功能，比如，动态属性，信号和槽
- 元对象编译器moc (the Meta Object Complier) ：moc 分析C＋＋源文件，如果它发现在一个头文件(header file)中包含Q_OBJECT 宏定义，然后动态的生成另外一个C++源文件，这个新的源文件包含 Q_OBJECT 的实现代码，这个新的 C++ 源文件也会被编译、链接到这个类的二进制代码中去，因为它也是这个类的完整的一部分。通常，这个新的C++ 源文件会在以前的C++ 源文件名前面加上 moc_ 作为新文件的文件名。其具体过程如下图所示：

除了提供在对象间进行通讯的机制外，元对象系统还包含以下几种功能：

- QObject::metaObject() 方法：它获得与一个类相关联的 meta-object
- QMetaObject::className() 方法：在运行期间返回一个对象的类名，它不需要本地C++编译器的RTTI(run-time type information)支持
- QObject::inherits() 方法：它用来判断生成一个对象类是不是从一个特定的类继承出来，当然，这必须是在QObject类的直接或者间接派生类当中
- QObject::tr() and QObject::trUtf8()：这两个方法为软件的国际化翻译字符串
- QObject::setProperty() and QObject::property()：这两个方法根据属性名动态的设置和获取属性值

除了以上这些功能外，它还使用qobject_cast()方法在QObject类之间提供动态转换，qobject_cast()方法的功能类似于标准C++的dynamic_cast()，但是qobject_cast()不需要RTTI的支持，在一个QObject类或者它的派生类中，我们可以不定义Q_OBJECT宏。如果我们在一个类中没有定义Q_OBJECT宏，那么在这里所提到的相应的功能在这个类中也不能使用，从meta-object的观点来说，一个没有定义Q_OBJECT宏的类与它最接近的那个祖先类是相同的，那就是所，QMetaObject::className() 方法所返回的名字并不是这个类的名字，而是与它最接近的那个祖先类的名字。所以，我们强烈建议，任何从QObject继承出来的类都定义Q_OBJECT 宏。

下一节，我们来了解另一个重要的工具：Meta-Object Compiler

## 元对象编译器moc

元对象编译器用来处理Qt 的C++扩展，moc 分析C＋＋源文件，如果它发现在一个头文件(header file)中包含Q_OBJECT 宏定义，然后动态的生成另外一个C++源文件，这个新的源文件包含 Q_OBJECT 的实现代码，这个新的 C++ 源文件也会被编译、链接到这个类的二进制代码中去，因为它也是这个类的完整的一部分。通常，这个新的C++ 源文件会在以前的C++ 源文件名前面加上 moc_ 作为新文件的文件名。

如果使用qmake工具来生成Makefile文件，所有需要使用moc的编译规则都会给自动的包含到Makefile文件中，所以对程序员来说不需要直接的使用moc

除了处理信号和槽之外，moc还处理属性信息，Q_PROPERTY()宏定义类的属性信息，而Q_ENUMS()宏则定义在一个类中的枚举类型列表。 Q_FLAGS()宏定义在一个类中的flag枚举类型列表，Q_CLASSINFO()宏则允许你在一个类的meta信息中插入name/value 对。

由moc所生成的文件必须被编译和链接，就象你自己写的另外一个C++文件一样，否则，在链接的过程中就会失败。
```c++
class MyClass : public QObject
{
    Q_OBJECT
    Q_PROPERTY(Priority priority READ priority WRITE setPriority)
    Q_ENUMS(Priority)
    Q_CLASSINFO("Author", "Oscar Peterson")
    Q_CLASSINFO("Status", "Active")

public:
    enum Priority { High, Low, VeryHigh, VeryLow };

    MyClass(QObject *parent = 0);
    virtual ~MyClass();

    void setPriority(Priority priority);
    Priority priority() const;
};
```

## 信号和槽
信号和槽是用来在对象间通讯的方法，当一个特定事件发生的时候，signal会被 emit 出来，slot 调用是用来响应相应的 signal 的。Qt 对象已经包含了许多预定义的 signal，但我们总是可以在派生类中添加新的 signal。Qt 对象中也已经包含了许多预定义的 slot，但我们可以在派生类中添加新的 slot 来处理我们感兴趣的 signal.

signal 和 slot 机制是类型安全的，signal 和 slot必须互相匹配(实际上，一个solt的参数可以比对应的signal的参数少，因为它可以忽略多余的参数)。signal 和 slot是松散的配对关系，发出signal的对象不关心是那个对象链接了这个signal，也不关心是那个或者有多少slot链接到了这个 signal。Qt的signal 和 slot机制保证了，如果一个signal和slot相链接，slot会在正确的时机被调用，并且是使用正确的参数。Signal和slot都可以携带任何数量和类型的参数，他们都是类型安全的。

所有从QObject直接或者间接继承出来的类都能包含信号和槽，当一个对象的状态发生变化的时候，信号就可以被emit出来，这可能是某个其它的对象所关心的。这个对象并不关心有那个对象或者多少个对象链接到这个信号了，这是真实的信息封装，它保证了这个对象可以作为一个软件组件来被使用。

槽(slot)是用来接收信号的，但同时他们也是一个普通的类成员函数，就象一个对象不关心有多少个槽链接到了它的某个信号，一个对象也不关心一个槽链接了多少个信号。这保证了用Qt创建的对象是一个真实的独立的软件组件。

一个信号可以链接到多个槽，一个槽也可以链接多个信号。同时，一个信号也可以链接到另外一个信号。所有使用了信号和槽的类都必须包含 Q_OBJECT 宏，而且这个类必须从QObject类派生(直接或者间接派生)出来，

当一个signal被emit出来的时候，链接到这个signal的slot会立刻被调用，就好像是一个函数调用一样。当这件事情发生的时候，signal和slot机制与GUI的事件循环完全没有关系，当所有链接到这个signal的slot执行完成之后，在 emit 代码行之后的代码会立刻被执行。当有多个slot链接到一个signal的时候，这些slot会一个接着一个的、以随机的顺序被执行。

Signal 代码会由 moc 自动生成，开发人员一定不能在自己的C++代码中实现它，并且，它永远都不能有返回值。Slot其实就是一个普通的类函数，并且可以被直接调用，唯一特殊的地方是它可以与signal相链接。C++的预处理器更改或者删除 signal, slot, emit 关键字，所以，对于C++编译器来说，它处理的是标准的C++源文件。

![Qt Signal Slot]({static}/images/qt_connect_signal_slot.gif)

如下图所示：假定 QPushButton 的 signal clicked() 已经和 QLineEdit 的 slot clear() 连接成功，那么当 QPushButton 的 clicked() signal 被 emit 出来的时候，QLineEdit 的 clear() slot 就会被调用。

![Qt Runtime]({static}/images/qt_runtime.gif)

## 元对象类概览

前面我们介绍了 Meta Object 的基本功能，和它支持的最重要的特性之一：Signal & Slot的基本功能。现在让我们来进入 Meta Object 的内部，看看它是如何支持这些能力的。

Meta Object 的所有数据和方法都封装在一个叫QMetaObject 的类中。它包含并且可以查询一个Qt类的 meta 信息，meta信息包含以下几种：
- 信号表(signal table)，其中有这个对应的 Qt 类的所有Signal的名字
- 槽表(slot table)，其中有这个对应的Qt类中的所有Slot的名字。
- 类信息表(class info table)，包含这个Qt类的类型信息
- 属性表(property table)，其中有这个对应的Qt类中的所有属性的名字。
- 指向parent meta object的指针(pointers to parent meta object)

请参考下图, Qt Meta Data Tables：

![Qt Meta Data Tables]({static}/images/qt_meta_object_data_table.gif)

QMetaOb ject 对象与 Qt 类之间的关系：

- 每一个 QMetaObject 对象包含了与之相对应的一个 Qt 类的元信息
- 每一个 Qt 类(QObject 以及它的派生类) 都有一个与之相关联的静态的(static) QMetaObject 对象（注：class的定义中必须有 Q_OBJECT 宏，否则就没有这个Meta Object）
- 每一个 QMetaObject 对象保存了与它相对应的 Qt 类的父类的 QMetaObject 对象的指针。   或者，我们可以这样说：“每一个QMetaObject对象都保存了一个其父亲(parent)的指针”.注意：严格来说，这种说法是不正确的，最起码是不严谨的。

请参考下图，Qt Meta Class 与 Qt class 之间的对应关系：

![Qt Meta Class & Class]({static}/images/qt_metaclass_class.gif)

Meta Object 的功能实现，Q_OBJECT这个宏立下了汗马功劳。首先，让我们来看看这个宏是如何定义的：

```c++
#define Q_OBJECT \
public: \
     Q_OBJECT_CHECK \
     static const QMetaObject staticMetaObject; \
     virtual const QMetaObject *metaObject() const; \
     virtual void *qt_metacast(const char *); \
     QT_TR_FUNCTIONS \
     virtual int qt_metacall(QMetaObject::Call, int, void **); \
private:
```

这里，我们先忽略Q_OBJECT_CHECK 和QT_TR_FUNCTIONS 这两个宏。
我们看到，首先定义了一个静态类型的类变量staticMetaObject，然后有一个获取这个对象指针的方法metaObject()。这里最重要的就是类变量staticMetaObject 的定义。这说明所有的 QObject 的对象都会共享这一个staticMetaObject 类变量，靠它来完成所有信号和槽的功能，所以我们就有必要来仔细的看看它是怎么回事了。


## QMetaObject类 数据成员

我们来看一下QMetaObject的定义，我们先看一下QMetaObject对象中包含的成员数据。
```c++
struct Q_CORE_EXPORT QMetaObject
{
    // ……
    struct { // private data
        const QMetaObject *superdata;
        const char *stringdata;
        const uint *data;
        const void *extradata;
    } d;
};
```
上面的代码就是QMetaObject类所定义的全部数据成员。就是这些成员记录了所有signal，slot，property，class information这么多的信息。下面让我们来逐一解释这些成员变量：

**const QMetaObject *superdata**：这个变量指向与之对应的QObject类的父类，或者是祖先类的QMetaObject对象。
如何理解这一句话呢？我们知道，每一个QMetaObject对象，一定有一个与之相对应的QObject类(或者由其直接或间接派生出的子类)，注意：这里是类，不是对象。
那么每一个QObject类(或其派生类)可能有一个父类，或者父类的父类，或者很多的继承层次之前的祖先类。或者没有父类(QObject)。那么 superdata 这个变量就是指向与其最接近的祖先类中的QMetaObject对象。对于QObject类QMetaObject对象来说，这是一个NULL指针，因为QObject没有父类。
下面，让我们来举例说明：
```c++
class Animal : public QObject
{
    Q_OBJECT
    //………….
};

class Cat : public Animal
{
    Q_OBJECT
    //………….
}
```
那么，Cat::staticMetaObject.d.superdata 这个指针变量指向的对象是 Animal::staticMetaObject
而 Animal::staticMetaObject.d.superdata 这个指针变量指向的对象是 QObject::staticMetaObject.
而 QObject::staticMetaObject.d.superdat 这个指针变量的值为 NULL。

但如果我们把上面class的定义修改为下面的定义，就不一样了：
```c++
class Animal : public QObject
{
    // Q_OBJECT，这个 class 不定义这个
    //………….
};

class Cat : public Animal
{
    Q_OBJECT
    //………….
}
```
那么，Cat::staticMetaObject.d.superdata 这个指针变量指向的对象是 QObject::staticMetaObject
因为 Animal::staticMetaObject 这个对象是不存在的。

**const char \*stringdata**:顾名思义，这是一个指向string data的指针。但它和我们平时所使用的一般的字符串指针却很不一样，我们平时使用的字符串指针只是指向一个字符串的指针，而这个指针却指向的是很多个字符串。那么它不就是字符串数组吗？哈哈，也不是。因为C++的字符串数组要求数组中的每一个字符串拥有相同的长度，这样才能组成一个数组。那它是不是一个字符串指针数组呢？也不是，那它到底是什么呢？让我们来看一看它的具体值，还是让我们以QObject这个class的QMetaObject为例来说明吧。

下面是QObject::staticMetaObject.d.stringdata指针所指向的多个字符串数组，其实它就是指向一个连续的内存区，而这个连续的内存区中保存了若干个字符串。
```c++
static const char qt_meta_stringdata_QObject[] =
{
    "QObject\0\0destroyed(QObject*)\0destroyed()\0"
    "deleteLater()\0_q_reregisterTimers(void*)\0"
    "QString\0objectName\0parent\0QObject(QObject*)\0"
    "QObject()\0"
};
```
这个字符串都是些什么内容呀？有，Class Name, Signal Name, Slot Name, Property Name。看到这些大家是不是觉得很熟悉呀，对啦，他们就是Meta System所支持的最核心的功能属性了。

既然他们都是不等长的字符串，那么Qt是如何来索引这些字符串，以便于在需要的时候能正确的找到他们呢？第三个成员正式登场了。

**const uint \*data**:这个指针本质上就是指向一个正整数数组，只不过在不同的object中数组的长度都不尽相同，这取决于与之相对应的class中定义了多少signal，slot，property。

这个整数数组的的值，有一部分指出了前一个变量(stringdata)中不同字符串的索引值，但是这里有一点需要注意的是，这里面的数值并不是直接标明了每一个字符串的索引值，这个数值还需要通过一个相应的算法计算之后，才能获得正确的字符串的索引值。

下面是QObject::staticMetaObject.d.data指针所指向的正整数数组的值。
```c++
static const uint qt_meta_data_QObject[] =
{
// content:
       2,       // revision
       0,       // classname
       0,    0, // classinfo
       4,   12, // methods
       1,   32, // properties
       0,    0, // enums/sets
       2,   35, // constructors

// signals: signature, parameters, type, tag, flags
       9,    8,    8,    8, 0×05,
      29,    8,    8,    8, 0×25,

// slots: signature, parameters, type, tag, flags
      41,    8,    8,    8, 0x0a,
      55,    8,    8,    8, 0×08,

// properties: name, type, flags
      90,   82, 0x0a095103,

// constructors: signature, parameters, type, tag, flags
     108,  101,    8,    8, 0x0e,
     126,    8,    8,    8, 0x2e,

       0        // eod
};
```

简单的说明一下，

第一个section，就是 //content 区域的整数值，这一块区域在每一个QMetaObject的实体对象中数量都是相同的，含义也相同，但具体的值就不同了。专门有一个struct定义了这个section，其含义在上面的注释中已经说的很清楚了。
```c++
struct QMetaObjectPrivate
{
    int revision;
    int className;
    int classInfoCount, classInfoData;
    int methodCount, methodData;
    int propertyCount, propertyData;
    int enumeratorCount, enumeratorData;
    int constructorCount, constructorData;
};
```
这个 struct 就是定义第一个secton的，和上面的数值对照一下，很清晰，是吧？

第二个section，以 // signals 开头的这段。这个section中的数值指明了QObject这个class包含了两个signal，
第三个section，以 // slots 开头的这段。这个section中的数值指明了QObject这个class包含了两个slot。
第四个section，以 // properties 开头的这段。这个section中的数值指明了QObject这个class包含有一个属性定义。
第五个section，以 // constructors 开头的这段，指明了QObject这个class有两个constructor。

**const void \*extradata**:这是一个指向QMetaObjectExtraData数据结构的指针，关于这个指针，这里先略过。

对于每一个具体的整数值与其所指向的实体数据之间的对应算法，实在是有点儿麻烦，这里就不讲解细节了，有兴趣的朋友自己去读一下源代码，一定会有很多发现。

## connect 幕后的故事

我们都知道，把一个signal和slot连接起来，需要使用QObject类的connect方法，它的作用就是把一个object的signal和另外一个object的slot连接起来，以达到对象间通讯的目的。connect 在幕后到底都做了些什么事情？为什么emit一个signal后，相应的slot都会被调用？好了，让我们来逐一解开其中的谜团。

SIGNAL 和 SLOT 宏定义

我们在调用connect方法的时候，一般都会这样写：
```c++
obj.connect(&obj, SIGNAL(destroyed()), &app, SLOT(aboutQt()));
```
我们看到，在这里signal和slot的名字都被包含在了两个大写的SIGNAL和SLOT中，这两个是什么呢？原来SIGNAL 和 SLOT 是Qt定义的两个宏。好了，让我们先来看看这两个宏都做了写什么事情：

这里是这两个宏的定义：
```c++
# define SLOT(a)      "1"#a
# define SIGNAL(a)   "2"#a
```

原来Qt把signal和slot都转化成了字符串，并且还在这个字符串的前面加上了附加的符号，signal前面加了’2’，slot前面加了’1’。也就是说，我们前面写了下面的connect调用，在经过moc编译器转换之后，就便成了：
```c++
obj.connect(&obj, "2destroyed()", &app, "1aboutQt()”));
```

当connect函数被调用了之后，都会去检查这两个参数是否是使用这两个宏正确的转换而来的，它检查的根据就是这两个前置数字，是否等于1或者是2，如果不是，connect函数当然就会失败啦！

然后，会去检查发送signal的对象是否有这个signal，方法就是查找这个对象的class所对应的staticMetaObject对象中所包含的d.stringdata所指向的字符串中是否包含这个signal的名字，在这个检查过程中，就会用到d.data所指向的那一串整数，通过这些整数值来计算每一个具体字符串的起始地址。同理，还会使用同样的方法去检查slot，看响应这个signal的对象是否包含有相应的slot。这两个检查的任何一个如果失败的话，connect函数就失败了，返回false.

前面的步骤都是在做一些必要的检查工作，下一步，就是要把发送signal的对象和响应signal的对象关联起来。在QObject的私有数据类QObjectPrivate中，有下面这些数据结构来保存这些信息：
```c++
class QObjectPrivate : public QObjectData
{
    struct Connection
    {
        QObject *receiver;
        int method;
        uint connectionType : 3; // 0 == auto, 1 == direct, 2 == queued, 4 == blocking
        QBasicAtomicPointer<int> argumentTypes;
    };

    typedef QList<Connection> ConnectionList;

    QObjectConnectionListVector *connectionLists;

    struct Sender
    {
        QObject *sender;
        int signal;
        int ref;
    };

    QList<Sender> senders;
}
```
在发送signal的对象中，每一个signal和slot的connection，都会创建一个QObjectPrivate::Connection对象，并且把这个对象保存到connectionList这个Vector里面去。

在响应signal的对象中，同样，也是每一个signal和slot的connection，都会一个创建一个Sender对象，并且把这个对象附加在Senders这个列表中。

以上就是connect的过程，其中，创建QObjectPrivate::Connection对象和Sender对象的过程有一点点复杂，需要仔细思考才可以，有兴趣的朋友可以去读一下源代码。

## emit 幕后的故事

当我们写下一下emit signal代码的时候，与这个signal相连接的slot就会被调用，那么这个调用是如何发生的呢？让我们来逐一解开其中的谜团。让我们来看一段例子代码：
```c++
class ZMytestObj : public QObject
{
    Q_OBJECT
signals:
    void sigMenuClicked();
    void sigBtnClicked();
};
```
MOC编译器在做完预处理之后的代码如下：
```c++
// SIGNAL 0
void ZMytestObj::sigMenuClicked()
{
    QMetaObject::activate(this, &staticMetaObject, 0, 0);
}

// SIGNAL 1
void ZMytestObj::sigBtnClicked()
{
    QMetaObject::activate(this, &staticMetaObject, 1, 0);
}
```
哈哈，看到了把，每一个signal都会被转换为一个与之相对应的成员函数。也就是说，当我们写下这样一行代码：
```c++
emit sigBtnClicked();
```
当程序运行到这里的时候，实际上就是调用了void ZMytestObj::sigBtnClicked() 这个函数。
大家注意比较这两个函数的函数体，void ZMytestObj::sigMenuClicked()  void ZMytestObj::sigBtnClicked()，它们唯一的区别就是调用 QMetaObject::activate 函数时给出的参数不同，一个是0，一个是1，它们的含义是什么呢？它们表示是这个类中的第几个signal被发送出来了，回头再去看头文件就会发现它们就是在这个类定义中，signal定义出现的顺序，这个参数可是非常重要的，它直接决定了进入这个函数体之后所发生的事情。
当执行流程进入到QMetaObject::activate函数中后，会先从connectionLists这个变量中取出与这个signal相对应的connection list，它根据的就是刚才所传入进来的signal index。这个connection list中保存了所有和这个signal相链接的slot的信息，每一对connection(即：signal 和 slot 的连接)是这个list中的一项。
在每个一具体的链接记录中，还保存了这个链接的类型，是自动链接类型，还是队列链接类型，或者是阻塞链接类型，不同的类型处理方法还不一样的。这里，我们就只说一下直接调用的类型。
对于直接链接的类型，先找到接收这个signal的对象的指针，然后是处理这个signal的slot的index，已经是否有需要处理的参数，然后就使用这些信息去调用receiver的qt_metcall 方法。
在qt_metcall方法中就简单了，根据slot的index，一个大switch语句，调用相应的slot函数就OK了。

## Qt对象之间的父子关系

很多C/C++初学者常犯的一个错误就是，使用malloc、new分配了一块内存却忘记释放，导致内存泄漏。Qt的对象模型提供了一种Qt对象之间的父子关系，当很多个对象都按一定次序建立起来这种父子关系的时候，就组织成了一颗树。当delete一个父对象的时候，Qt的对象模型机制保证了会自动的把它的所有子对象，以及孙对象，等等，全部delete，从而保证不会有内存泄漏的情况发生。
任何事情都有正反两面作用，这种机制看上去挺好，但是却会对很多Qt的初学者造成困扰，我经常给别人回答的问题是：
- new了一个Qt对象之后，在什么情况下应该delete它？
- Qt的析构函数是不是有bug？
- 为什么正常delete一个Qt对象却会产生segment fault？等等诸如此类的问题，本小节就是针对这个问题的详细解释。

在每一个Qt对象中，都有一个链表，这个链表保存有它所有子对象的指针。当创建一个新的Qt对象的时候，如果把另外一个Qt对象指定为这个对象的父对象，那么父对象就会在它的子对象链表中加入这个子对象的指针。另外，对于任意一个Qt对象而言，在其生命周期的任何时候，都还可以通过setParent函数重新设置它的父对象。当一个父对象在被delete的时候，它会自动的把它所有的子对象全部delete。当一个子对象在delete的时候，会把它自己从它的父对象的子对象链表中删除。
QWidget是所有在屏幕上显示出来的界面对象的基类，它扩展了Qt对象的父子关系。一个Widget对象也就自然的成为其父Widget对象的子Widget，并且显示在它的父Widget的坐标系统中。例如，一个对话框(dialog)上的按钮(button)应该是这个对话框的子Widget。
关于Qt对象的new和delete，下面我们举例说明。
例如，下面这一段代码是正确的：
```c++
int main()
{
  QObject* objParent = new QObject(NULL);
  QObject* objChild = new QObject(objParent);
  QObject* objChild2 = new QObject(objParent);
  delete objParent;
}
```

在上述代码片段中，objParent是objChild的父对象，在objParent对象中有一个子对象链表，这个链表中保存它所有子对象的指针，在这里，就是保存了objChild和objChild2的指针。在代码的结束部分，就只有delete了一个对象objParent，在objParent对象的析构函数会遍历它的子对象链表，并且把它所有的子对象(objChild和objChild2)一一删除。所以上面这段代码是安全的，不会造成内存泄漏。
如果我们把上面这段代码改成这样，也是正确的：
```c++
int main()
{
  QObject* objParent = new QObject(NULL);
  QObject* objChild = new QObject(objParent);
  QObject* objChild2 = new QObject(objParent);
  delete objChild;
  delete objParent;
}
```
在这段代码中，我们就只看一下和上一段代码不一样的地方，就是在delete objParent对象之前，先delete objChild对象。在delete objChild对象的时候，objChild对象会自动的把自己从objParent对象的子对象链表中删除，也就是说，在objChild对象被delete完成之后，objParent对象就只有一个子对象(objChild2)了。然后在delete objParent对象的时候，会自动把objChild2对象也delete。所以，这段代码也是安全的。
Qt的这种设计对某些调试工具来说却是不友好的，比如valgrind。比如上面这段代码，valgrind工具在分析代码的时候，就会认为objChild2对象没有被正确的delete，从而会报告说，这段代码存在内存泄漏。哈哈，我们知道，这个报告是不对的。
我们在看一看这一段代码：
```c++
int main()
{
  QWidget window;
  QPushButton quit("Exit", &window);
}
```
在这段代码中，我们创建了两个widget对象，第一个是window，第二个是quit，他们都是Qt对象，因为QPushButton是从QWidget派生出来的，而QWidget是从QObject派生出来的。这两个对象之间的关系是，window对象是quit对象的父对象，由于他们都会被分配在栈(stack)上面，那么quit对象是不是会被析构两次呢？我们知道，在一个函数体内部声明的变量，在这个函数退出的时候就会被析构，那么在这段代码中，window和quit两个对象在函数退出的时候析构函数都会被调用。那么，假设，如果是window的析构函数先被调用的话，它就会去delete quit对象；然后quit的析构函数再次被调用，程序就出错了。事实情况不是这样的，C++标准规定，本地对象的析构函数的调用顺序与他们的构造顺序相反。那么在这段代码中，这就是quit对象的析构函数一定会比window对象的析构函数先被调用，所以，在window对象析构的时候，quit对象已经不存在了，不会被析构两次。
如果我们把代码改成这个样子，就会出错了，对照前面的解释，请你自己来分析一下吧。
```c++
int main()
{
  QPushButton quit("Exit");
  QWidget window;
  quit.setParent(&window);
}
```
但是我们自己在写程序的时候，也必须重点注意一项，千万不要delete子对象两次，就像前面这段代码那样，程序肯定就crash了。
最后，让我们来结合Qt源码，来看看父子关系是如何实现的。
在“对象数据存储”，我们说到过，所有Qt对象的私有数据成员的基类是QObjectData类，这个类的定义如下

```c++
typedef QList<QObject*> QObjectList;
class QObjectData
{
public:
  QObject *parent;
  QObjectList children;
  // 忽略其它成员定义
};
```
我们可以看到，在这里定义了指向parent的指针，和保存子对象的列表。其实，把一个对象设置成另一个对象的父对象，无非就是在操作这两个数据。把子对象中的这个parent变量设置为指向其父对象；而在父对象的children列表中加入子对象的指针。当然，我这里说的非常简单，在实际的代码中复杂的多，包含有很多条件判断，有兴趣的朋友可以自己去读一下Qt的源代码。

## 参考资料

- [Inside Qt Series](http://www.qkevin.com)
- [Inside Qt Series 中文](https://blog.csdn.net/ilvu999/article/details/8048623)
