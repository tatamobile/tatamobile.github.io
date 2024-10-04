Title: 如何快速计算Android进程模块自身的加载基地址？
Date: 2022-02-10 22:21:12
Modified: 2023-02-10 22:21:12
Category: Reverse Engineering
Tags: arm, android
Slug: calcute-so-address
Figure: android.png


## 缘起
在Android安全开发中，经常需要获取进程内模块的加载基地址，获取方法一般有：

- 通过解析/proc/pid/maps文件
- 使用“dl_iterate_phdr”遍历

上述这些方法比较慢，用于一些检测任务是可以的，考虑这样一个场景：开发一个安全模块，这个模块是接管了进程的入口，在入口处需要基于安全模块自身的加载基地址做一些事情，如检验、取数据等。那么快速获取基地址就变得非常有必要了。

## 探索
在阅读android 8.1.0_r33中的linker源码时(bionic/linker/linker_main.cpp)，发现一段非常有意思的代码：
```c++
extern "C" ElfW(Addr) __linker_init(void* raw_args) {
  KernelArgumentBlock args(raw_args);

  // AT_BASE is set to 0 in the case when linker is run by iself
  // so in order to link the linker it needs to calcuate AT_BASE
  // using information at hand. The trick below takes advantage
  // of the fact that the value of linktime_addr before relocations
  // are run is an offset and this can be used to calculate AT_BASE.
  static uintptr_t linktime_addr = reinterpret_cast<uintptr_t>(&linktime_addr);
  ElfW(Addr) linker_addr = reinterpret_cast<uintptr_t>(&linktime_addr) - linktime_addr;
```
这两行神奇的代码可直接计算出linker的加载基地址，如果我们直接使用来计算自己开发的模块加载基地址，结果会是0。为什么呢？其实上面代码片段中的注释已经解释了原因，如果代码在未完成重定位之前就执行，就能计算出正确的基地址，但自己开发的模块执行这两句代码时候，已经完成了重定位，所以结果是0。
为了更好地理解重定位前后对计算结果的影响，需要考察这两句代码对于的汇编语言，这里假设linker加载基地址是0xea923000。
```armasm
0000f6c0 <__dl___linker_init>:
    f6c0:	e92d 4ff0 	stmdb	sp!, {r4, r5, r6, r7, r8, r9, sl, fp, lr}
    f6c4:	f5ad 5d95 	sub.w	sp, sp, #4768	; 0x12a0
    f6c8:	b081      	sub	sp, #4
    f6ca:	f850 1b04 	ldr.w	r1, [r0], #4
    f6ce:	e9cd 107b 	strd	r1, r0, [sp, #492]	; 0x1ec
    f6d2:	eb00 0081 	add.w	r0, r0, r1, lsl #2
    f6d6:	3004      	adds	r0, #4
    f6d8:	907d      	str	r0, [sp, #500]	; 0x1f4
    f6da:	f850 1b04 	ldr.w	r1, [r0], #4
    f6de:	2900      	cmp	r1, #0
    f6e0:	d1fb      	bne.n	f6da <__dl___linker_init+0x1a>
    ; 0x101b4地址的值为0x07BAC2 r1=0x07BAC2
    f6e2:	f8df 1ad0 	ldr.w	r1, [pc, #2768]	; 101b4 <__dl_$d.12> 
    f6e6:	907e      	str	r0, [sp, #504]	; 0x1f8
    f6e8:	2700      	movs	r7, #0
    ; pc=0xf6ea+0x4+0xea923000 r1 = r1 + pc = 0xEA9AE1B0
    f6ea:	4479      	add	r1, pc 
    ; 0xEA9AE1B0地址的值是0x8B1B0, r2 = 0x8B1B0 即linktime_addr的地址
    f6ec:	680a      	ldr	r2, [r1, #0]
    ; r4 = r1 - r2 = 0xEA9AE1B0 - 0x8B1B0 = 0xEA923000 即linker加载基地址
    f6ee:	1a8c      	subs	r4, r1, r2
    f6f0:	f850 1b04 	ldr.w	r1, [r0], #4
```
linktime_addr的偏移是0x8B1B0。在重定位之前，地址0x8B1B0的值也是0x8B1B0。

