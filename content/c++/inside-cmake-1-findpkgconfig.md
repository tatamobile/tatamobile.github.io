Title: 深入理解CMake（一）: FindPkgConfig
Date: 2022-05-05 15:17:53
Modified: 2024-05-05 15:17:53
Category: C++
Tags: CMake, C++
Slug: inside-cmake-1-findpkgconfig
Figure: cmake.png

## 缘起
在某些FindXXX.cmake模块中经常出现下面这两条命令：
```CMake
find_package(PkgConfig QUIET)
pkg_check_modules(PC_GLIB2 QUIET glib-2.0)
```
主要在一些第三方库没有提供CMake模块，只提供了pkg-config的配置，需要开发者自己开发CMake模块。
本文详细介绍这两条命令的含义。

## 搜索pkg-config

```CMake
cmake_minimum_required(3.18)

project(proj1)

find_package(PkgConfig QUIET)
message(STATUS "PKG_CONFIG_FOUND:${PKG_CONFIG_FOUND}")
message(STATUS "PKG_CONFIG_VERSION_STRING:${PKG_CONFIG_VERSION_STRING}")
message(STATUS "PKG_CONFIG_EXECUTABLE:${PKG_CONFIG_EXECUTABLE}")
message(STATUS "PKG_CONFIG_ARGN:${PKG_CONFIG_ARGN}")
```

输出
```bash
-- PKG_CONFIG_FOUND:TRUE
-- PKG_CONFIG_VERSION_STRING:0.29.2
-- PKG_CONFIG_EXECUTABLE:/usr/bin/pkg-config
-- PKG_CONFIG_ARGN:
```

find_package(PkgConfig) 找到CMake模块：
/usr/share/cmake-3.18/Modules/FindPkgConfig.cmake 并执行。
该模块主要搜索pkg-config可执行程序的位置，并定义了三个宏：
- pkg_get_variable
- pkg_check_modules
- pkg_search_module

## 宏pkg_check_modules
使用pkg_check_modules查找一个模块

```CMake
pkg_check_modules(PC_GLIB2 QUIET glib-2.0)
message(STATUS "PC_GLIB2_FOUND:${PC_GLIB2_FOUND}")
message(STATUS "PC_GLIB2_LIBRARIES:${PC_GLIB2_LIBRARIES}")
message(STATUS "PC_GLIB2_LINK_LIBRARIES:${PC_GLIB2_LINK_LIBRARIES}")
message(STATUS "PC_GLIB2_LIBRARY_DIRS:${PC_GLIB2_LIBRARY_DIRS}")
message(STATUS "PC_GLIB2_LDFLAGS:${PC_GLIB2_LDFLAGS}")
message(STATUS "PC_GLIB2_LDFLAGS_OTHER:${PC_GLIB2_LDFLAGS_OTHER}")
message(STATUS "PC_GLIB2_INCLUDE_DIRS:${PC_GLIB2_INCLUDE_DIRS}")
message(STATUS "PC_GLIB2_CFLAGS:${PC_GLIB2_CFLAGS}")
message(STATUS "PC_GLIB2_CFLAGS_OTHER:${PC_GLIB2_CFLAGS_OTHER}")
message(STATUS "PC_GLIB2_INCLUDEDIR:${PC_GLIB2_INCLUDEDIR}")
message(STATUS "PC_GLIB2_LIBDIR:${PC_GLIB2_LIBDIR}")
```

输出
```bash
-- PC_GLIB2_FOUND:1
-- PC_GLIB2_LIBRARIES:glib-2.0
-- PC_GLIB2_LINK_LIBRARIES:/usr/lib/x86_64-linux-gnu/libglib-2.0.so
-- PC_GLIB2_LIBRARY_DIRS:
-- PC_GLIB2_LDFLAGS:-lglib-2.0
-- PC_GLIB2_LDFLAGS_OTHER:
-- PC_GLIB2_INCLUDE_DIRS:/usr/include/glib-2.0;/usr/lib/x86_64-linux-gnu/glib-2.0/include
-- PC_GLIB2_CFLAGS:-I/usr/include/glib-2.0;-I/usr/lib/x86_64-linux-gnu/glib-2.0/include
-- PC_GLIB2_CFLAGS_OTHER:
-- PC_GLIB2_INCLUDEDIR:/usr/include
-- PC_GLIB2_LIBDIR:/usr/lib/x86_64-linux-gnu
```

pkg-config 解析相应的pc文件：/usr/lib/x86_64-linux-gnu/pkgconfig/glib-2.0.pc
```
prefix=/usr
libdir=${prefix}/lib/x86_64-linux-gnu
includedir=${prefix}/include

bindir=${prefix}/bin
glib_genmarshal=${bindir}/glib-genmarshal
gobject_query=${bindir}/gobject-query
glib_mkenums=${bindir}/glib-mkenums

Name: GLib
Description: C Utility Library
Version: 2.68.4
Requires.private: libpcre >=  8.31
Libs: -L${libdir} -lglib-2.0
Libs.private: -pthread -lm
Cflags: -I${includedir}/glib-2.0 -I${libdir}/glib-2.0/include
```

## 参考资料
- [FindPkgConfig](https://cmake.org/cmake/help/latest/module/FindPkgConfig.html)
