Title: Android进程内存布局：主线程的栈顶是多少？
Date: 2022-02-09 17:10:09
Modified: 2023-02-09 17:10:09
Category: Reverse Engineering
Tags: arm, android
Slug: whats-stack-top-main-thread
Figure: android.png


## 缘起
最近开发一个基于unicron的模拟执行库，为了更好地模拟进程和线程的一些特性（比如线程本地存储），需要知道Android进程的实际内存布局，这里主要介绍线程栈的布局，非主线程可以通过分析pthread_create实现过程，了解到线程栈是通过mmap分配内存得到的，并且大小是1M。那主线程的栈位于哪里呢？一般进程内存布局如下图：

![Android process memory layout]({static}/images/android_process_mem_layout.png)

在32位系统里，4G虚拟内存空间内核占用1G，用户空间占用3G，推测主线程的栈顶就是0xc0000000。可以通过"/proc/pid/maps" 查看详细的内存分布：

![Android process memory maps]({static}/images/android-mem-layout-maps.png)

从图中可以看出主线程栈顶是0xbea5a000。

## 探索
"0xbea5a000" 是如何计算出来的？在linux中进程创建通常通过fork和execv两个系统调用配合完成。可通过阅读内核关于这两个系统调用的源码来理解栈的分配逻辑。这里不详述fork和execv的执行逻辑，与栈相关的代码在fs/binfmt.c里。

```c
#ifndef STACK_RND_MASK
#define STACK_RND_MASK (0x7ff >> (PAGE_SHIFT - 12))	/* 8MB of VA */
#endif

static unsigned long randomize_stack_top(unsigned long stack_top)
{
	unsigned int random_variable = 0;

	if ((current->flags & PF_RANDOMIZE) &&
		!(current->personality & ADDR_NO_RANDOMIZE)) {
		random_variable = get_random_int() & STACK_RND_MASK;
		random_variable <<= PAGE_SHIFT;
	}
#ifdef CONFIG_STACK_GROWSUP
	return PAGE_ALIGN(stack_top) + random_variable;
#else
	return PAGE_ALIGN(stack_top) - random_variable;
#endif
}
```

主线程的栈顶不是固定的，有一个随机范围 0 ~ 8M。那代码中的stack_top是多少呢？
函数 "randomize_stack_top" 在 "load_elf_binary"里被调用。
load_elf_binary 代码片段 ：

```c
/* Do this immediately, since STACK_TOP as used in setup_arg_pages
	   may depend on the personality.  */
	SET_PERSONALITY(loc->elf_ex);
	if (elf_read_implies_exec(loc->elf_ex, executable_stack))
		current->personality |= READ_IMPLIES_EXEC;

	if (!(current->personality & ADDR_NO_RANDOMIZE) && randomize_va_space)
		current->flags |= PF_RANDOMIZE;

	setup_new_exec(bprm);

	/* Do this so that we can load the interpreter, if need be.  We will
	   change some of these later */
	current->mm->free_area_cache = current->mm->mmap_base;
	current->mm->cached_hole_size = 0;
	retval = setup_arg_pages(bprm, randomize_stack_top(STACK_TOP),
				 executable_stack);
```

“STACK_TOP”是一个宏定义，详细定义在文件"arch/arm/include/asm/processor.h"里：

```c
#ifdef __KERNEL__
#define STACK_TOP	((current->personality & ADDR_LIMIT_32BIT) ? \
			 TASK_SIZE : TASK_SIZE_26)
#define STACK_TOP_MAX	TASK_SIZE
#endif
```

"TASK_SIZE"宏定义在"arch/arm/include/asm/memory.h"里：
```c
/*
 * PAGE_OFFSET - the virtual address of the start of the kernel image
 * TASK_SIZE - the maximum size of a user space task.
 * TASK_UNMAPPED_BASE - the lower boundary of the mmap VM area
 */
#define PAGE_OFFSET		UL(CONFIG_PAGE_OFFSET)
#define TASK_SIZE		(UL(CONFIG_PAGE_OFFSET) - UL(0x01000000))
#define TASK_UNMAPPED_BASE	(UL(CONFIG_PAGE_OFFSET) / 3)
```

