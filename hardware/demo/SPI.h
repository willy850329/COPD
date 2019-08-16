#ifndef __SPI_H_
#define __SPI_H_

int32_t cpld_spi_init(void);
int32_t spi_read_qei(void *data, int len);
int32_t spi_write_pwm(uint8_t *data, int len);
int32_t spi_open(void);
int32_t int_open(void);
#endif