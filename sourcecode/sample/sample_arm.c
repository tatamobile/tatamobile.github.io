/* Unicorn Emulator Engine */
/* By Nguyen Anh Quynh, 2015 */

/* Sample code to demonstrate how to emulate ARM code */

#include <unicorn/unicorn.h>
#include <string.h>


// code to be emulated
#define THUMB_CODE "\x10\xb5\x4f\xf6\x00\x74\xe8\xbf\x10\xbd"

// memory address where emulation starts

int STACK_MEMORY_BASE = 0x00000000;
int STACK_MEMORY_SIZE = 0x00800000;

int HOOK_MEMORY_BASE = 0x1000000;
int HOOK_MEMORY_SIZE = 0x0800000;



static void hook_code(uc_engine *uc, uint64_t address, uint32_t size, void *user_data)
{
    unsigned char bytes[8];
    char instruction[32] = {0};
    int i = 0;
    uc_mem_read(uc,address,bytes,size);
    for(i = 0; i < size; i++){
      sprintf(instruction + i * 3,"%02x ", bytes[i]);
    }
    printf(">>> Tracing instruction at 0x%"PRIx64 ", instruction size = 0x%x, instruction = %s\n", address, size, instruction);
    
    
}

unsigned char bytes[32];
char instruction[64] = {0};
static void test_thumb(void)
{
    uc_engine *uc;
    uc_err err;
    uc_hook trace2;

    int sp = 1024;     // R0 register
    int code_length;

    printf("Emulate THUMB code\n");

    // Initialize emulator in ARM mode
    err = uc_open(UC_ARCH_ARM, UC_MODE_THUMB, &uc);
    if (err) {
        printf("Failed on uc_open() with error returned: %u (%s)\n",
                err, uc_strerror(err));
        return;
    }

    // map 2MB memory for this emulation
    uc_mem_map(uc, HOOK_MEMORY_BASE, HOOK_MEMORY_SIZE, UC_PROT_ALL);
    uc_mem_map(uc, STACK_MEMORY_BASE, STACK_MEMORY_SIZE, UC_PROT_ALL);

    // write machine code to be emulated to memory
    code_length = sizeof(THUMB_CODE) - 1;
    
    uc_mem_write(uc, HOOK_MEMORY_BASE, THUMB_CODE, code_length);
    

    // initialize machine registers
    int lr = HOOK_MEMORY_BASE + 0x80;
    sp = STACK_MEMORY_BASE + STACK_MEMORY_SIZE;
    uc_reg_write(uc, UC_ARM_REG_SP, &sp);
    printf(">>> SP = 0x%x\n", sp);
    uc_reg_write(uc, UC_ARM_REG_LR, &lr);

    // tracing all basic blocks with customized callback
    //uc_hook_add(uc, &trace1, UC_HOOK_BLOCK, hook_block, NULL, 1, 0);

    // tracing one instruction at ADDRESS with customized callback
    uc_hook_add(uc, &trace2, UC_HOOK_CODE, hook_code, NULL, HOOK_MEMORY_BASE, HOOK_MEMORY_BASE + HOOK_MEMORY_SIZE);

    // emulate machine code in infinite time (last param = 0), or when
    // finishing all the code.
    // Note we start at ADDRESS | 1 to indicate THUMB mode.
    err = uc_emu_start(uc, (HOOK_MEMORY_BASE) | 1, lr, 0, 0);
    if (err) {
        printf("Failed on uc_emu_start() with error returned: %u\n", err);
    }

    // now print out some registers
    printf(">>> Emulation done. Below is the CPU context\n");

    uc_reg_read(uc, UC_ARM_REG_SP, &sp);
    printf(">>> SP = 0x%x\n", sp);

    uc_close(uc);
}

int main(int argc, char **argv, char **envp)
{
    // dynamically load shared library
#ifdef DYNLOAD
    if (!uc_dyn_load(NULL, 0)) {
        printf("Error dynamically loading shared library.\n");
        printf("Please check that unicorn.dll/unicorn.so is available as well as\n");
        printf("any other dependent dll/so files.\n");
        printf("The easiest way is to place them in the same directory as this app.\n");
        return 1;
    }
#endif
    
    // test_arm();
    printf("==========================\n");
    test_thumb();

    // dynamically free shared library
#ifdef DYNLOAD
    uc_dyn_free();
#endif
    
    return 0;
}