从上述代码可知，一般情况下，PAGE_OFFSET 是内核空间的开始地址0xC0000000，TASK_SIZE(即STACK_TOP)是用户空间的结束地址，与PAGE_OFFSET有一个16M的间隔，即STACK_TOP的值是0xBF000000。从函数 "randomize_stack_top"可知，在STACK_TOP上还有0～8M的随机。由此可知，主线程栈顶的值在范围[0xBE800000,0xBF000000]内。文章开头提到的0xBEA5A000属于这个范围，多观察几台手机的主线程栈顶都在这个范围，符合预期。

到目前为止，我们已经解决了文章开头提到的问题，不过在探索过程中又出现了3个新问题：
- STACK_TOP和PAGE_OFFSET 之间间隔的16M地址空间有什么用处呢？
- 在观察进程内存情况时，处于内核空间的[0xFFFF0000,0xFFFF1000]这一块地址空间主要用来做什么呢？
- 在主线程栈顶附近的数据到底是什么？

后续三个小节继续探索这3个问题的答案。

## 内核模块（驱动）
STACK_TOP和PAGE_OFFSET 之间间隔的16M地址空间有什么用处呢？
参考文件"Documentation/arm/memory.txt"中的描述，动态加载的内核模块将被映射的到这个地址范围。
```
MODULES_VADDR	MODULES_END-1  Kernel module space
                               Kernel modules inserted via insmod are
                               placed here using dynamic mappings.
```

对memory.txt的理解是否正确，并未通过编写一个内核模块来验证。

## CPU 向量页
在观察进程内存情况时，处于内核空间的[0xFFFF0000,0xFFFF1000]这一块地址空间主要用来做什么呢？
参考文件"Documentation/arm/memory.txt"中的描述。
```
ffff0000    ffff0fff    CPU vector page.
                        The CPU vectors are mapped here if the
                        CPU supports vector relocation (control
                        register V bit.)
```
在ARM架构下，这块空间主要用于存放异常处理相关代码，异常处理细节不在这里讨论。其实这块空间除了用于异常处理之外，还有几个特殊的地址。
在文件“Documentation/arm/kernel_user_helpers.txt”描述了几个特殊的地址：

- 0xffff0fc0 存放了"__kuser_cmpxchg"的指令
- 0xffff0fa0 存放了“__kuser_memory_barrier”的指令

在这里特别说明这两个地址，是因为开发模拟执行库时，某些库函数会直接跳转到这些地址开始执行，用于实现原子操作。

![IDA Pro sync fetch add]({static}/images/ida_sync_fetch_and_add_4.png)

## 栈中的数据
在主线程栈顶附近的数据到底是什么？
为了可以解析栈顶附近的数据，需要找到一个进程的入口在哪里，在Android系统中，每个进程的入口都在linker里，即内核完成进程资源准备后，将控制权移交给用户空间时，第一条执行的指令都是一样的：
代码文件：bionic/linker/arch/arm/begin.S

```armasm
ENTRY(_start)
  mov r0, sp
  bl __linker_init

  /* linker init returns the _entry address in the main image */
  mov pc, r0
END(_start)
```

函数“__linker_init”的代码片段：

```c++
extern "C" ElfW(Addr) __linker_init(void* raw_args) {
  KernelArgumentBlock args(raw_args);

  ElfW(Addr) linker_addr = args.getauxval(AT_BASE);
  ElfW(Addr) entry_point = args.getauxval(AT_ENTRY);
  ElfW(Ehdr)* elf_hdr = reinterpret_cast<ElfW(Ehdr)*>(linker_addr);
  ElfW(Phdr)* phdr = reinterpret_cast<ElfW(Phdr)*>(linker_addr + elf_hdr->e_phoff);
  // ...
}
```

raw_args 就是栈的位置，解析栈数据应该在KernelArgumentBlock里。
类“KernelArgumentBlock”的代码片段：

