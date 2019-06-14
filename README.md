# COPD
* [Introduction](#introduction)
  * [Functions](#functions)
  * [System Architecture](#system-architecture) 
* [Hardware/Software Setup](#hardwaresoftware-setup)
  * [Hardware Requirements](#hardware-requirements)
  * [Software Requirements](#software-requirements)
* [Demo](#demo)
* [User Manual](#user-manual)
  
## Introduction
Wearable and Environmental Sensors to Enable Precision Medicine for Chronic Obstructive Pulmonary Disease.

This project developed a wearable vest want to solve two problems.
First, provide quantifiable physiological signal and environmental information, as an important reference for physician diagnosis and improve the patient's subjective statements at the time of the doctor's consultation to cause the deviation of the diagnosis.
Second, the use of wearable devices to achieve the purpose of real-time monitoring, effectively prevent the harm caused by sudden illness.

### Functions
* Collect physiological signals through the sensor, such as breathing sound, ECG, heart rate.
* Collecting nine-axis signals through the MPU9250 for activity level recording.
* Collect environmental information for correlation analysis, such as temperature, humidity, and VOC.
* Classify the breathing sound that is collected with ARC emsk board.
* Real-time monitoring and recording the physiological and environmental when COPD occured.



### System Architecture
![system overview](/pics/system.png)

## Hardware/Software Setup
### Hardware Requirements
* Hardware devices
  * [ARC EM Starter Kit](#https://embarc.org/embarc_osp/doc/build/html/board/emsk.html)
  * MPU9250
  * 
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
## User manual
