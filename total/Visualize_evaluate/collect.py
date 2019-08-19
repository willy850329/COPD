from bluepy import btle
import struct
import threading
import binascii
import time
import sys
import myOpenGL
from numpy import *
import numpy as np 
import pickle
import select
import collections 
import Madgwick
import Mahony
import scipy.interpolate
import os
import QTRealLine
from ctypes import c_bool
from multiprocessing import Process,Array,Value, Lock
import pynput
import keyboard
from scipy.signal import butter, lfilter, freqz
import wave
from librosa import resample

imuNodeNum = 1
dongleNum = 3

acc_divider = 4095.999718
gyro_divider = 65.500002
DEG2RAD = 0.01745329251

lock = threading.Lock()
mainLock = threading.Lock()

# remove gravity parameter
alpha = 0.8

save_data_flag="notReady"
savedFileNum = 0

deviceList = []
mic_ch_1 = []
mic_ch_2 = []

axisName = ['ax','ay','az','gx','gy','gz','time','touch']
# node's parameter
class myNode(object):
    '''' a class to maintain connection and the calibration value of sensors'''
    def __init__(self):
        self.noti = None
        self.Peripheral = None
        self.accBias = [0.0,0.0,0.0]
        self.gyroBias = [0.0,0.0,0.0]
        self.magBias = [0.0,0.0,0.0]
        self.magScale = [0.0,0.0,0.0]
        self.magCalibration = [0.0,0.0,0.0]
        self.gravity = [0.0,0.0,0.0]
        self.dataDicts= []
        self.count = 0
        self.madgwick = Madgwick.MadgwickClass()
        self.mahony = Mahony.MahonyClass()
        self.nodeCube = myOpenGL.myCube(x_axis = 90)

#get rawdata from ecomini when notification
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, node):
        btle.DefaultDelegate.__init__(self)
        self.node = node

    def handleNotification(self, cHandle, data):
        self.node.noti = data

#scan
def scanThread():
    global deviceList
    iface = 1
    scanner = btle.Scanner(iface)

    while True :
        if len(deviceList) >= imuNodeNum:
            print("Devices all connected")
            return

        print("Still scanning...")
        devcies = scanner.scan(timeout = 3)

        for dev in devcies:
            if dev.addr == "88:4a:ea:77:84:e8":
                print("devcies %s (%s) , RSSI = %d dB" % (dev.addr , dev.addrType , dev.rssi))

                connNode = myNode()
                connNode.Peripheral = btle.Peripheral(dev.addr , dev.addrType , iface)
                print(connNode.Peripheral.setMTU(0xEFFF))
                connNode.Peripheral.setDelegate(MyDelegate(connNode))
                try:
                    service = connNode.Peripheral.getServiceByUUID("0000ffe0-0000-1000-8000-00805f9b34fb")
                    char = service.getCharacteristics("0000ffe1-0000-1000-8000-00805f9b34fb")[0] 
                    connNode.Peripheral.writeCharacteristic(char.handle + 2,struct.pack('<bb', 0x01, 0x00),True)
                    deviceList.append(connNode)
                except:
                    print("get service, characteristic or set notification failed")
                    break

def on_press(key):
    global saverState
    global S_time
    global isFirstpacket
    global touchData,recordDataList
    try: k = key.char # single-char keys
    except: k = key.name # other keys
    if key == pynput.keyboard.Key.esc: return False # stop listener
    if k == 'c': 
        recordDataList = [[],[],[],[],[],[],[],[]]    
        saverState.value=0
        isFirstpacket = True
        S_time=time.time()
    elif k == 's':
        print (len(recordDataList[0]))
        print(time.time()-S_time)
        time.sleep(1)
        saverState.value=1
    elif k == 'r':
        saverState.value=2
    elif k=='q':
        saverState.value=9
        sys.exit(0)
    elif k == 'z':
        saverState.value=0
        touchData = 1


