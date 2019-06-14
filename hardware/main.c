/* ------------------------------------------
 * Copyright (c) 2017, Synopsys, Inc. All rights reserved.

 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:

 * 1) Redistributions of source code must retain the above copyright notice, this
 * list of conditions and the following disclaimer.

 * 2) Redistributions in binary form must reproduce the above copyright notice,
 * this list of conditions and the following disclaimer in the documentation and/or
 * other materials provided with the distribution.

 * 3) Neither the name of the Synopsys, Inc., nor the names of its contributors may
 * be used to endorse or promote products derived from this software without
 * specific prior written permission.

 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
--------------------------------------------- */

/**
 * \defgroup	EMBARC_APP_TMPL		embARC Template Example
 * \ingroup	EMBARC_APPS_TOTAL
 * \ingroup	EMBARC_APPS_BOARD_EMSK
 * \ingroup	EMBARC_APPS_BAREMETAL
 * \brief	embARC Example for template
 *
 * \details
 * ### Extra Required Tools
 *
 * ### Extra Required Peripherals
 *
 * ### Design Concept
 *
 * ### Usage Manual
 *
 * ### Extra Comments
 *
 */

/**
 * \file
 * \ingroup	EMBARC_APP_TMPL
 * \brief	main source of template example
 */

/**
 * \addtogroup	EMBARC_APP_TMPL
 * @{
 */
/* embARC HAL */
#include "embARC.h"
#include "embARC_debug.h"
#include "emsk_temperature.h"
#define LED_TOGGLE_MASK		BOARD_LED_MASK
#include <stdio.h>
#include <string.h>
#define BOARD_TEMP_I2C_SLAVE_ADDRESS  TEMP_I2C_SLAVE_ADDRESS
#include "u8g.h"
u8g_t u8g;
static DEV_IIC *iic_0;
static DEV_IIC *iic_1;
static DEV_UART *uart;
static uint32_t iic_slvaddr = 0x28;

#define EMSK_IIC_CHECK_EXP_NORTN(EXPR)		CHECK_EXP_NOERCD(EXPR, error_exit)
#define EMSK_GPIO_CHECK_EXP_NORTN(EXPR)		CHECK_EXP_NOERCD(EXPR, error_exit)
int32_t my_emsk_iic_init(uint32_t slv_addr);
void my_emsk_uart_init(void);
void u8g_prepare(void)
{
	u8g_SetFont(&u8g, u8g_font_7x14B);
	u8g_SetFontRefHeightExtendedText(&u8g);
	u8g_SetDefaultForegroundColor(&u8g);
	u8g_SetFontPosTop(&u8g);
}

static void draw(int32_t temp, int32_t g_temp)
{
	char s[] = "Temperature:  .  C";
	s[12] = (int)(temp / 100) + 48;
	s[13] = (int)((temp - ((int)(temp / 100)) * 100) / 10) + 48;
	s[15] = (int)(temp % 10) + 48;
	u8g_DrawStr(&u8g, 0, 15, s);
	char s1[] = "CO/VOC:   ppm";	
	s1[7] = (int)0;
	s1[8] = (int)9;
	s1[9] = (int)9;
	u8g_DrawStr(&u8g, 0, 45, s1);

}
int32_t g_temp;
static void timer1_isr(void *ptr)
{
	timer_int_clear(TIMER_1);
	int32_t temp1;
	uint16_t pm;
	int32_t temp_val;

	if (temp_sensor_read(&temp_val) == E_OK)
	{
		temp1 = temp_val;
		g_temp = temp_val;
		EMBARC_PRINTF("temp is %d\n", temp1);
	}
	else
	{
		EMBARC_PRINTF("Unable to read temperature sensor value, please check it!\r\n");
	}
	u8g_FirstPage(&u8g);
	do {
		draw(temp1,g_temp);
	} while (u8g_NextPage(&u8g));
}


/** main entry */
int main(void)
{
	uint32_t baudrate = 115200;
	int32_t ercd;
	cpu_lock();
	board_init();
	my_emsk_uart_init();
	int count = 0;
	char message[4];

	ercd = temp_sensor_init(BOARD_TEMP_I2C_SLAVE_ADDRESS);
	my_emsk_iic_init(iic_slvaddr);
	EMBARC_PRINTF("Part 3 \n");
	uint8_t config[2];
	config[0] = 0x08; 
	config[1] = 0x10; 
	iic_0->iic_write(config, 2);
	EMBARC_PRINTF("Part 4 \n");
	config[0] = 0x08; 
	config[1] = 0x70; 
	iic_1->iic_write(config, 2);

	if (ercd != E_OK) {
		EMBARC_PRINTF("Temperature sensor open failed\r\n");
	}
	int_disable(INTNO_TIMER1);
	timer_stop(INTNO_TIMER1);
	int_handler_install(INTNO_TIMER1, timer1_isr);
	int_enable(INTNO_TIMER1);
	timer_start(TIMER_1, TIMER_CTRL_IE, BOARD_CPU_CLOCK);
	cpu_unlock();
	u8g_InitComFn(&u8g, &u8g_dev_ssd1306_128x64_2x_i2c, U8G_COM_SSD_I2C);
	u8g_Begin(&u8g);
	u8g_prepare();
	while (1)
	{
		my_emsk_uart_init();
		uart->uart_write("\x1b[j", 3);
		uart->uart_write("Value=", 6);
		message[0] = 0;
		message[1] = 0;
		message[2] = 0;
		message[3] = 0;
		sprintf(message, "%4d", g_temp);
		uart->uart_write(message, 4);
		count++;
		board_delay_ms(100, 1);
		
	}
	return E_SYS;
}

void my_emsk_uart_init(void)
{
	uart = uart_get_dev(DW_UART_0_ID);

	uart->uart_open(UART_BAUDRATE_9600);

error_exit:
	return;
}

int32_t my_emsk_iic_init(uint32_t slv_addr)
{
	int32_t ercd = E_OK;

	iic_0 = iic_get_dev(DW_IIC_0_ID);

	EMSK_IIC_CHECK_EXP_NORTN(iic_0 != NULL);

	ercd = iic_0->iic_open(DEV_MASTER_MODE, IIC_SPEED_HIGH);
	if ((ercd == E_OK) || (ercd == E_OPNED)) {
		ercd = iic_0->iic_control(IIC_CMD_MST_SET_TAR_ADDR, CONV2VOID(slv_addr));
		iic_slvaddr = slv_addr;
	}

	iic_1 = iic_get_dev(DW_IIC_1_ID);

	EMSK_IIC_CHECK_EXP_NORTN(iic_1 != NULL);

	ercd = iic_1->iic_open(DEV_MASTER_MODE, IIC_SPEED_HIGH);
	if ((ercd == E_OK) || (ercd == E_OPNED)) {
		ercd = iic_1->iic_control(IIC_CMD_MST_SET_TAR_ADDR, CONV2VOID(slv_addr));
		iic_slvaddr = slv_addr;
	}
error_exit:
	return ercd;
}


/** @} */
