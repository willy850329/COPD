/* ------------------------------------------
 * Copyright (c) 2019, Synopsys, Inc. All rights reserved.

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


#include "embARC.h"
#include "embARC_debug.h"

#include "adt7420.h"
#include "u8g.h"
#include "SPI.h"

#include <stdio.h>
#include <stdlib.h>

#define TEMPERATURE_ADDRESS  TEMP_I2C_SLAVE_ADDRESS

static DEV_IIC *iic;
static DEV_UART *uart;
static ADT7420_DEF *ADT7420;
u8g_t u8g;

char message[21]={0};
char s1[] = "Temperature:  . C";
char s2[] = "CO/VOC:   ppm";	

float tmpval=0;
int air_val=0;

uint8_t config[1];
uint8_t data[2];
uint8_t sound_data[3];

uint32_t val_time;
uint32_t spi_check =0xFFFF;
uint32_t audio_counter = 0;
static uint32_t iic_slvaddr = 0x28;

/** emsk on-board uart init */
void my_emsk_uart_init(void)
{
	uart = uart_get_dev(DW_UART_0_ID);
	int32_t check2 = uart->uart_open(UART_BAUDRATE_230400);
error_exit:
	return;
}

void my_emsk_temperature(){
	
	ADT7420 = malloc(sizeof(ADT7420_DEF));
	
	ADT7420->i2c_id = DW_IIC_1_ID;
	ADT7420->slvaddr = TEMPERATURE_ADDRESS;
	ADT7420->resolution = ADT7420_RESOLUTION_16BIT;
	
	int32_t Check_tmp = adt7420_sensor_init(ADT7420);
	
	
	if(Check_tmp==E_OK){
		EMBARC_PRINTF("ADT7420 init success\n");
	}else{
		EMBARC_PRINTF("ADT7420 init failed\n");
	}
	
error_exit:
	return;
}

int32_t my_emsk_iic_init(uint32_t slv_addr)
{
	int32_t ercd = E_OK;
	
	iic = iic_get_dev(DW_IIC_1_ID);
	if(iic!=NULL){
		printf("Get device successfully\n");
	}
	
	ercd = iic->iic_open(DEV_MASTER_MODE, IIC_SPEED_FAST);
	if ((ercd == E_OK) || (ercd == E_OPNED)) {
		ercd = iic->iic_control(IIC_CMD_MST_SET_TAR_ADDR, CONV2VOID(slv_addr));
		//printf("I2C open\n");
	}

error_exit:
	return ercd;
}

void gpio_ISR(){
	spi_read_qei(sound_data, 3);

	//printf("%x%x%x\n",sound_data[0],sound_data[1],sound_data[2]);
	//sound_data[0] = 0x30;
	//sound_data[1] = 0x31;
	//sound_data[2] = 0x32;

	if(audio_counter>=5){
		memcpy(message+audio_counter*3, sound_data, 3);
		my_emsk_uart_init();
		uart->uart_write(message, 18);
		audio_counter = 0;
	}else{
		memcpy(message+audio_counter*3, sound_data, 3);
		audio_counter += 1;
	}

}

void u8g_prepare(void)
{
	u8g_SetFont(&u8g, u8g_font_7x14B);
	u8g_SetFontRefHeightExtendedText(&u8g);
	u8g_SetDefaultForegroundColor(&u8g);
	u8g_SetFontPosTop(&u8g);
}

/* Air function */
int32_t air_read(uint8_t *val){
	int32_t ercd = E_PAR;
	DEV_IIC_PTR iic = iic_get_dev(DW_IIC_1_ID);
	uint8_t air_addr[1];
	air_addr[0] = 0x28;
	iic->iic_control(IIC_CMD_MST_SET_TAR_ADDR, CONV2VOID(iic_slvaddr));
	/** write register address then read register value */
	ercd = iic->iic_control(IIC_CMD_MST_SET_NEXT_COND, CONV2VOID(IIC_MODE_RESTART));
	//ercd = iic->iic_write(air_addr[0], 1);
	ercd = iic->iic_control(IIC_CMD_MST_SET_NEXT_COND, CONV2VOID(IIC_MODE_STOP));
	ercd = iic->iic_read(val, 2);

error_exit:
	return ercd;
}

static void timer1_isr(void *ptr)
{
	timer_int_clear(TIMER_1);
	/* Temperature */
	int ten_tmp, one_tmp;
	adt7420_sensor_read(ADT7420, &tmpval);
	ten_tmp = (int)(tmpval/10.0);
	s1[12] = ten_tmp + 48;
	one_tmp = (int)((tmpval*1.0) - ten_tmp*10);
	s1[13] = one_tmp + 48;
	s1[15] = (int)((tmpval*10.0) - 100*ten_tmp - 10*one_tmp) + 48;
	
	/* Air */
	air_read(data);
	air_val = ((uint16_t)data[0] << 8) + ((uint16_t)data[1]);
	air_val = ((990*air_val)/4095) + 10;
	s2[7] = air_val/100 + 48;
	s2[8] = (air_val%100)/10 + 48;
	s2[9] = air_val%10 + 48;
	
	
	u8g_FirstPage(&u8g);
	do {
		u8g_DrawStr(&u8g, 0, 15, s1);
		u8g_DrawStr(&u8g, 0, 45, s2);
	} while (u8g_NextPage(&u8g));
	//printf("Temperature = %f\n", tmpval);
	//printf("Air int = %d\n",air_val);
	//printf("Air 16 bit= %x%x\n",data[0],data[1]);
}

/** main entry */
int main(void)
{		

	/* Temperature I2C */
	my_emsk_temperature();
	
	/* Air I2C */
	int32_t ercd = my_emsk_iic_init(iic_slvaddr);
	if(ercd==E_OK){
		printf("Control device successfully(Address = 0x28)\n");
	}
	config[0] = 0x10;
	iic->iic_write(config,1);
	
	/* U8G */
	u8g_InitComFn(&u8g, &u8g_dev_ssd1306_128x64_2x_i2c, U8G_COM_SSD_I2C);
	u8g_Begin(&u8g);
	u8g_prepare();
	
	/* Timer interrupt */
	cpu_lock();
	board_init();
	cpu_unlock();
	
	if(timer_present(TIMER_1)){
		printf("TIMER0");
		timer_current(TIMER_1, &val_time);
		printf("cnt:%d\n", val_time);
		
		int_handler_install(INTNO_TIMER1, timer1_isr);
		int_enable(INTNO_TIMER1);
		timer_start(TIMER_1, TIMER_CTRL_IE, 20000000);
	}
	
	//UART
	my_emsk_uart_init();
	
	/* SPI 24bit ADS1256 */
	spi_check = cpld_spi_init();
	int_open();
	
	if(spi_check==E_OK){
		printf("Success to open SPI\n");	
	}
	
	uint8_t sss[1]={0x0F};
	spi_write_pwm(&sss[0],1);
	//uint8_t sps_con[3]={0x53,0x00,0xA1};????
	uint8_t sps_con[3]={0x53,0x01,0xA1};
	spi_write_pwm(&sps_con[0],3);
	
	uint8_t rc = 0x03;
	spi_write_pwm(&rc,1);
	printf("Success SPI command\n");
	
	
	
	while(1){
	}
	
	return E_SYS;
}
