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
* [Check software environment](#check-software-environment)
	* [COPD Respiratory Sounds Classification](#first-part:copd-respiratory-sounds-classification)
		* [Method](#method)
		* [result](#result)
  * [COPD visualization](#second-part:copd-visualization)
    * [Result](#result)
* [User Manual](#user-manual)
	* [Excute the code](#Excute-the-code)
  
## Introduction
Wearable and Environmental Sensors to Enable Precision Medicine for Chronic Obstructive Pulmonary Disease(COPD).

We developed a wearable device and want to solve two problems on this project.

  First, the device will provide quantifiable physiological signal and environmental information, as an important reference for physician diagnosis. After obtaining this data, we can improve the deviation of the diagnosis caused by the patient's subjective statements at the time of the doctor's consultation.

  Second, using wearable devices can achieve the purpose of real-time monitoring and prevent the harm caused by sudden onset effectively. In addition, we may know the condition causing the COPD by the environmantal data.

### Functions
* Collect breathing sound by LM386 microphone sensor.
* Real time monitoring the physiological and environmental information, such as temperature, humidity, and VOC.
* Classify the data of breathing sound by our model.
* Once detecting COPD, our system starts to record the information in real time.



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
* [ADT7420 (Temperature)](https://www.analog.com/en/products/adt7420.html#product-overview)
* [ADS1256 (Analog-to-digital converter)](http://www.ti.com/lit/ds/sbas288k/sbas288k.pdf)
* [LM386 (Sound sensor)](https://goods.ruten.com.tw/item/show?21550300879819)
#### Hardware Connection
* Connect HM10 to J1 (UART)
* Connect SSD1306 to J2 (i2C)
* Connect PmodAD2 to J4 (i2C)
* Connect ADT7420 to J4 (i2C)
* Connect ADS1256 to J6 (SPI)
* Connect MQ135 to PmodAD2
* Connect Mic to ADS1256

  
### Software Requirements
* Install the listed python libraries by the following bash commands.
  * NUMPY 
  ```C
  	sudo pip install numpy
  ```
  * MATPLOTLIB 
  ```C
  	sudo pip install matplotlib
  ```
  * SCIPY : 
  ```C
  	sudo pip install scipy
  ```
  * SKLEARN 
  ```C
  	sudo pip install sklearn
  ```
  * Simplejson : 
  ```C
  	sudo pip install simplejson
  ```
  * eyeD3 : 
  ```C
  	sudo pip install eyed3
  ```
  * pydub : 
  ```C
  	sudo pip install pydub
  ```
  * python-tk
  ```C
  	sudo sudo apt-get install python-tk
  ```
  * ffmpeg
  ```C
  	sudo add-apt-repository ppa:jonathonf/ffmpeg-4
  	sudo apt-get install ffmpeg
  ```


## Check software environment
### First part:COPD Respiratory Sounds Classification
#### Method
![Classification System](/pics/ClassificationSystem.png)
**Training data sources**
  * [Respiratory sound database](https://www.kaggle.com/vbookshelf/respiratory-sound-database)
  * [Basics of Lung Sounds](https://www.easyauscultation.com/course-contents?courseid=201)
  * [R.A.L.E Repository](http://www.rale.ca/Default.htm)
#### Result
To demonstrate our result of COPD respiratory sounds classification, please follow the instructions below.
##### step 1 : Make sure libraries mentioned in [Software Requirements](software-requirements) have already installed.
##### step 2 : Go to "scripts" folder : ../software/scripts.
##### step 3 : Run the demo shell script by bash command : *sh demo.sh*.
After running step 3, you will see the information on your terminal as shown in the picture below.
![Software demo](/pics/softwareDemo.png)
**As you can see, 23 of 25 COPD breathing sound data contained in the COPD_test folder are correctly determined as COPD class by our model. The accuracy is roughly 92%, and we will use this model to analyze the data acquired by EMSK**

### Second part:COPD visualization
#### Environment setting
* If you don't have git
```C
  sudo apt install git
```
* Install the listed python libraries by the following bash commands.
  * bluepy 
    * If fail, you can go to their webside. 
      https://github.com/IanHarvey/bluepy
  ```C
  	sudo apt-get install git build-essential libglib2.0-dev
    git clone https://github.com/IanHarvey/bluepy.git
    cd bluepy
    python setup.py build
    sudo python setup.py install
  ```
  * OpenGL.GL 
  ```C
  	sudo apt-get install python python-numpy python-opengl python-qt4 python-qt4-gl
  ```
  * scipy
  ```C
  	sudo pip install scipy
  ```
  * pyqtgraph.Qt
  ```C
  	sudo pip install pyqtgraph
  ```
  * pyqtgraph.Qt
  ```C
  	sudo pip install pyqtgraph
  ```
  * pytnut
  ```C
  	sudo pip install pytnut
  ```
  * keyboard
  ```C
  	sudo pip install keyboard
  ```
  * librosa 
  ```C
  	sudo pip install librosa
  ```

#### Test
1. Go to ./total/model/
```C
	>>> C:/../total/model/
```
2. Execute the ARC_evaluate python file
```C
	>>> sudo python ARC_evaluate.py
```
3. Check the connection and if any module didn't install

#### Result
![breath picture](/pics/breath.png)

## User manual
* When excuting our code, you have to becareful that
  * Must check the environment of the software part and excute successfully.
  * Must run software code and then run firmware code.

### Excute the software code
1. Go to ./total/
```C
	>>> C:/../COPD/total
```
2. Execute run.sh file
```C
	>>> sh run.sh
```
3. It will show two terminal
  * First terminal is for checking the connection and connecting the BLE4.0.
  * Second terminal is for data visualization and return the prediction of sound.
  * Beside, it will record the sound data to sound.wav in Visualize_evaluate/soundfile

### Excute the firmware code
Before running 
1. Git [embarc_osp](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_osp) to your PC or notebook.
```C
	>>> git clone https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_osp
```
2. Copy demo folder from our repository under baremental folder on your PC or notebook.
```C
	>>> C:/../embarc_osp/example/baremetal/
```
3. Use command line or terminal under demo folder
```C
	>>> cd ../embarc_osp/example/baremetal/demo
```
4. Under demo folder, use "make run" or "build .elf" to excute our code
```C
	 >>> make TOOLCHAIN=gnu BOARD=emsk BD_VER=22 CUR_CORE=arcem9d -j4 run
```