def write_file():
    print ("Saving file now")
    global recordDataList
    
    jsonData = {'ax':[],'ay':[],'az':[],'gx':[],'gy':[],'gz':[],'time':[],'touch':[]}
    for key,data in zip(axisName,recordDataList):
        jsonData[key] = data
    import json
    with open(str(time.time())+'.json','w') as fp:
        json.dump(jsonData,fp)
    recordDataList = [[],[],[],[],[],[],[],[]]
    print ("Save file")





def eliminate_gravity(node, value):

    node.gravity[0] = alpha*node.gravity[0] + (1-alpha)*value[0]
    node.gravity[1] = alpha*node.gravity[1] + (1-alpha)*value[1]
    node.gravity[2] = alpha*node.gravity[2] + (1-alpha)*value[2]

    return value[0]-node.gravity[0], value[1]-node.gravity[1], value[2]-node.gravity[2]



def dataCalibration(rawdata, i=0): 
    acc = [None]*3
    acc[0] = rawdata[0]/acc_divider - node.accBias[0]
    acc[1] = rawdata[1]/acc_divider - node.accBias[1]
    acc[2] = rawdata[2]/acc_divider - node.accBias[2]

    gyro = [None]*3
    gyro[0] = (rawdata[3]/gyro_divider - node.gyroBias[0])*DEG2RAD
    gyro[1] = (rawdata[4]/gyro_divider - node.gyroBias[1])*DEG2RAD
    gyro[2] = (rawdata[5]/gyro_divider - node.gyroBias[2])*DEG2RAD

    # secondData = rawdata[7] & (~0xC000)
    secondData = rawdata[9] / 1000000.0

    return [acc[0],acc[1],acc[2],gyro[0],gyro[1],gyro[2],secondData]

def Uint4Toshort(tenData):
    #print(threeData)
    retVal =[]
    
    for idx, data in enumerate(tenData):
        i = 0
        byteArray = []
        while(i != 4):
            byteArray.append(int(data[i:i+2], 16))
            i=i+2

        b = ''.join(chr(i) for i in byteArray)
        if idx == 9:
            retVal.append(struct.unpack('<H',b)[0])
        else:
            retVal.append(struct.unpack('<h',b)[0])
    return retVal

#mag
def Uint8Tofloat(threeData):
    retVal =[]
    
    for data in threeData:
        i = 0
        byteArray = []
        while(i != 8):
            byteArray.append(int(data[i:i+2], 16))
            i=i+2

        b = ''.join(chr(i) for i in byteArray)
        retVal.append(struct.unpack('<f',b)[0])
    return retVal




def QTRun(plotMyData,plot1,plot2,plot3,plot4,plot5,plot6,dataLengthList,Timestamp,Idx,resetFlag,isStatic): 

    data=[[],[],[],[],[],[]]
    windowsLen = []
    while True:
        tEnd = time.time()
        while isStatic.value == True: 
            pass
        if  resetFlag.value == True:
            plotMyData.ResetGraph()
            resetFlag.value = False
        endIdx = Idx.value
        data[0]= plot1[0:endIdx]
        data[1]= plot2[0:endIdx]
        data[2]= plot3[0:endIdx]
        data[3]= plot4[0:endIdx]
        data[4]= plot5[0:endIdx]
        data[5]= plot6[0:endIdx]
        windowsLen.append([0,1])
        windowsLen.append([0,1])
        windowsLen.append([0,1])
        isStatic.value = True
        
        plotMyData.setMyData(data,windowsLen)            
        data=[[],[],[],[],[],[],[]]
        windowsLen = []

def QTWebCam(plotMyData,plot1,plot2,plot3,plot4,plot5,plot6,Timestamp,isCapturing,isStatic,resetFlag): 

    data=[[],[],[],[],[],[],[]]
    windowsLen = []
    while True:
        tStart = time.time() 
        while isStatic.value == True: 
            pass
        if  resetFlag.value == True:
            plotMyData.ResetGraph()
            resetFlag.value = False
        endIdx = Idx.value
        data[0]= plot1[0:endIdx]
        data[1]= plot2[0:endIdx]
        data[2]= plot3[0:endIdx]
        data[3]= plot4[0:endIdx]
        data[4]= plot5[0:endIdx]
        data[5]= plot6[0:endIdx]
        data[6]= Timestamp[0:endIdx]
        


        plotMyData.setMyData(data,isCapturing.value)              
        data=[[],[],[],[],[],[],[],[]]
        windowsLen = []
        tStart = time.time() 
        isStatic.value = True

