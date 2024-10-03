Title: unicorn v1.0.3 Bug : IT 指令不能工作
Date: 2021-06-24 21:20:55
Modified: 2022-05-05 15:17:53
Category: Reverse Engineering
Tags: unicorn, arm
Slug: unicorn-v1-0-3-bug-it-instruction-not-work
Figure: idapro.png

## 测试代码
```c
{! sample/sample_arm.c !}
```

## V1.0.2 输出
```shell
==========================
Emulate THUMB code
>>> SP = 0x800000
>>> Tracing instruction at 0x1000000, instruction size = 0x2, instruction = 10 b5
>>> Tracing instruction at 0x1000002, instruction size = 0x4, instruction = 4f f6 00 74
>>> Tracing instruction at 0x1000006, instruction size = 0x2, instruction = e8 bf
>>> Tracing instruction at 0x1000008, instruction size = 0x2, instruction = 10 bd
>>> Emulation done. Below is the CPU context
>>> SP = 0x800000
```

## V1.0.3 输出
```shell
==========================
Emulate THUMB code
>>> SP = 0x800000
thumb insn: 0xb510
thumb insn: 0xb510 gen_uc_tracecode
thumb2:insn: 0xf64f
thumb insn: 0xbfe8
>>> Tracing instruction at 0x1000000, instruction size = 0x2, instruction = 10 b5
>>> Tracing instruction at 0x1000002, instruction size = 0x4, instruction = 4f f6 00 74
>>> Emulation done. Below is the CPU context
>>> SP = 0x800000
```

## 尝试修复

修复的具体进展：[issues #1412](https://github.com/unicorn-engine/unicorn/issues/1412)

笔者通过自己阅读源代码发现，可能是修复 [issues #853](https://github.com/unicorn-engine/unicorn/issues/853)引入的BUG，代码差异：

qemu/target-arm/translate.c

- Version 1.0.2
```c
default:
  gen_uc_tracecode(tcg_ctx, 2, UC_HOOK_CODE_IDX, s->uc, s->pc);
```

- Version 1.0.3
```c
default:
  if (!((insn & 0xff00) == 0xbf00)){
    gen_uc_tracecode(tcg_ctx, 2, UC_HOOK_CODE_IDX, s->uc, s->pc);
  }              
```

但是简单还原为1.0.2的代码，也不能正常运行。期待[issues #1412](https://github.com/unicorn-engine/unicorn/issues/1412)的解决。