![Android 8.10 linker linktimeaddr]({static}/images/android_810_linker_linktimeaddr.png)

使用readelf工具考察linker中的重定位项：

```bash
$ arm-linux-androideabi-readelf -r linker
...
0008b198  00000017 R_ARM_RELATIVE
0008b1a4  00000017 R_ARM_RELATIVE
0008b1b0  00000017 R_ARM_RELATIVE
0008b1d8  00000017 R_ARM_RELATIVE
...
```
继续观察R_ARM_RELATIVE类型的重定位如何处理(6.0.1_r10/bionic/linker/linker.cpp)：
```cpp
      case R_GENERIC_RELATIVE:
        count_relocation(kRelocRelative);
        MARK(rel->r_offset);
        TRACE_TYPE(RELO, "RELO RELATIVE %16p <- %16p\n",
                   reinterpret_cast<void*>(reloc),
                   reinterpret_cast<void*>(load_bias + addend));
        *reinterpret_cast<ElfW(Addr)*>(reloc) = (load_bias + addend);
        break;
```
由于0x0008b1b0在重定位表里且类型为R_ARM_RELATIVE，完成重定位之后，地址0x8B1B0的值变为0xEA9AE1B0(0x8B1B0+0xEA923000)，与0xEA9AE1B0（linktime_addr变量在内存的地址）相减为0。这就是为什么在我们编写的模块里无法使用此种方法完成加载基地址的计算。

难道就这样结束了？不，虽然这种方法无法被直接使用，但这种思路值得借鉴，稍加改进之后，就可以运用到自己的方案中。改进方法：想办法去掉重定位项。

## 改进
为了避免生成重定位项，可通过汇编语言实现，下面是模块文件结构：
```bash
sample
    ├── jni
    │   ├── Android.mk
    │   ├── Application.mk
    │   ├── asm.h
    │   ├── begin.S
    │   ├── sample.c
```

文件Application.mk
```
APP_ABI := armeabi
APP_PLATFORM = android-9
```

文件Android.mk
```
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE    := sample
LOCAL_SRC_FILES := begin.S sample.c
LOCAL_LDLIBS += -llog
include $(BUILD_SHARED_LIBRARY)

```

文件asm.h
```c++
#ifndef SAMPLE_ASM_H
#define SAMPLE_ASM_H

#define __asm_custom_entry(f)
#define __asm_custom_end(f)
#define __asm_function_type %function
#define __asm_align 0

#define ENTRY(f) \
    .text; \
    .globl f; \
    .align __asm_align; \
    .type f, __asm_function_type; \
    f: \
    __asm_custom_entry(f); \
    .cfi_startproc;

#define END(f) \
    .cfi_endproc; \
    .size f, .-f; \
    __asm_custom_end(f)

#endif
```

文件begin.S
```armasm
#include "asm.h"

.type _linktime_addr,%object
    .global _linktime_addr
    .p2align 2
_linktime_addr:
    .long 0xf8c
    .size _linktime_addr, 4

ENTRY(_init)
    push {r0-r7, lr}
    sub sp,#12
    adr r0, _linktime_addr
    ldr r1, [r0]
    sub r0,r1
    bl sample_init
    add sp,#12
    pop {r0-r7, pc}
END(_init)
```

文件sample.c
```c++
#include <android/log.h>
#include <unistd.h>
#include <stdint.h>

extern void sample_init(uint32_t base){
    __android_log_print(ANDROID_LOG_INFO, "sample", "base:0x%08x", base);
}
```

反汇编构建出来的libsample.so中的_init函数：

![IDA Pro libsample self-base address]({static}/images/ida_libsample_self_base.png)

你可能已经注意到linktime_addr的初始值被设为0xf8c，这里只是方便演示，在笔者本机编译发现linktime_addr的地址是0xf8c。在实际运用中，你应该编写一个独立的脚本专门patch模块中linktime_addr的值，比如通过解析ELF文件，获得linktime_addr在文件的位置，并在此位置写入对应的值即可。

## 小结
本文通过研究linker中计算模块基地址的方法，找到了一种可快速计算模块自身的加载基地址。

## 参考资料
- [Android 8.1.0_r33](http://androidxref.com/8.1.0_r33)
- [Android 6.0.1_r10](http://androidxref.com/6.0.1_r10)