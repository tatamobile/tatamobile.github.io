Title: 重学ELF文件格式
Date: 2022-02-23 20:52:22
Modified: 2023-02-23 20:52:22
Category: Reverse Engineering
Tags: elf, arm, android
Slug: elf-file-format-under-the-hood
Figure: android.png


## 缘起

ELF文件格式的讨论已经存在非常多的文章，这里试图从另一个角度来讨论如何学习ELF文件格式。OAID SDK已经更新到1.0.30了，发现代码保护方式变化了，采用了自实现Linker方式来保护代码，libmsaoaidsec.so 就是负责释放真实的so。但本文不讨论释放和自加载过程，主要讨论从内存中dump真实代码到文件后，如何修复这个ELF文件，达到学习ELF文件格式的目的。放一张ELF文件结构图，有个整体印象：

![ELF file link view & load view]({static}/images/elf_view.png)

## 初探

可以从链接视图和内存视图两个角度来观察ELF文件格式，一般的ELF文件修复工具都是从内存视图解析相关信息后重构出链接视图。但从OAID SDK 内存中dump出来的文件，程序头表(PHDR)已经被抹除了。

![sodump oaid ehdr]({static}/images/sodump_oaid_ehdr.png)

从图中可知，ELF文件头被"F1F1"覆盖了，就不能解析出PHDR，一般的修复工具就失效了。遇到这种情况，该如何修复呢？逆向工程有一个指导原则：“正反结合”。可以这样假设：这个dump出来的ELF文件和标准的ELF文件相比，只有ELF文件头部有改变，其他地方应该和标准的ELF文件格式一样。可以自己编译一个标准的ELF文件一一对比布局，就可以修复。从上图还可以看出，OAID SDK应该是采用NDK r16 编译的，为了消除编译器差异，我们也用相同版本的NDK编译出一个标准的ELF文件。标准ELF文件的文件头如下：

![elf ndk r16b ehdr]({static}/images/elf_ndk_r16b_ehdr.png)

通过对比可知，主要差异确实就是程序头部表（Program Header Table）。

## 重建
### ELF文件头

通过观察可知，dump文件的EHDR是完整的，可以解析，解析结果如下：
```bash
>>> data length: 0x0009d000
ident:7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
>>> parse elf header ...
Class: ELFCLASS32
Type: ET_DYN
Machine: EM_ARM
Version: EV_CURRENT
Start of section headers: 0x0
Entry point address: 0x9b1ec
Start of program headers: 0x34
Start of section headers: 0x9b1ec
Flags: 0x5000200
Size of this header: 0x34
Size of program headers: 32
Number of program headers: 8
Size of section headers: 40
Number of section headers: 27
Section header string table index: 26
+++ ph offset: 0x34 - 0x134
+++ sh offset: 0x9b1ec - 0x9b624
```

dump ELF文件有8个program header和26个section header,标准ELF文件有8个program header和27个section header。
```bash
$ arm-linux-androideabi-readelf -h libarmelfformat.so
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
  Entry point address:               0x0
  Start of program headers:          52 (bytes into file)
  Start of section headers:          103040 (bytes into file)
  Flags:                             0x5000200, Version5 EABI, soft-float ABI
  Size of this header:               52 (bytes)
  Size of program headers:           32 (bytes)
  Number of program headers:         8
  Size of section headers:           40 (bytes)
  Number of section headers:         28
  Section header string table index: 27
```

### 初探ELF段表(Segment Header Table)

