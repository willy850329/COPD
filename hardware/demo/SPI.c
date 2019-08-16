#include "embARC.h"
#include "embARC_debug.h"
#include "spi.h"

#include <stdio.h>
#include <stdlib.h>

#define SPI_ID  DW_SPI_0_ID
//CS
#define CS_PORT	DEV_GPIO_PORT_C
#define CS_PIN  DEV_GPIO_PIN_28
#define CS_MASK 1<<CS_PIN
//INT for DRDY
#define INT_PORT DEV_GPIO_PORT_A
#define INT_PIN  DEV_GPIO_PIN_28
#define INT_MASK 1<<INT_PIN

static DEV_SPI*  spi;
static DEV_GPIO_BIT_ISR gpio_isr_handler;
static DEV_GPIO* gpio;
static DEV_GPIO_INT_CFG gpio_config;
static DEV_GPIO* gpio_for_DRDY;
extern void gpio_ISR();

int32_t spi_open(void)
{
	int32_t ercd = 0;

	spi = spi_get_dev(SPI_ID);
	
	/*spi frequence:2M*/
	ercd = spi->spi_open(DEV_MASTER_MODE, 1000000);

	if (ercd != E_OK && ercd != E_OPNED) {
		return ercd;
	}

	/*
	 * Set designware spi device data frame size:16 bits
	 * However struct dev_spi_transfer tx_buf,rx_buf -> uint8_t
	 * it doesn't work as expected
	 */
	//spi->spi_control(SPI_CMD_SET_DFS, CONV2VOID(16));
	spi->spi_control(SPI_CMD_SET_CLK_MODE, CONV2VOID(SPI_CPOL_0_CPHA_1));
	
	//spi->spi_control(SPI_CMD_SET_DUMMY_DATA, CONV2VOID(0x00));

	
	
	return E_OK;
}

int32_t gpio_open(void)
{
	
	int32_t ercd = 0;
	//CS:start
	gpio = gpio_get_dev(CS_PORT);
	
	//configASSERT(gpio != NULL);
	
	ercd = gpio->gpio_open(CS_MASK);
	if (ercd == E_OPNED) {
		gpio->gpio_control(GPIO_CMD_SET_BIT_DIR_OUTPUT, (void *)(CS_MASK));
		
	}
	//CS:end
	

	//INT:end
	return E_OK;
}

int32_t int_open(void){
	int32_t ercd = 0;
		//INT:start
	gpio_for_DRDY = gpio_get_dev(INT_PORT);

	ercd = gpio_for_DRDY->gpio_open(INT_MASK);
	if (ercd == E_OPNED) {
		gpio_for_DRDY->gpio_control(GPIO_CMD_SET_BIT_DIR_INPUT, (void *)(INT_MASK));
		
		//printf("ACTIVE_LOW = %d, FALLING_EDGE = %d, INT_ACTIVE_HIGH = %d, RISING_EDGE = %d\n",GPIO_INT_ACTIVE_LOW, GPIO_INT_FALLING_EDGE, GPIO_INT_ACTIVE_HIGH, GPIO_INT_RISING_EDGE);
		/*
		config
		*/
		gpio_config.int_bit_mask = INT_MASK;
		gpio_config.int_bit_type = 0x10000000;
		gpio_config.int_bit_polarity = 0;//why active low == falling edge dev_gpio wrong?
		gpio_config.int_bit_debounce = GPIO_INT_DEBOUNCE;
		gpio_for_DRDY->gpio_control(GPIO_CMD_SET_BIT_INT_CFG, &gpio_config);
		
		/*
		gpio_isr_handler : dev_gpio.h 367 lines
		int_bit_ofs
		int_bit_handler : interrupt handler
		*/
		gpio_isr_handler.int_bit_handler = gpio_ISR;
		gpio_isr_handler.int_bit_ofs = INT_PIN;
		
		/*
		gpio_control : dev_gpio.h 448 lines
		GPIO_CMD_SET_BIT_ISR : dev_gpio.h 215 lines
		(DEV_GPIO*)gpio_for_DRDY : dev_gpio.h 417 lines
		*/
		gpio_for_DRDY->gpio_control(GPIO_CMD_SET_BIT_ISR, &gpio_isr_handler);
		gpio_for_DRDY->gpio_control(GPIO_CMD_ENA_BIT_INT, (void *)(INT_MASK));
	}
	return E_OK;
}

/*
 * \brief	open spi interface, use J6 spi0 (CS0)
 * \retval	0	success
 * \retval	-1	fail
 */

int32_t cpld_spi_init(void)
{
	int32_t ercd = 0;

	ercd = spi_open();
	if (ercd != E_OK) {
		printf("something happen1");
		return ercd;
	}

	ercd = gpio_open();
	if (ercd != E_OK) {
		printf("something happen2");
		return ercd;
	}
	printf("something happen2\n");
	/* write 1 to CS pin, pull-up */
	//ercd = spi->spi_control(SPI_CMD_MST_SEL_DEV, CONV2VOID(EMSK_SPI_LINE_0));
	gpio->gpio_write(CS_MASK, CS_MASK);
	
	if(ercd != E_OK){
		printf("something happen3");
	}
	return E_OK;
}

static void spi_select(void)
{
	/*select spi slave device*/
	spi->spi_control(SPI_CMD_MST_SEL_DEV, CONV2VOID(EMSK_SPI_LINE_0));
	/* write 0 to CS pin, pull-down */
	gpio->gpio_write((~(CS_MASK)), CS_MASK);
}

static void spi_deselect(void)
{ 
	/* write 1 to CS pin, pull-up */
	gpio->gpio_write(CS_MASK, CS_MASK);
	/*deselect spi slave device*/
	spi->spi_control(SPI_CMD_MST_DSEL_DEV, CONV2VOID(EMSK_SPI_LINE_0));
}

/*
 * \brief	read qei[2](16bits)(continuous 2x8bits)
 * \param   array to store data
 * \retval  spi status
 */

int32_t spi_read_qei(void *data, int len)
{
	int32_t ercd = 0;

	DEV_SPI_TRANSFER xfer;

	DEV_SPI_XFER_SET_TXBUF(&xfer, NULL, 0, 0);
	DEV_SPI_XFER_SET_RXBUF(&xfer, data, 0, len);
	DEV_SPI_XFER_SET_NEXT(&xfer, NULL);

	spi_select();

	ercd = spi->spi_control(SPI_CMD_TRANSFER_POLLING, CONV2VOID(&xfer));
	spi_deselect();
	return ercd;
}

/*
 * \brief	
 			Format:
 			-----------------------------------------
 			  L  |      data[0]        |   data[1]
 			-----|---------------------|--------------
 				 | pwm_l | (pwm[0].hi) | (pwm[1].lo)
			-----|---------------------|--------------
 			  R  |      data[0]        |   data[1]
 			-----|---------------------|--------------
 				 | pwm_r | (pwm[1].hi) | (pwm[2].lo)	
 			-----------------------------------------
 * \param   array to transfer
 * \retval  spi status
 */

int32_t spi_write_pwm(uint8_t *data, int len)
{
	int32_t ercd = 0;
	
	DEV_SPI_TRANSFER xfer;
	
	DEV_SPI_XFER_SET_TXBUF(&xfer, data, 0, len);
	DEV_SPI_XFER_SET_RXBUF(&xfer, NULL, len, 0);
	DEV_SPI_XFER_SET_NEXT(&xfer, NULL);

	spi_select();

	ercd = spi->spi_control(SPI_CMD_TRANSFER_POLLING, CONV2VOID(&xfer));
	
	spi_deselect();

	return ercd;

}