# COPD
* [Introduction](#introduction)
  * [Functions](#functions)
  * [System Architecture](#system-architecture) 
	* [Hardware System](#hardware-system)
		* [Hardware devices](#Hardware-devices)
		* [Hardware Connection](#Hardware-Connection)
	* [Software System](#software-system)
* [Hardware/Software Setup](#hardwaresoftware-setup)
  * [Hardware Requirements](#hardware-requirements)
  * [Software Requirements](#software-requirements)
* [Demo](#demo)
	* [COPD Respiratory Sounds Classification](#copd-respiratory-sounds-classification)
		* [Method](#method)
		* [result](#result)
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
#### Hardware devices
* [ARC EM Starter Kit](https://embarc.org/embarc_osp/doc/build/html/board/emsk.html)
* [HM-10 BLE (Bluetooth)](http://jnhuamao.cn/bluetooth.asp?id=1)
* [SSD1306 - Adafruit (Screen)](https://www.adafruit.com/product/326)
	* [Library](https://github.com/adafruit/Adafruit-GFX-Library)
* [Pmod AD2: 4-channel 12-bit A/D Converter (Analog-to-digital converter)](https://store.digilentinc.com/pmod-ad2-4-channel-12-bit-a-d-converter/)
* [MQ135 sensor (Gas)](https://arduino.co.ke/product/mq135-mq-135-air-quality-sensor-hazardous-gas-detection-module-for-arduino/)
* [0687A mic (Sound)](http://www.pu-yang.com.tw/download.html)
* [ADT7420 (Temperature)](https://www.analog.com/en/products/adt7420.html#product-overview)
#### Hardware Connection
* Connect HM10 to J1 (UART)
* Connect SSD1306 to J2 (i2C)
* Connect PmodAD2 to J3 (i2C)
* Connect MQ135 to PmodAD2 V1 
* Connect Mic module to PmodAD2 V2
* Connect ADT7420 to J4 (i2C)
  
### Software Requirements
* step1 : install the listed python libraries by the following bash commands.
  * NUMPY : *pip install numpy*
  * MATPLOTLIB : *pip install matplotlib*
  * SCIPY : *pip install scipy*
  * SKLEARN : *pip install sklearn*
  * Simplejson : *pip install simplejson*
  * eyeD3 : *pip install eyed3*
  * pydub : *pip install pydub*



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
Then you would see this scene.
![Software demo](/pics/softwareDemo.png)
**As you could see, 23 of 25 COPD breathing sound datas contained in the COPD_test folder are correctly determined as COPD class by our model. The accuracy is roughly 92%, and we will use this model to analyze the data acquired by EMSK**
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
1. Git [embarc_osp](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_osp) to your PC
```C
	git clone https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_osp
```
2. Add demo folder of this repository under path ../embarc_osp/example/baremetal/ (on your PC)
3. cd ../embarc_osp/example/baremetal/demo
4. make run (build .elf)