观察标准ELF文件段表：
```bash
arm-linux-androideabi-readelf -l libarmelfformat.so
Elf file type is DYN (Shared object file)
Entry point 0x0
There are 8 program headers, starting at offset 52

Program Headers:
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  PHDR           0x000034 0x00000034 0x00000034 0x00100 0x00100 R   0x4
  LOAD           0x000000 0x00000000 0x00000000 0x17b7c 0x17b7c R E 0x1000
  LOAD           0x017fc0 0x00018fc0 0x00018fc0 0x010d4 0x06014 RW  0x1000
  DYNAMIC        0x018c1c 0x00019c1c 0x00019c1c 0x00120 0x00120 RW  0x4
  NOTE           0x000134 0x00000134 0x00000134 0x000bc 0x000bc R   0x4
  GNU_STACK      0x000000 0x00000000 0x00000000 0x00000 0x00000 RW  0x10
  EXIDX          0x015580 0x00015580 0x00015580 0x00bb0 0x00bb0 R   0x4
  GNU_RELRO      0x017fc0 0x00018fc0 0x00018fc0 0x01040 0x01040 RW  0x8

 Section to Segment mapping:
  Segment Sections...
   00
   01     .note.android.ident .note.gnu.build-id .dynsym .dynstr .hash .gnu.version .gnu.version_d .gnu.version_r .rel.dyn .rel.plt .plt .text .ARM.extab .ARM.exidx .rodata
   02     .data.rel.ro.local .fini_array .data.rel.ro .init_array .dynamic .got .data .bss
   03     .dynamic
   04     .note.android.ident .note.gnu.build-id
   05
   06     .ARM.exidx
   07     .data.rel.ro.local .fini_array .data.rel.ro .init_array .dynamic .got
```
重建ELF文件的过程就是要分析出每个段(Segment)和节(Section)的开始位置和大小。从标准ELF文件分析结果，可以确定两个段的开始位置和大小：PHDR和NOTE。对于其它段全部先暂时全部填充0。为了能让IDA等工具可以加载分析，需要生成一个LOAD段，暂时将开始位置设为0，大小为整个文件的大小。

段PHDR 开始位置：0x34，大小：0x100，恰好就是整个段表。
段NOTE 开始位置：0x134,大小：0xbc，来看下是什么内容：

![sodump oaid segment note]({static}/images/sodump_oaid_segment_note.png)

看起来像是在描述编译器的信息，比如NDK版本号和GCC版本号等。
到目前为止，已经分析出两个段的信息，经过与标准ELF文件比对，应该是正确的。

### 初探ELF节表(Section Header Table)
观察标准ELF文件节表
```bash
arm-linux-androideabi-readelf -S libarmelfformat.so
There are 28 section headers, starting at offset 0x19280:

Section Headers:
  [Nr] Name              Type            Addr     Off    Size   ES Flg Lk Inf Al
  [ 0]                   NULL            00000000 000000 000000 00      0   0  0
  [ 1] .note.android.ide NOTE            00000134 000134 000098 00   A  0   0  4
  [ 2] .note.gnu.build-i NOTE            000001cc 0001cc 000024 00   A  0   0  4
  [ 3] .dynsym           DYNSYM          000001f0 0001f0 000b20 10   A  4   1  4
  [ 4] .dynstr           STRTAB          00000d10 000d10 001496 00   A  0   0  1
  [ 5] .hash             HASH            000021a8 0021a8 0004dc 04   A  3   0  4
  [ 6] .gnu.version      VERSYM          00002684 002684 000164 02   A  3   0  2
  [ 7] .gnu.version_d    VERDEF          000027e8 0027e8 00001c 00   A  4   1  4
  [ 8] .gnu.version_r    VERNEED         00002804 002804 000020 00   A  4   1  4
  [ 9] .rel.dyn          REL             00002824 002824 001118 08   A  3   0  4
  [10] .rel.plt          REL             0000393c 00393c 000348 08  AI  3  21  4
  [11] .plt              PROGBITS        00003c84 003c84 000500 00  AX  0   0  4
  [12] .text             PROGBITS        00004184 004184 010d18 00  AX  0   0  4
  [13] .ARM.extab        PROGBITS        00014e9c 014e9c 0006e4 00   A  0   0  4
  [14] .ARM.exidx        ARM_EXIDX       00015580 015580 000bb0 08  AL 12   0  4
  [15] .rodata           PROGBITS        00016130 016130 001a4c 00   A  0   0  4
  [16] .data.rel.ro.loca PROGBITS        00018fc0 017fc0 0007b8 00  WA  0   0  8
  [17] .fini_array       FINI_ARRAY      00019778 018778 000008 04  WA  0   0  4
  [18] .data.rel.ro      PROGBITS        00019780 018780 00048c 00  WA  0   0  8
  [19] .init_array       INIT_ARRAY      00019c0c 018c0c 000010 04  WA  0   0  4
  [20] .dynamic          DYNAMIC         00019c1c 018c1c 000120 08  WA  4   0  4
  [21] .got              PROGBITS        00019d40 018d40 0002c0 00  WA  0   0  4
  [22] .data             PROGBITS        0001a000 019000 000094 00  WA  0   0  4
  [23] .bss              NOBITS          0001a098 019094 004f3c 00  WA  0   0  8
  [24] .comment          PROGBITS        00000000 019094 000065 01  MS  0   0  1
  [25] .note.gnu.gold-ve NOTE            00000000 0190fc 00001c 00      0   0  4
  [26] .ARM.attributes   ARM_ATTRIBUTES  00000000 019118 00003d 00      0   0  1
  [27] .shstrtab         STRTAB          00000000 019155 00012a 00      0   0  1
```

