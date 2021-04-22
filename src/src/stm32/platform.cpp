#if defined(PLATFORM_STM32)

#include <stm32_def.h>
#include <string.h>
#include <stdint.h>

void copy_functions_to_ram(void)
{
    /* Load functions into RAM */
    extern uint8_t ram_code_start;
    extern uint8_t ram_code_end;
    extern uint8_t ram_code;
    memcpy(&ram_code_start, &ram_code, (size_t) (&ram_code_end - &ram_code_start));
}



__attribute__((constructor(102))) void perkele_initVariant(void)
{
    copy_functions_to_ram();
    /* Reset vector location which is set wrongly by SystemInit */
    extern uint32_t g_pfnVectors;
    SCB->VTOR = (__IO uint32_t) &g_pfnVectors;
}

extern "C"
void initVariant(void)
{
    /* This can be used to run some init before \ref setup() */
}

#endif /* PLATFORM_STM32 */
