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
        # for count packet number
        self.count = 0
        # for madgwick filter
        self.madgwick = Madgwick.MadgwickClass()
        self.mahony = Mahony.MahonyClass()
        # # for cube
        self.nodeCube = myOpenGL.myCube(x_axis = 90)
        # for packet loss handle
        # self.lossTime = -1
        # self.lastTenData = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        #                     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]

#get rawdata from ecomini when notification
class MyDelegate(btle.DefaultDelegate):
    def __init__(self, node):
        btle.DefaultDelegate.__init__(self)
        self.node = node

    def handleNotification(self, cHandle, data):
        #should not use this at release version 
        #reading =  binascii.b2a_hex(data) # transfer string to binary then using hex format to express
        #print(reading)
        #self.node.noti = Uint4Toshort([reading[0:4],reading[4:8],reading[8:12],reading[12:16],reading[16:20],reading[20:24],reading[24:28],reading[28:32],reading[32:36],reading[36:40]])
        self.node.noti = data
        #self.node.noti means rawdata without calibration from ecomini 
        #acc[x], acc[y], acc[z], gyro[x], gyro[y], gyro[z], mag[x], mag[y], mag[z], timer

#scan
def scanThread():
    global deviceList
    iface = 0
    scanner = btle.Scanner(iface)

    while True :
        if len(deviceList) >= imuNodeNum:
            print("Devices all connected")
            return
            # time.sleep(5)
            # continue

        print("Still scanning...")
        # try:
        devcies = scanner.scan(timeout = 3)

        for dev in devcies:
            if dev.addr == "88:4a:ea:77:84:e8":  #new 3c:cd:40:18:c1:5b # 3c:cd:40:0b:c0:38  #test 3c:cd:40:0b:c1:1c

                print("devcies %s (%s) , RSSI = %d dB" % (dev.addr , dev.addrType , dev.rssi))

                connNode = myNode()
                connNode.Peripheral = btle.Peripheral(dev.addr , dev.addrType , iface)
                print(connNode.Peripheral.setMTU(0xEFFF))
                connNode.Peripheral.setDelegate(MyDelegate(connNode))
                
                # gyroBias = binascii.b2a_hex(connNode.Peripheral.readCharacteristic(0x43))
                # magBias = binascii.b2a_hex(connNode.Peripheral.readCharacteristic(0x46))
                # magScale = binascii.b2a_hex(connNode.Peripheral.readCharacteristic(0x49))
                # magCalibration = binascii.b2a_hex(connNode.Peripheral.readCharacteristic(0x4C))
                # calibrationData = [accBias[0:8], accBias[8:16], accBias[16:24]]
                # connNode.accBias = Uint8Tofloat(calibrationData)
                # calibrationData = [gyroBias[0:8], gyroBias[8:16], gyroBias[16:24]]
                # connNode.gyroBias = Uint8Tofloat(calibrationData)
                # calibrationData = [magBias[0:8], magBias[8:16], magBias[16:24]]
                # connNode.magBias = Uint8Tofloat(calibrationData)
                # calibrationData = [magScale[0:8], magScale[8:16], magScale[16:24]]
                # connNode.magScale = Uint8Tofloat(calibrationData)
                # calibrationData = [magCalibration[0:8], magCalibration[8:16], magCalibration[16:24]]
                # connNode.magCalibration = Uint8Tofloat(calibrationData)
                
                # print("accBias: ",connNode.accBias)
                # print("gyroBias: ",connNode.gyroBias)
                # print("magBias: ",connNode.magBias)
                # print("magScale: ",connNode.magScale)
                # print("magCalibration: ",connNode.magCalibration)
                # print("connect successfully")

                #Try to get Service, Characteristic and set notification
                try:
                    # need to add 0000fed0-0000-1000-8000-00805f9b34fb
                    service = connNode.Peripheral.getServiceByUUID("0000ffe0-0000-1000-8000-00805f9b34fb")
                    char = service.getCharacteristics("0000ffe1-0000-1000-8000-00805f9b34fb")[0] 
                    connNode.Peripheral.writeCharacteristic(char.handle + 2,struct.pack('<bb', 0x01, 0x00),True)
                    deviceList.append(connNode)
                except:
                    print("get service, characteristic or set notification failed")
                    break
        # except:
            # print "failed scan" 
            # exit() 