节.note.android.ident和.note.gnu.build-id的内容和段NOTE是一致的。紧挨着的是节.dynsym和.dynstr。可以确定节.dynsym的开始位置就是0x1f0。但如何确定.dynsym的结束位置呢？可以使用节.dynstr开头内容的特征区分，标准ELF文件节.dynstr开头的内容：

![elf ndk r16b dynstr]({static}/images/elf_ndk_r16b_dynstr.png)

从上图可知，节.dynstr开头的字符串是“.__cxa_finalize”，尝试在dump文件里顺序查找，看是否有这样的特征：

![sodump oaid dynstr]({static}/images/sodump_oaid_dynstr.png)

这样就可以初步确定节.dynsym的开始和结束位置：0x01F0 ~ 0x31D0。节.dynstr的开始位置：0x31D0，那.dynstr的结束位置如何确定呢？ 

![sodump oaid dynstr end]({static}/images/sodump_oaid_dynstr_end.png)

从上图观察，节.dynstr的结束位置还是非常好确定的，初步认为就是：0xA9B4。接下来计算节.hash的大小，根据.hash的结构计算：
```bash
(nbuckets + nchains + 1 + 1) * 4 = (0x209 + 0x2FE + 1 + 1) * 4 = 0x1424
```
紧接着，节.gnu.version的开始位置是：0xA9B4 + 0x1424 = 0xBDD8。
小结：到目前为止，我们已经分析出5个节的开始位置和结束位置
- .note.android.ident : 0x134 ~ 0x1CC
- .note.gnu.build-id : 0x1CC ~ 0x1F0
- .dynsym : 0x01F0 ~ 0x31D0
- .dynstr: 0x31D0 ~ 0xA9B4
- .hash: 0xA9B4 ~ 0xBDD8

接下来分析节.plt(Procedure Linkage Table)，带版本的符号相关节(.gnu.version)暂不分析。

### 分析节.PLT
通过观察节.plt和节.text是紧挨着的，且开始位置有明显的特征。观察节.plt开始位置和结束位置的反汇编代码，
开始位置：

![sodump oaid plt start]({static}/images/sodump_oaid_plt_start.png)

结束位置：

![sodump oaid plt end]({static}/images/sodump_oaid_plt_end.png)

节.plt开始位置是固定16字节的一个函数sub_D438，然后接着就是一组类似sub_D44C这样的函数，直到结束。因此，节.plt的开始位置和结束位置是：0xD438 ~ 0xD920。

从节.plt节的信息还可以计算出节.rel.plt的大小，计算方法：
```bash
(0xD920 - 0xD438 - 0x14) / 0xC = 0x67
```
0x67 是节.rel.plt中重定位的数量，上述公式中的0x14是函数sub_D438的大小，0xC是每个桩函数如sub_D44C的大小。
由于节.rel.plt与节.plt相邻，因此节.rel.plt的结束位置：0xD438，重定位每项大小为8，个数为0x67，大小为0x338。节.rel.plt的开始位置和结束位置为：0xD100 ~ 0xD438。那么节.rel.dyn的结束位置为：0xD100。那如何确定节.rel.dyn的开始位置呢？还是根据特征。观察标准ELF文件节.rel.dyn开始位置的内容：

![elf ndk r16b rel_dyn start]({static}/images/elf_ndk_r16b_rel_dyn_start.png)

