Title: JNI 方法注册和签名
Date: 2021-12-21 11:35:42
Modified: 2022-12-21 11:35:42
Category: Reverse Engineering
Tags: java, jni
Slug: jni-function-name-override
Figure: java.png

## 缘起
最近分析一个Android平台上的so，发现JNI函数命名如下：

![JNI Function Name]({static}/images/jni_function_name.png)

函数名字和自己平时写代码不一样，故重新学习JNI方法的签名规则。

## 规则
### 工具使用
可以使用javah自动生成JNI函数签名，来探索函数命名规则。

```shell
javah -jni 包名.类名
```

一般类的普通函数

```java
{! android/com/example/Sample.java !}
```

执行命令 "javah -jni com.example.Sample" 后生成的c++文件

```c++
{! android/com_example_Sample.h !}
```

内部类的函数和重载函数

```java
{! android/com/example/Native.java !}
```

执行命令 "javah -jni com.example.Native" 后生成的c++文件

```c++
{! android/com_example_Native.h !}
{! android/com_example_Native_Stub.h !}
```

### 函数签名
一般函数的JNI接口函数命名：**Java_包名_类名_方法名**。
比如包com.example下的类Sample中的GetSample函数对应的JNI函数名 ： 
“*Java_com_example_Sample_GetSample*” 。

重载函数的JNI接口函数命名：**Java_包名_类名_方法名__参数签名**。
比如包名com.example下的类Native中的GetSample函数对应的JNI函数名： 
“*Java_com_example_Native_GetSample__ILjava_lang_String_2_3I*” 。

内部类Stub的JNI函数名：
“*Java_com_example_Native_00024Stub_GetSample*” 。

### 类型签名
|类型签名|Java类型|
| --- | --- |
|Z|boolean|
|B|byte|
|C|char|
|S|short|
|I|int|
|J|long|
|F|float|
|D|double|
|Lfully-qulitied-class;|全限定类|
|\[type|type\[\] 数组|
|(argtypes)rettype|方法类型|

### 转义字符
JNI在函数命名时采用名字扰乱方案，以保证所有的Unicode字符都能转换为有效的C函数名，所有的“/”,无论是包名中的还是全限定类名中的，均使用“_”代替，用_0,…,_9来代替转义字符。

|转义字符序列|表示|
| --- | --- |
|_0XXXX|Unicode字符XXXX|
|_1|字符“_”|
|_2|签名中的字符“；”|
|_3|签名中的字符“[”|

比如 "IdsSupplier_00024Stub" 中的"_00024" 表示字符"$" 。

## 参考资料
- [JNI 方法注册与签名](https://blog.csdn.net/superxlcr/article/details/72724096)
- [JNI使用规范详解](https://www.cnblogs.com/nuliniaoboke/archive/2012/10/31/2747715.html)