def on_press(key):
    global saverState
    global S_time
    global isFirstpacket
    global touchData,recordDataList
    try: k = key.char # single-char keys
    except: k = key.name # other keys
    if key == pynput.keyboard.Key.esc: return False # stop listener
    if k == 'c': # keys interested  
        recordDataList = [[],[],[],[],[],[],[],[]]    
        saverState.value=0
        isFirstpacket = True
        S_time=time.time()
    elif k == 's': # keys interested
        print (len(recordDataList[0]))
        print(time.time()-S_time)
        time.sleep(1)
        saverState.value=1
    elif k == 'r': # keys interested
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
    #(data)
        i = 0
        byteArray = []
        while(i != 4):
            byteArray.append(int(data[i:i+2], 16))
        #print(int(data, 16))
            i=i+2

        b = ''.join(chr(i) for i in byteArray)
        if idx == 9:
            retVal.append(struct.unpack('<H',b)[0])
        else:
            retVal.append(struct.unpack('<h',b)[0])
    return retVal

#mag
def Uint8Tofloat(threeData):
    #print(threeData)
    retVal =[]
    
    for data in threeData:
    #(data)
        i = 0
        byteArray = []
        while(i != 8):
            byteArray.append(int(data[i:i+2], 16))
        #print(int(data, 16))
            i=i+2

        b = ''.join(chr(i) for i in byteArray)
        retVal.append(struct.unpack('<f',b)[0])
    return retVal