可以看到有大量的0x17（0x17 就是 R_ARM_RELATIVE），由此可以找到dump文件中节.rel.dyn的开始位置：

![sodump oaid rel_dyn start]({static}/images/sodump_oaid_rel_dyn_start.png)

可初步推断节.rel.dyn的开始位置是0xC430，即节.rel.dyn的开始和结束位置为：0xC430 ~ 0xD100。

继续观察前面提到的函数sub_D438中的一行汇编代码：
```armasm
LDR             LR, =(dword_9BE58 - 0xD448)
```
dword_9BE58就是常说的“_GLOBAL_OFFSET_TABLE_”，即0x9BE58在节.got范围内。从0x9BE58向前和向后观察，可以初步推断节.got的开始和结束位置。
开始位置：

![sodump oaid got start]({static}/images/sodump_oaid_got_start.png)

结束位置：

![sodump oaid got end]({static}/images/sodump_oaid_got_end.png)

小结：到目前为止，初步分析出4个节的开始和结束位置：
- .rel.dyn : 0xC430 ~ 0xD100
- .rel.plt : 0xD100 ~ 0xD438
- .plt : 0xD438 ~ 0xD920
- .got : 0x9BDCC ~ 0x9C000

### 带版本信息的符号
与版本符号相关的节一般是3个：.gnu.version，.gnu.version_d和.gnu.version_r。根据前文的分析可知，这3个节的开始和结束位置是：0xBDD8 ~ 0xC430。如何来划分这3个节各自的开始和结束位置呢？主要通过相关节的作用来分析。参考[Symbol Versioning](https://refspecs.linuxfoundation.org/LSB_3.0.0/LSB-PDA/LSB-PDA.junk/symversion.html)。

#### .gnu.version
来看一段节.gnu.version的描述：
> The special section .gnu.version which has a section type of SHT_GNU_versym shall contain the Symbol Version Table. This section shall have the same number of entries as the Dynamic Symbol Table in the .dynsym section.

翻译：节.gnu.version与节.dynsym的项数相同。
> The .gnu.version section shall contain an array of elements of type Elfxx_Half. Each entry specifies the version defined for or required by the corresponding symbol in the Dynamic Symbol Table.

翻译：节.gnu.version每一项的大小是2字节。

节.dynsym的开始和结束位置是：0x01F0 ~ 0x31D0。项数是：(0x31D0 - 0x01F0) / 0x10 = 0x2FE，因此，节.gnu.version的大小是：0x2FE * 2 = 0x5FC，开始和结束位置是：0xBDD8 ~ 0xC3D4

#### .gnu.version_d
来看一段.gnu.version_d的描述：
> The special section .gnu.version_d which has a section type of SHT_GNU_verdef shall contain symbol version definitions. The number of entries in this section shall be contained in the DT_VERDEFNUM entry of the Dynamic Section .dynamic. The sh_link member of the section header (see figure 4-8 in the System V ABI) shall point to the section that contains the strings referenced by this section.

翻译：.gnu.version_d的sh_link一般指向节.dynstr，且与节.dynamic中的某一项DT_VERDEFNUM有关。

> The section shall contain an array of Elfxx_Verdef structures,optionally followed by an array of Elfxx_Verdaux structures

翻译：节.gnu.version_d 是一个数组，每一项是结构Elfxx_Verdef，可能会跟Elfxx_Verdaux。

结构体Elfxx_Verdef定义
```c++
typedef struct {
	Elfxx_Half    vd_version;
	Elfxx_Half    vd_flags;
	Elfxx_Half    vd_ndx;
	Elfxx_Half    vd_cnt;
	Elfxx_Word    vd_hash;
	Elfxx_Word    vd_aux;
	Elfxx_Word    vd_next;
} Elfxx_Verdef;
```
结构体Elfxx_Verdaux定义
```c++
typedef struct {
	Elfxx_Word    vda_name;
	Elfxx_Word    vda_next;
} Elfxx_Verdaux;
```
每个成员的含义，用修复好的实际例子解释，一般的so节.gnu.version_d只有一项：

![sodump oaid gnu_version_d]({static}/images/sodump_oaid_gnu_version_d.png)

- vd_cnt:与之关联的verdaux有几个，这里是1个。
- vd_aux: verdaux偏移，这里是0x14。
- vd_next: 下一个verdef偏移。这里是0，表示结束。
- vda_name: 在.dynstr中的偏移。值为0x1D。
- vda_next: 下一个verdaux入口位置。值为0，表示结束。


#### .gnu.version_r
来看一段关于节.gnu.version_r的描述：
> The special section .gnu.version_r which has a section type of SHT_GNU_verneed shall contain required symbol version definitions. The number of entries in this section shall be contained in the DT_VERNEEDNUM entry of the Dynamic Section .dynamic. The sh_link member of the section header (see figure 4-8 in System V ABI) shall point to the section that contains the strings referenced by this section.

翻译：.gnu.version_r的sh_link一般指向节.dynstr，且与节.dynamic中的某一项DT_VERNEEDNUM有关。
> The section shall contain an array of Elfxx_Verneed structures, as described in Figure 2-3, optionally followed by an array of Elfxx_Vernaux structures, as defined in Figure 2-4.

翻译：节.gnu.version_r 是一个数组，每一项是结构Elfxx_Verneed，可能会跟Elfxx_Vernaux。

结构体Elfxx_Verneed的定义：
```c++
typedef struct {
	Elfxx_Half    vn_version;
	Elfxx_Half    vn_cnt;
	Elfxx_Word    vn_file;
	Elfxx_Word    vn_aux;
	Elfxx_Word    vn_next;
} Elfxx_Verneed;
```

结构体Elfxx_Vernaux的定义：
```c++
typedef struct {
	Elfxx_Word    vna_hash;
	Elfxx_Half    vna_flags;
	Elfxx_Half    vna_other;
	Elfxx_Word    vna_name;
	Elfxx_Word    vna_next;
} Elfxx_Vernaux;
```
每个成员的含义，用修复好的实际例子解释:

![sodump oaid gnu_version_r]({static}/images/sodump_oaid_gnu_version_r.png)

- vn_file : 在节.dynstr的偏移 。
- vn_aux :  与这个verneed关联的vernaux入口偏移。
- vn_next : 下一个verneed入口的偏移。
- vna_name : 在节.dynstr的偏移。
- vna_next : 下一个vernaux入口的偏移。

本文不关注“版本符号”的用途，只关注节的边界，所以只选择了解释与偏移、大小等相关成员解释。

小结：本节分析出3个节的开始和结束位置：
- .gnu.version : 0xBDD8 ~ 0xC3D4
- .gnu.version_d : 0xC3D4 ~ 0xC3F0
- .gnu_version_r : 0xC3F0 ~ 0xC430

### 节.ARM.exidx和.ARM.extab
节.ARM.exidx和.ARM.extab是ARM架构体系下专门用于异常处理：发生异常时，借助这两个节的信息还原出调用栈，此方法与传统的基于EBP恢复调用栈区别很大，如何恢复调用栈，不在本文讨论，这里主要借助这两个节的特殊信息来确定其他节的边界，比如节.text。

节.text,.ARM.extab,.ARM.exidx和.rodata 4个节相邻，从前面分析可知，节.text开始位置是：0xD920。那节.ARM.exidx如何确定开始和结束位置呢？其实没什么办法直接分析出来，不过可以先看看节.rodata的开始位置在哪里？观察下图：

![sodump oaid rodata start]({static}/images/sodump_oaid_rodata_start.png)

初步判断0x93620，因为0x93621一定在节.rodata里，根据对齐原则，可认为0x93620就是节.rodata的开始位置，也是节.ARM.exidx的结束位置。先直接给出结论，可以使用如下脚本直接分析出节.ARM.exidx和.ARM.extab的边界：
```python
# -*- coding:utf-8 -*-
import os
from io import BytesIO
from elftools.elf.elffile import ELFFile
from elftools.elf.structs import ELFStructs
from elftools.ehabi.ehabiinfo import EHABIInfo


class MemoryELFFile(ELFFile):
    """精简过的 ELFFile，去除里面多余的功能"""

    def __init__(self, stream):
        self.stream = stream
        self._identify_file()
        self.structs = ELFStructs(
            little_endian=self.little_endian,
            elfclass=self.elfclass)

        self.structs.create_basic_structs()
        self.header = self._parse_elf_header()
        self.structs.e_type = self['e_type']
        self.structs.e_machine = self['e_machine']
        self.structs.e_ident_osabi = self['e_ident']['EI_OSABI']
        self.structs._create_phdr()


class FakeSection:
    """因为无法从内存中恢复完整的 Section，只能手动创建虚假的 Section，填充关键数据"""

    def __init__(self, stream, offset, size):
        self.stream = stream
        self.offset = offset
        self.size = size

    def __getitem__(self, item):
        if item == 'sh_offset':
            return self.offset
        elif item == 'sh_size':
            return self.size

"""
特征码:80A8B0B0
"""
if __name__ == "__main__":
    filename = "./data/libdump_oaid_0x9ad23000_0x0009d000.bin"
    print(filename)
    with open(filename, "rb") as f:
        data = f.read()
        stream = BytesIO(data)
        elf = MemoryELFFile(stream)
        print(elf)

        exidx_offset = 0x917c8
        exidx_size = 0x93620 - exidx_offset
        ehabi_info = EHABIInfo(FakeSection(stream, exidx_offset, exidx_size), elf.little_endian)
        print("exentry count: {}".format(ehabi_info.num_entry()))
        eh_table_offset_max = 0
        eh_table_offset_min = 0xFFFFFFFF
        for i in range(ehabi_info.num_entry()):
            entry = ehabi_info.get_entry(i)
            print(entry)
            eh_table_offset = entry.eh_table_offset
            if eh_table_offset is None:
                continue
            if eh_table_offset < eh_table_offset_min:
                eh_table_offset_min = eh_table_offset
            if eh_table_offset > eh_table_offset_max:
                eh_table_offset_max = eh_table_offset
    print("extab:0x{:x}-0x{:x}".format(eh_table_offset_min, eh_table_offset_max))
    print("success.")
```
运行脚本，结果如下：
```bash
python3 parser_arm_exidx.py
...
extab:0x8dc50-0x917bc
success.
```
由此可确定三个节的开始和结束位置：
- .text : 0xD920 ~ 0x8dc50
- .ARM.extab : 0x8dc50-0x917bc
- .ARM.exidx : 0x917bc-0x93620

现在，来解释一下上述脚本的关键点
- 0x93620 是我们初步分析出的.rodata的开始位置也是.ARM.exidx的结束位置，经过解析0x93620前的几个字节是否合法，就进一步确定了0x93620就是节.ARM.exidx的结束位置。
- 0x917c8 代码中的这个数值是节.ARM.exidx的开始位置，是怎么分析出来的？没有什么好办法，就是从0x93620一直向前试，知道脚本不能正常解析，就找到了开始位置。每次向前移动8个字节，.ARM.exidx每一项的大小是8字节。
- 由于.ARM.extab是.ARM.exidx的辅助信息，完全可借助每一项信息分析出.ARM.extab的开始位置。观察一下解析结果就明白了：
```bash
<EHABIEntry function_offset=0xd930, personality=1, eh_table_offset=0x8dda0, bytecode=[151, 65, 132, 11, 176, 176]>
<CannotUnwindEHABIEntry function_offset=0xd9cc>
<EHABIEntry function_offset=0xd9f8, personality=1, eh_table_offset=0x8dc50, bytecode=[151, 65, 132, 13, 176, 176]>
<EHABIEntry function_offset=0xda34, personality=1, eh_table_offset=0x8dc5c, bytecode=[151, 65, 132, 13, 176, 176]>
<EHABIEntry function_offset=0xda70, personality=1, eh_table_offset=0x8dc68, bytecode=[151, 65, 132, 13, 176, 176]>
<EHABIEntry function_offset=0xdaac, personality=1, eh_table_offset=0x8dc74, bytecode=[151, 67, 128, 128, 171, 176]>
<EHABIEntry function_offset=0xdb24, personality=1, eh_table_offset=0x8dc80, bytecode=[151, 70, 128, 240, 171, 176]>
```
需要深入学习.ARM.exidx的内容，也可通过readelf查看：
```bash
readelf -u liboaid.so
```

### 节.init_array和.fini_array

这两个节的位置比较好确定，与.rodata相邻，这里直接给出结论：
- .fini_array : 0x9B5C4 ~ 0x9B5CC
- .init_array : 0x9B5CC ~ 0x9B5D4

那如何区分这两个节谁在前呢？可根据数组中函数确定。先看两个节的内容：

![sodump oaid fini_array]({static}/images/sodump_oaid_fini_array.png)

继续考察函数sub_D920：

![sodump oaid func_cxa_finalize]({static}/images/sodump_oaid_func_cxa_finalize.png)

调用__cxa_finalize的函数只可能在节.fini_array里，而且一般的so里都有这个函数，因此当不能确定.fini_array的位置时，可以根据谁引用了函数sub_D920来确定节.fini_array的大致位置。

### 节.dynamic
这个节非常重要，大部分修复工具也是根据这个节的内容分析出其他节的范围，但非常可惜，本文修复的目标文件把这个节的内容抹除了。节.dynamic一般在节.got的前面，看一下抹除后的内容：

![sodump oaid dynamic before fix]({static}/images/sodump_oaid_dynamic_pre_fix.png)

这里根据前面的分析结果，重建节.dynamic，重建脚本片段
```python
def rebuild_dynamic(self):
      # 重建dynamic
      print(">>> rebuild dynamic ...")
      self.dyns = list()
      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_PLTGOT'],d_val=0x9BDCC))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_PLTRELSZ'],d_val=824))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_JMPREL'],d_val=0xD100))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_PLTREL'],d_val=0x11))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_REL'],d_val=0xc430))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_RELSZ'],d_val=0xcd0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_RELENT'],d_val=8))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_RELCOUNT'],d_val=96))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_SYMTAB'],d_val=0x1f0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_SYMENT'],d_val=0x10))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_STRTAB'],d_val=0x31D0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_STRSZ'],d_val=0x77E4))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_HASH'],d_val=0xa9b4))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NEEDED'],d_val=0xa9a7-0x31D0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NEEDED'],d_val=0xa99f-0x31D0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NEEDED'],d_val=0xa995-0x31D0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NEEDED'],d_val=0x5e45-0x31D0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NEEDED'],d_val=0x15))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_SONAME'],d_val=0x1d))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_FINI_ARRAY'],d_val=0x9B5C4))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_FINI_ARRAYSZ'],d_val=8))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_INIT_ARRAY'],d_val=0x9B5CC))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_INIT_ARRAYSZ'],d_val=8))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_FLAGS'],d_val=8))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_FLAGS_1'],d_val=1))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_VERSYM'],d_val=0xbdd8))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_VERDEF'],d_val=0xc3d4))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_VERDEFNUM'],d_val=1))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_VERNEED'],d_val=0xC3f0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_VERNEEDNUM'],d_val=2))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      dyn_data = self.structs.Elf_Dyn.build(dict(d_tag=ENUM_D_TAG['DT_NULL'],d_val=0x0))
      dyn = self.structs.Elf_Dyn.parse(dyn_data)
      self.dyns.append(dyn_data)
      print(dyn)

      print("+++dynamic count:{}".format(len(self.dyns)))
```
来看下重建后的内容：

![sodump oaid dynamic fixed]({static}/images/sodump_oaid_dynamic_fixed.png)

## 总结
我们通过修复一个被严重破坏后的ELF文件，重新温习了ELF文件的各个关键结构。现在来看下整体修复成果：

![sodump odaid exports]({static}/images/sodump_oaid_exports.png)

这个JNI前面好像有点奇怪，其实是正常的，关于JNI签名的详细内容可参考 [JNI 方法注册和签名]({filename}/reverse_engineering/jni-function-name-override.md) 。

## 参考资料
- [Symbol Versioning](https://refspecs.linuxfoundation.org/LSB_3.0.0/LSB-PDA/LSB-PDA.junk/symversion.html)
- [ARM栈回溯——从理论到实践，开发ida-arm-unwind-plugin](https://bbs.pediy.com/thread-261585.htm)