```c++
class KernelArgumentBlock {
 public:
  KernelArgumentBlock(void* raw_args) {
    uintptr_t* args = reinterpret_cast<uintptr_t*>(raw_args);
    argc = static_cast<int>(*args);
    argv = reinterpret_cast<char**>(args + 1);
    envp = argv + argc + 1;

    // Skip over all environment variable definitions to find aux vector.
    // The end of the environment block is marked by two NULL pointers.
    char** p = envp;
    while (*p != NULL) {
      ++p;
    }
    ++p; // Skip second NULL;

    auxv = reinterpret_cast<ElfW(auxv_t)*>(p);
  }
}
``` 

从代码逻辑，可总结出栈数据布局可能是这样的：
```
position            content                     size (bytes)  comment
  ------------------------------------------------------------------------
stack pointer ->  [ argc = number of args ]     4      
                  [ argv[0] (pointer) ]         4      
                  [ argv[1] (pointer) ]         4      
                  [ argv[..] (pointer) ]        4 * n  
                  [ argv[n - 1] (pointer) ]     4      
                  [ argv[n] (pointer) ]         4           = NULL

                  [ envp[0] (pointer) ]         4     
                  [ envp[1] (pointer) ]         4      
                  [ envp[..] (pointer) ]        4      
                  [ envp[term] (pointer) ]      4           = NULL

                  [ auxv[0] (Elf32_auxv_t) ]    8      
                  [ auxv[1] (Elf32_auxv_t) ]    8
                  [ auxv[..] (Elf32_auxv_t) ]   8 
                  [ auxv[term] (Elf32_auxv_t) ] 8           = AT_NULL vector

                  [ padding ]                   0 - 16     

                  [ argument ASCIIZ strings ]   >= 0   
                  [ environment ASCIIZ str. ]   >= 0   

(0xbxxxxxxx)      [ end marker ]                4          = NULL 结束

(0xbx000000)       < bottom of stack >          0          (virtual)
```

### 参数
接下来分析一个真实的进程，验证上述结论。进程主线程栈的范围是：be11e000-be91d000，当执行到__linker_init时，raw_args=0xBE91CB60。

![Main thread stack 0xBE91CB60]({static}/images/main_thread_stack_BE91CB60.png)

按照顺序解析数据：
argc = 5
argv[0] = 0xBE91CC59 存储了字符串“ss.android.lotus.demo” 即进程名。
argv[1] = 0xBE91CC71 字符串为空
argv[2] = 0xBE91CC7A 字符串为空
argv[3] = 0xBE91CC86 字符串为空
argv[4] = 0xBE91CC8E 字符串为空
argv[5] = 0x00000000 NULL

### 环境变量
继续分析envp结构，envp指向的数据：
![Main thread stack 0xBE91CCA0]({static}/images/main_thread_stack_BE91CCA0.png)
![Main thread stack 0xBE91CEC0]({static}/images/main_thread_stack_BE91CEC0.png)

envp[0] = 0xBE91CCA5 PATH=/sbin:/vendor/bin:/system/sbin:/system/bin:/system/xbin
envp[1] = 0xBE91CCE2 ANDROID_BOOTLOGO=1
envp[2] = 0xBE91CCF5 ANDROID_ROOT=/system
envp[3] = 0xBE91CD0A ANDROID_ASSETS=/system/app
envp[4] = 0xBE91CD25 ANDROID_DATA=/data
envp[5] = 0xBE91CD38 ANDROID_STORAGE=/storage
envp[6] = 0xBE91CD51 EXTERNAL_STORAGE=/sdcard
envp[7] = 0xBE91CD6A ASEC_MOUNTPOINT=/mnt/asec
envp[8] = 0xBE91CD84 BOOTCLASSPATH=/system/framework/core-libart.jar:/system/framework/conscrypt.jar:...
envp[9] = 0xBE91CF2C SYSTEMSERVERCLASSPATH=/system/framework/services.jar:...
envp[10] = 0xBE91CFAB ANDROID_PROPERTY_WORKSPACE=10,0
envp[11] = 0xBE91CFCB ANDROID_SOCKET_zygote=12
envp[12] = 0x00000000