def get_bias():
    '''Get bias data of acc and gyro'''
    for i in range(3):
        node.gyroBias[i]=0
        node.accBias[i]=0
    calibrationCount = 0
    while(calibrationCount!=CALIBRATIONTIMES):
        if node.Peripheral.waitForNotifications(0.05):
            rawdata = node.noti
            calibrationCount+=1
            for i in range(3):
                node.accBias[i]+=rawdata[i]
                node.gyroBias[i]+=rawdata[i+3]
    for i in range(3):
        node.accBias[i]=(node.accBias[i]/acc_divider)/CALIBRATIONTIMES
        node.gyroBias[i]=(node.gyroBias[i]/gyro_divider)/CALIBRATIONTIMES
    print ("accBias: ",node.accBias)
    print ("gyroBias: ",node.gyroBias)
    print (calibrationCount)
    print ('Calibration completed')

def main():
    #device address
    #targetDevice = "3c:cd:40:18:c1:04" #3c:cd:40:18:c0:4f==>waist 3c:cd:40:18:c1:04==>wrist
    global runningThreadNum,saverState,recordDataList
    global ret
    ret = np.zeros( (0,6) )
    recordDataList = [[],[],[],[],[],[],[],[]]
    scanTh =  threading.Thread(target = scanThread)
    # scanTh.setDaemon(True)
    scanTh.start()
    scanTh.join()

    runningThreadNum = 0

    #drawing parameters
    plot1 = Array('f',[0.0 for i in range(0,200)])
    plot2 = Array('f',[0.0 for i in range(0,200)])
    plot3 = Array('f',[0.0 for i in range(0,200)])
    plot4 = Array('f',[0.0 for i in range(0,200)])
    plot5 = Array('f',[0.0 for i in range(0,200)])
    plot6 = Array('f',[0.0 for i in range(0,200)])
    plot7 = Array('i',[0 for i in range(0,650)])   
    Timestamp = Array('f',[0.0 for i in range(0,200)])

    resetFlag = Value(c_bool,False)
    Idx =  Value('i',-1)
    staticFlag = Value(c_bool,True)
    isCapturing = Value(c_bool,False)
    numberOfPlot = 20
    temp = 0


    saverState = Value('i',-1)

    lis = pynput.keyboard.Listener(on_press=on_press)
    lis.start() # start to listen on a separate thread

    plotMyData = QTRealLine.MyRealTimePlot()  
    plotRealTimeData = Process(target=QTRun,args=(plotMyData,plot1,plot2,plot3,plot4,plot5,plot6,plot7,Timestamp,Idx,resetFlag,staticFlag))
    plotRealTimeData.daemon=True
    plotRealTimeData.start()
    
    global mic_ch_1
    global S_time
    global sensorStopMax
    global node,touchData
    global CALIBRATIONTIMES,isFirstpacket
    isFirstpacket=False
    CALIBRATIONTIMES = 300
    sensorStopMax = [1.252, 0.055]
    node = deviceList[0]
    touchData=0
    test_counter = 0
    calibratedData=[0.0,0.0,0.0,0.0,0.0,0.0,0]

    previous_byte = ""
    extend_sign=str(chr(0x00))
    odd_flag = False
    count = 0
    while(True):
        mic_ch_1=[]
        while count<25000:
            if node.Peripheral.waitForNotifications(1):

                # code
                rawdata = node.noti
                
                if odd_flag:
                    rawdata = previous_byte + rawdata
                
                if len(rawdata)%3 == 1:
                    previous_byte = rawdata[-1]
                    rawdata = rawdata[0:-1]
                    odd_flag = True
                elif len(rawdata)%3 == 2:
                    previous_byte = rawdata[-2:]
                    rawdata = rawdata[0:-2]
                    odd_flag = True
                else:
                    odd_flag = False    

                for i in range(0,len(rawdata), 3):
                    try:
                        #positive value
                        if(ord(rawdata[i])<=128):
                            extend_sign = str(chr(0x00))
                            #print("positive")
                        #minus value
                        else:
                            extend_sign = str(chr(0xFF))
                            #print("negative")
                        #print(extend_sign+rawdata[i:i+3])

                        #print(struct.unpack('>l',extend_sign+rawdata[i:i+3])[0])
                        calibratedData[0]=struct.unpack('>l',extend_sign+rawdata[i:i+3])[0]
                        #print(calibratedData[0])
                        #print(struct.unpack('<l',zero+rawdata[i:i+3])[0])
                        mic_ch_1.append(struct.unpack('>l',extend_sign+rawdata[i:i+3])[0])
                        
                        count = count + 1
                        #print(count)
                    except:
                        print("Packet Loss")

                #keyboard
                if saverState.value == 2:
                    saverState.value = -1
                if saverState.value == 0:
                    if(isFirstpacket):
                        isFirstpacket = False
                        print ('start record')
                        continue
                    for i in range(3):
                        recordDataList[i].append(calibratedData[i])
                        recordDataList[i+3].append(calibratedData[i+3])
                    if keyboard.is_pressed('z'):
                        touchData = 1
                    else:
                        touchData = 0
                    recordDataList[6].append(calibratedData[6])
                    recordDataList[7].append(touchData)
                if saverState.value == 1:
                    saverState.value = -1
                    # saveProcess = threading.Thread(target = write_file)
                    # saveProcess.start()
                    # saveProcess.join()
                if saverState.value == 9:
                    sys.exit(0)
                plotData = np.asmatrix(calibratedData[:-1])
                ret = np.concatenate( (ret,plotData),axis=0 )      
                if plotData.shape[0] != 0 :            
                        if ret.shape[0] == numberOfPlot:
                            ret = ret.transpose()
                            # print ret
                            plot1[0:numberOfPlot] = ret[0,:].tolist()[0]
                            plot2[0:numberOfPlot] = ret[1,:].tolist()[0]
                            plot3[0:numberOfPlot] = ret[2,:].tolist()[0]
                            plot4[0:numberOfPlot] = ret[3,:].tolist()[0]
                            plot5[0:numberOfPlot] = ret[4,:].tolist()[0]
                            plot6[0:numberOfPlot] = ret[5,:].tolist()[0]
                            Idx.value = numberOfPlot
                            staticFlag.value = False
                            ret = np.zeros( (0,6) )
            else:
                previous_byte = ""
                print("No packet")
        tranfer_to_WAV()
        print("Create new sound file")
        count = 0

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def tranfer_to_WAV():
    global mic_ch_1
    global mic_ch_2
    lowcut = 10.0
    fs = 1000.0
    highcut = 499.0
    
    mic_ch_2 = mic_ch_1
    mic_ch_2 = butter_bandpass_filter(mic_ch_2, lowcut, highcut, fs, order=5)
    mic_ch_2=np.array(mic_ch_2)

    #print("before:", np.size(mic_ch_2))
    mic_ch_2 = resample(mic_ch_2, 1000, 44100)
    #print("after:", np.size(mic_ch_2))

    max_ch2=max(mic_ch_2)
    min_ch2=min(mic_ch_2)
    mic_ch_2=mic_ch_2*(65535.0/abs(max_ch2-min_ch2))

    wave_data=mic_ch_2
    wave_data = wave_data.astype(np.short)
    f = wave.open("./Visualize_evaluate/soundfile/sound.wav", "wb")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    f.writeframes(wave_data.tostring())
    f.close()

if __name__ == '__main__':
	main()