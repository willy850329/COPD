# COPD
* [Introduction](#introduction)
  * [Functions](#functions)
  * [System Architecture](#system-architecture) 
	* [Hardware System](#hardware-system)
	* [Software System](#software-system)
* [Hardware/Software Setup](#hardwaresoftware-setup)
  * [Hardware Requirements](#hardware-requirements)
  * [Software Requirements](#software-requirements)
* [Result](#result)
	* [COPD Respiratory Sounds Classification](#copd-respiratory-sounds-classification)
		* [Method](#method)
		* [Demo](#demo)
* [User Manual](#user-manual)
  
## Introduction
Wearable and Environmental Sensors to Enable Precision Medicine for Chronic Obstructive Pulmonary Disease.

This project developed a wearable vest want to solve two problems.
First, provide quantifiable physiological signal and environmental information, as an important reference for physician diagnosis and improve the patient's subjective statements at the time of the doctor's consultation to cause the deviation of the diagnosis.
Second, the use of wearable devices to achieve the purpose of real-time monitoring, effectively prevent the harm caused by sudden illness.

### Functions
* Collect breathing sound through the sensor.
* Collect environmental information for correlation analysis, such as temperature, humidity, and VOC.
* Classify the breathing sound that is collected with ARC emsk board.
* Real-time monitoring and recording the physiological and environmental when COPD occured.



### System Architecture
#### Hardware System
![Hardware system](pics/HWsystem.png)
#### Software Systm
![system overview](/pics/system.png)



## Hardware/Software Setup
### Hardware Requirements
* Hardware devices
  * [ARC EM Starter Kit](https://embarc.org/embarc_osp/doc/build/html/board/emsk.html)
  * [HM-10 BLE](http://jnhuamao.cn/bluetooth.asp?id=1)
  * SSD1306 - Adafruit
  * Pmod AD2: 4-channel 12-bit A/D Converter
  * MQ135 sensor
  * 0687A mic
  * ADT7420
  
### Software Requirements
* step1 : install the listed python libraries by the following bash commands.
  * NUMPY : *pip install numpy*
  * MATPLOTLIB : *pip install matplotlib*
  * SCIPY : *pip install scipy*
  * SKLEARN : *pip install sklearn*
  * Simplejson : *pip install simplejson*
  * eyeD3 : *pip install eyed3*
  * pydub : *pip install pydub*

### Hardware Connection
*  connect HM10 to J1 (UART)
*  connect SSD1306 to J2 (i2C)
*  connect PmodAD2 to J3 (i2C)
*  connect MQ135 to PmodAD2 V1 
*  connect Mic module to PmodAD2 V2
*  connect ADT7420 to J4 (i2C)

* step2 : 

## Demo
### COPD Respiratory Sounds Classification
#### Method
![Classification System](/pics/ClassificationSystem.png)
#### Result
To demonstrate our result of COPD respiratory sounds classification, please follow the instructions below.
##### step 1 : Make sure libraries mentioned in [Software Requirements](software-requirements) have already installed.
##### step 2 : Go to directory : ../software/scripts.
##### step 3 : Run the demo shell script by bash command : *sh demo.sh*.
## User manual
### Before Running This Application

need modify following file
(embarc_osp\board\emsk\drivers\mux\mux.c)

```C
set_pmod_mux(mux_regs, PM1_UR_UART_0 | PM1_LR_SPI_S	\
				| PM2_I2C_HRI			\
				| PM3_I2C_GPIO_D			\
				| PM4_I2C_GPIO_D		\
				| PM5_UR_SPI_M1 | PM5_LR_UART_2	\
				| PM6_UR_SPI_M0 | PM6_LR_GPIO_A );
```
### Run This Application
Here take EMSK2.2 - ARC EM7D
1. git https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_osp clone to your PC
2. add demo folder of this repository under path ../embarc_osp/example/baremetal/ (on your PC)
3. cd ../embarc_osp/example/baremetal/demo
4. make run (build .elf)