def QTRun(plotMyData,plot1,plot2,plot3,plot4,plot5,plot6,dataLengthList,Timestamp,Idx,resetFlag,isStatic): 

    data=[[],[],[],[],[],[]]
    windowsLen = []
    # print "xxxxxxxxxxxxxxxx"
    while True:
        # continue
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
        # data[3].append(plot4.value)
        # data[4].append(plot5.value)
        # data[5].append(plot6.value)
        # data[6].append(timestamp.value)
            #,isCapturing.value
        
        plotMyData.setMyData(data,windowsLen)   #isCapturing.value              
        data=[[],[],[],[],[],[],[]]
        windowsLen = []
        # tStart = time.time() 

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

    # f = open('../20k.txt','r')
    # word = []
    # for line in f.readlines():
    #     word.append(line.strip('\n'))
    # writeIndex = [i for i in range(20000)]
    # writedWord = []
    # for file in os.listdir('../data/train_word/0317/'):
    # 	writedWord.append(file[:-5])
    # for file in os.listdir('../data/train_word/0423/'):
    #     writedWord.append(file[:-5])
    # f = open('../data/train_word/')
    lis = pynput.keyboard.Listener(on_press=on_press)
    lis.start() # start to listen on a separate thread

    plotMyData = QTRealLine.MyRealTimePlot()  
    plotRealTimeData = Process(target=QTRun,args=(plotMyData,plot1,plot2,plot3,plot4,plot5,plot6,plot7,Timestamp,Idx,resetFlag,staticFlag))
    plotRealTimeData.daemon=True
    plotRealTimeData.start()
    

    global S_time
    global sensorStopMax
    global node,touchData
    global CALIBRATIONTIMES,isFirstpacket
    isFirstpacket=False
    CALIBRATIONTIMES = 300
    sensorStopMax = [1.252, 0.055]
    node = deviceList[0]   
    #get_bias()
    touchData=0
    test_counter = 0
    #We need to put the 1-D data into calibrateData[0]
    #We don't use calibratedData[1]~calibratedData[6] here
    calibratedData=[0.0,0.0,0.0,0.0,0.0,0.0,0]

    previous_byte = ""
    extend_sign=str(chr(0x00))
    odd_flag = False
    count = 0
    while count<15000:
    #while True:
        if node.Peripheral.waitForNotifications(1):
            # rawdata = node.noti
            # test_counter = test_counter + 1
            # calibratedData[0] = test_counter

            # code
            rawdata = node.noti
            #print(rawdata)
            #print(len(rawdata))
            #print(count)
            #OK
            
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
            
            #print(rawdata)
            #print(type(rawdata))
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

                    #print(struct.unpackqq('>l',extend_sign+rawdata[i:i+3])[0])
                    calibratedData[0]=struct.unpack('>l',extend_sign+rawdata[i:i+3])[0]
                    print(calibratedData[0])
                    #print(struct.unpack('<l',zero+rawdata[i:i+3])[0])
                    mic_ch_1.append(struct.unpack('>l',extend_sign+rawdata[i:i+3])[0])
                    
                    count = count + 1
                    #print(count)
                except:
                    print("Packet Loss")
            #fp.write(rawdata+"\n")
            #code end

            #keyboard
            if saverState.value == 2:
                print('ya')
            	# while(True):
             #    	idx = random.choice(writeIndex)
             #    	writeIndex.remove(idx)
             #    	if ( ('v' not in word[idx]) and ('w' not in word[idx])):
             #    		continue
             #    	if(word[idx] not in writedWord):
             #    		writedWord.append(word)
             #    		break
             #    print ("Please write %s" % (word[idx]))
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
                # if(time.time()-S_time >=5):
                # 	print (len(recordDataList[0]))
                # 	S_time=time.time()
            if saverState.value == 1:
                saverState.value = -1
                saveProcess = threading.Thread(target = write_file)
                saveProcess.start()
                saveProcess.join()
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
        	#print("Notification fail")
            #print("count:")
            #print(count)
            previous_byte = ""
            print("No packet")
    print("Collect data done")
    tranfer_to_WAV()

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
    #print(len(mic_ch_1))
    global mic_ch_1
    global mic_ch_2
    #samples_num=len(mic_ch_1)
    lowcut = 10.0
    fs = 1000.0
    highcut = 499.0
    mic_ch_1 = butter_bandpass_filter(mic_ch_1, lowcut, highcut, fs, order=5)
    mic_ch_1=np.array(mic_ch_1)

    mic_ch_2=np.array(mic_ch_2)
    
    max_ch1=max(mic_ch_1)
    min_ch1=min(mic_ch_1)
    mic_ch_1=mic_ch_1*(65535.0/abs(max_ch1-min_ch1))
    # plt.plot(mic_ch_1)
    # plt.show() 

    # plt.plot(mic_ch_2)
    # plt.show() 


    # windows=10000
    # for i in range(0,int(len(mic_ch_1)),windows):
    #     max_ch1=max(mic_ch_1[i:i+windows])
    #     min_ch1=min(mic_ch_1[i:i+windows])
    #     mic_ch_1[i:i+windows]=mic_ch_1[i:i+windows]*(50000.0/abs(max_ch1-min_ch1))
    #     #print (i)
    # for i in range(0,int(len(mic_ch_2)),windows): 
    #     max_ch2=max(mic_ch_2[i:i+windows])
    #     min_ch2=min(mic_ch_2[i:i+windows])
    #     mic_ch_2[i:i+windows]=mic_ch_2[i:i+windows]*(50000.0/abs(max_ch2-min_ch2))

  
    # plt.title("after normalize")
    # plt.plot(mic_ch_1)
    # plt.show() 

    # plt.title("after normalize")
    # plt.plot(mic_ch_2)
    # plt.show() 
    
    #DO FFT and see if there is any noise
    #fft_analysis()

    wave_data=mic_ch_1
    wave_data = wave_data.astype( np.short)
    f = wave.open("./soundfile/sound.wav", "wb")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(1000)
    #f.writeframes(np.array(interpld_ch1).tostring())
    f.writeframes(wave_data.tostring())
    f.close()

if __name__ == '__main__':
	main()

'''
question:
1. accscale? +-8g
	https://github.com/hbldh/calibraxis?fbclid=IwAR0OhqcQ0uw_pnYggVWpNtwCao3w2P6axklK_2J8zE6_pwGVzYqqnfFFTfc
2. magscale? +-500 rad/s
	https://github.com/kriswiner/MPU6050/wiki/Simple-and-Effective-Magnetometer-Calibration?fbclid=IwAR3sDTLc3IiWroQJUFNgbziquGrwK6BymMfZ84cqPD64bUVf4DHFWG2pgYs
3. how to remove gravity?
4. firmware cabli
'''