### 辅助向量表
继续分析axuv接口，auxv结构体定义：
```c++
typedef struct {
  __u32 a_type;
  union {
    __u32 a_val;
  } a_un;
} Elf32_auxv_t;
```
每一项auxv占用8个字节。auxv 的type定义：
```c++
#define AT_NULL 0
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_IGNORE 1
#define AT_EXECFD 2
#define AT_PHDR 3
#define AT_PHENT 4
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_PHNUM 5
#define AT_PAGESZ 6
#define AT_BASE 7
#define AT_FLAGS 8
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_ENTRY 9
#define AT_NOTELF 10
#define AT_UID 11
#define AT_EUID 12
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_GID 13
#define AT_EGID 14
#define AT_PLATFORM 15
#define AT_HWCAP 16
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_CLKTCK 17
#define AT_SECURE 23
#define AT_BASE_PLATFORM 24
#define AT_RANDOM 25
/* WARNING: DO NOT EDIT, AUTO-GENERATED CODE - SEE TOP FOR INSTRUCTIONS */
#define AT_HWCAP2 26
#define AT_EXECFN 31
```

0xBE91CBB0 是auxv数据的开始地址。

auxv[0]=0x10(AT_HWCAP) 0x0007B0D7

auxv[1]=0x06(AT_PAGESZ) 0x00001000  页大小4KB

auxv[2]=0x11(AT_CLKTCK) 0x00000064

auxv[3]=0x03(AT_PHDR) 0xB6F79034 /system/bin/app_process32_xposed 的phdr地址

auxv[4]=0x04(AT_PHENT) 0x00000020 segment表每一项的大小

auxv[5]=0x05(AT_PHNUM) 0x00000009 segment表项数量

auxv[6]=0x07(AT_BASE) 0xB6F57000

auxv[7]=0x08(AT_FLAGS) 0x00000000

auxv[8]=0x09(AT_ENTRY) 0xB6F7DEE8

auxv[9]=0x0D(AT_GID) 0x00000000

auxv[10]=0x0E(AT_EGID) 0x00000000

auxv[11]=0x17(AT_SECURE) 0x00000000

auxv[12]=0x19(AT_RANDOM) 0xBE91CC45

auxv[13]=0x1F(AT_EXECFN) 0xBE91CFE4  "/system/bin/app_process"

auxv[14]=0x0F(AT_PLATFORM) 0xBE91CC55 "v71"

auxv[15]=0x00(AT_NULL) 0x00000000

AT_BASE=0xB6F57000表示linker在内存中的地址

![Lotus memory layout for auxv]({static}/images/lotus_memory_layout_auxv.png)

可以看出，“/system/bin/linker”在内存的开始地址正是0xB6F57000。
AT_ENTRY=0xB6F7DEE8表示app_process32_xposed的入口地址。根据app_process32_xposed的开始地址0xB6F79000，可以计算出入口的相对偏移：
RVA = 0xB6F7DEE8 - 0xB6F79000 = 0x4EE8

使用readelf可以解析出app_process32_xposed的入口正是0x4EE8。

```bash
$ arm-linux-androideabi-readelf -h app_process32_xposed
ELF Header:
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF32
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Shared object file)
  Machine:                           ARM
  Version:                           0x1
  Entry point address:               0x4ee8
  Start of program headers:          52 (bytes into file)
  Start of section headers:          91756 (bytes into file)
  Flags:                             0x5000000, Version5 EABI
  Size of this header:               52 (bytes)
  Size of program headers:           32 (bytes)
  Number of program headers:         9
  Size of section headers:           40 (bytes)
  Number of section headers:         32
  Section header string table index: 29
```


## 小结
本文主要探索了ARM架构下Android系统中，进程的部分关键内存空间细节，目的是为了更加真实地模拟进程空间，提升模拟执行库的稳定性。

## 参考资料
- [Linux Kernel 3.4](http://androidxref.com/kernel_3.4)
- [Android 6.0.1_r10](http://androidxref.com/6.0.1_r10)
