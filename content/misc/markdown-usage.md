Title: Markdown 在 Pelican上的的支持情况
Date: 2021-03-13 09:09:19
Modified: 2022-05-05 15:17:53
Category: Misc
Tags: markdown
Slug: markdown-usage
Figure: pelican.svg

## 代码
### C++ 代码
```cpp
#include <iostream>
using namespace std;
int main(int argc,char* argv[]){
  cout << "Hello,World" << endl;
  return 0;
}
```
### Python 代码
```python
# -*- coding:utf-8 -*-
import sys,os
if __name__ == '__main__':
  print('Hello,World')
```

## 引用代码
### 嵌入全文
```c++
{! sample/hello.cpp !}
```

### 嵌入某一行
{% include_code lang:cpp from:6 to:10 sample/hello.cpp %}

## 数学公式
测试：$c = \pm\sqrt{a^2 + b^2}$

测试：$\frac{1}{x^2-1}$

测试：$(E=mc^2)$

测试：
\begin{equation} \label{eq1}
e=mc^2
\end{equation}

多行公式：
$$
\begin{equation} \label{eq2}
\begin{aligned}
a &= b + c \\
  &= d + e + f + g \\
  &= h + i
\end{aligned}
\end{equation}
$$


行内显示：$f(x)=ax+b$

行间显示：
$$
f(x)=ax+b
$$

### 上标与下标
使用 ^ 表示上标，使用 _ 表示下标，如果上下标的内容多于一个字符，可以使用大括号括起来：
```
f(x) = a_1x^n + a_2x^{n-1} + a_3x^{n-2}
```
显示效果：$f(x) = a_1x^n + a_2x^{n-1} + a_3x^{n-2}$

如果左右两边都有上下标可以使用 \sideset 语法：
```
\sideset{^n_k}{^x_y}a
```
显示效果：$\sideset{^n_k}{^x_y}a$

### 括号
在 markdown 语法中，, $, {, }, _都是有特殊含义的，所以需要加\转义。小括号与方括号可以使用原始的() [] 大括号需要转义\也可以使用\lbrace和 \rbrace : 
```latex
\{x*y\}
\lbrace x*y \rbrace
```
显示效果：$\lbrace x*y \rbrace$

原始符号不会随着公式大小自动缩放，需要使用 \left 和 \right 来实现自动缩放：
```latex
\left \lbrace \sum_{i=0}^n i^3 = \frac{(n^2+n)(n+6)}{9} \right \rbrace
```
效果：$\left \lbrace \sum_{i=0}^n i^3 = \frac{(n^2+n)(n+6)}{9} \right \rbrace$

不使用\left 和 \right的效果：
```latex
 \lbrace \sum_{i=0}^n i^3 = \frac{(n^2+n)(n+6)}{9}  \rbrace
```
$$ \lbrace \sum_{i=0}^n i^3 = \frac{(n^2+n)(n+6)}{9}  \rbrace $$

### 分数与开方
可以使用\frac 或者 \over 实现分数的显示：
```latex
\frac xy
x+3 \over y+5
```
分别显示为：$\frac xy$ 和 $x+3 \over y+5$

开方使用\sqrt:
```latex
 \sqrt{x^5} 
 \sqrt[3]{\frac xy} 
```
分别显示为：$\sqrt{x^5}$ 和 $\sqrt[3]{\frac xy}$

### 求和与积分
求和使用\sum,可加上下标，积分使用\int可加上下限，双重积分用\iint:
```latex
 \sum_{i=0}^n 
 \int_1^\infty 
 \iint_1^\infty 
```
分别显示: $\sum_{i=0}^n$ 和 $\int_1^\infty$ 以及 $\iint_1^\infty$。

### 极限
极限使用\lim:
```latex
 \lim_{x \to 0} 
```
显示为：$\lim_{x \to 0}$

测试：$\lim_{n\rightarrow \infty}(1+2^n+3^n)^\frac{1}{x+\sin n}$

### 表格与矩阵
表格样式lcr表示居中，|加入一条竖线，\hline表示行间横线，列之间用&分隔，行之间用\分隔
```latex
\begin{array}{c|lcr}
n & \text{Left} & \text{Center} & \text{Right} \\\\
\hline
1 & 1.97 & 5 & 12 \\\\
2 & -11 & 19 & -80 \\\\
3 & 70 & 209 & 1+i \\\\
\end{array}
```

显示效果：
$$
\begin{array}{c|lcr}
n & \text{Left} & \text{Center} & \text{Right} \\\\
\hline
1 & 1.97 & 5 & 12 \\\\
2 & -11 & 19 & -80 \\\\
3 & 70 & 209 & 1+i \\\\
\end{array}
$$

矩阵显示和表格很相似
```latex
\left[
\begin{matrix}
V_A \\\\
V_B \\\\
V_C \\\\
\end{matrix}
\right] =
\left[
\begin{matrix}
1 & 0 & L \\\\
-cosψ & sinψ & L \\\\
-cosψ & -sinψ & L
\end{matrix}
\right]
\left[
\begin{matrix}
V_x \\\\
V_y \\\\
W \\\\
\end{matrix}
\right] 
```

显示效果：
$$
\left[
\begin{matrix}
V_A \\\\
V_B \\\\
V_C \\\\
\end{matrix}
\right] =
\left[
\begin{matrix}
1 & 0 & L \\\\
-cosψ & sinψ & L \\\\
-cosψ & -sinψ & L
\end{matrix}
\right]
\left[
\begin{matrix}
V_x \\\\
V_y \\\\
W \\\\
\end{matrix}
\right]
$$

## 图片
![test image]({static}/images/test.jpg)

## 引用文章
1. [深入理解CMake（一）: FindPkgConfig]({filename}/c++/inside-cmake-1-findpkgconfig.md)
2. [unicorn v1.0.3 Bug : IT 指令不能工作]({filename}/reverse_engineering/unicorn-v1-0-3-bug-it-instruction-not-work.md)

## 引用

> Do not just seek happiness for yourself. Seek happiness for all. Through kindness. Through mercy.
>
> - Authors: David Levithan, Wide Awake


> Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque hendrerit lacus ut purus iaculis 
> feugiat. Sed nec tempor elit, quis aliquam neque. Curabitur sed diam eget dolor fermentum semper at eu lorem.

