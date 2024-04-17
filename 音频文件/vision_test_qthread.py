from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time
import threading
import cv2 as cv
import numpy as np
import random   #导入随机数模块
import pyaudio  #导入音频模块
import wave    #导入音频读写模块
from aip import AipSpeech
from playsound import playsound
#录音相关的参数
CHUNK = 16
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORE_SEDCONDS = 3
WAVE_OUTPUT_FILENAME = "/home/pi/test/语音识别文件/test_video.wav"
#######
##语音识别相关
''' 你的APPID AK SK  参数在申请的百度云语音服务的控制台查看'''
APP_ID = '25861395'
API_KEY = 'gl8XFDiZypmaP4siBC1LTOvp'
SECRET_KEY = 'Bn51PdCp7pDGud88RjMeLhB2SSvaKcGW'

# 新建一个AipSpeech
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
##语音识别相关
# 继承QThread
class Vision_Test_Thread(QThread):  # 线程1
    _signal = pyqtSignal(QImage)
    sight_signal = pyqtSignal(int,int) #发送最终的视力值
    voice_signal = pyqtSignal(int)
    def __init__(self,distance):
        super().__init__()
        self.proportion = 500./distance
        self.thd_on = 1
        self.eyes = 0 #0表示测试的是左眼  1表示测试的是左眼
        self.left_sight = 40 #表示左眼视力为4.0
        self.right_sight = 40 #表示右眼视力为4.0
        self.test_sight = 45 #表示从4.5开始测试
        self.result_flag = 0
        self.test_result = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        self.list = ['上','下','左','右']   #标明取出的为上下左右
        self.dir = 0  #表明目前所指示的方向
        self.str = "" #表明视力图片文件路径
        #录音相关
        
    def run(self):
        self.voice_signal.emit(0)
        time.sleep(2.5)
        #playsound("/home/pi/test/音频文件/请闭上你的左眼/请闭上你的左眼.wav",block=True)
        while (self.eyes==0): #表明程序进行并且测试的是左眼
            self.test_result[self.test_sight-40] = 0
            self.list = ['上','下','左','右']
            self.random = random.randint(0,3)
            #self.list = self.list.remove(self.random)
            del self.list[self.random]
            for i in range(3):
                while(self.thd_on==0):
                    time.sleep(0.5)
                print(self.list[i])
                self.str = '/home/pi/test/视力检测E/视力检测E'+str(self.test_sight)+'树莓派.jpg'
                self.image = cv.imread(self.str)
                #print(np.array(self.image).shape)
                self.image_zoom_rows, self.image_zoom_cols = self.image.shape[:2]
                print(self.image_zoom_rows, self.image_zoom_cols)
                #print(self.list[i])
                if(self.list[i] == '上'):
                    self.image = cv.transpose(self.image)
                    self.image = cv.flip(self.image,0)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), -90, self.proportion)
                elif self.list[i] == '下':
                    self.image = cv.transpose(self.image)
                    #self.image = cv.flip(self.image,0)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), 90, self.proportion)
                elif self.list[i] == '左':
                    self.image = cv.flip(self.image, 1)
                    #self.image = cv.transpose(self.image)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), 180, self.proportion)
                else:
                    pass
                #cv.imshow("xuan",self.image)
                #print(np.array(self.image).shape)
                self.image = cv.resize(self.image,(int(self.image_zoom_rows/self.proportion),int(self.image_zoom_cols/self.proportion)))
                self.image_rows, self.image_cols, self.image_channels = self.image.shape
                self.bytesPerLine = self.image_channels * self.image_cols
                QImg = QImage(self.image.data, self.image_cols, self.image_rows, self.bytesPerLine, QImage.Format_RGB888)
                self._signal.emit(QImg)
                time.sleep(1.5)
                #playsound("/home/pi/test/音频文件/请说出视标方向/请说出视标方向.wav",block=True)
                print("开始录音")
                #录音
                self.voice_record()
                print("录音结束")
                #录音结束
                if(self.stt(WAVE_OUTPUT_FILENAME)==self.list[i]):#识别正确
                    self.test_result[self.test_sight-40]=self.test_result[self.test_sight-40]+1                    
                    print("正确")
                else:
                    print("错误")
                time.sleep(0.2)  # 休眠
                print(self.test_result)
            for i in range(13):
                if(self.test_result[i]>=2 and 0<=self.test_result[i+1]<2):
                    self.result_flag = 1
                    self.left_sight = i+40
                    break
                else:
                    self.result_flag = 0
            if(self.result_flag):
                break
            else:
                if(self.test_result[self.test_sight-40]>=2):
                    self.test_sight=self.test_sight+1
                    
                else:
                    self.test_sight=self.test_sight-1
            print(self.test_sight)
            if(self.test_sight>54):
                self.left_sight=54
                break
            elif(self.test_sight<40):
                self.left_sight=40
                break
            else:
                pass
        self.eyes=1
        self.test_sight = 45 #表示从4.5开始测试
        self.result_flag = 0
        self.test_result = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]
        self.voice_signal.emit(1)
        print(self.result_flag)
        self.voice_signal.emit(1)
        time.sleep(2.5)
        #playsound("/home/pi/test/音频文件/请闭上你的左眼/请闭上你的右眼.wav",block=True)        
        while (self.eyes==1): #表明程序进行并且测试的是左眼
            self.test_result[self.test_sight-40] = 0
            self.list = ['上','下','左','右']
            self.random = random.randint(0,3)
            #self.list = self.list.remove(self.random)
            del self.list[self.random]
            for i in range(3):
                #print(self.list[i])
                while(self.thd_on==0):
                    time.sleep(0.5)
                self.str = '/home/pi/test/视力检测E/视力检测E'+str(self.test_sight)+'树莓派.jpg'
                self.image = cv.imread(self.str)
                #print(np.array(self.image).shape)
                self.image_zoom_rows, self.image_zoom_cols = self.image.shape[:2]
                #print(self.list[i])
                if(self.list[i] == '上'):
                    self.image = cv.transpose(self.image)
                    self.image = cv.flip(self.image,0)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), -90, self.proportion)
                elif self.list[i] == '下':
                    self.image = cv.transpose(self.image)
                    #self.image = cv.flip(self.image,0)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), 90, self.proportion)
                elif self.list[i] == '左':
                    self.image = cv.flip(self.image, 1)
                    #self.image = cv.transpose(self.image)
                    #self.image = cv.getRotationMatrix2D((self.image_zoom_rows//2, self.image_zoom_cols//2), 180, self.proportion)
                else:
                    pass
                #cv.imshow("xuan",self.image)
                #print(np.array(self.image).shape)
                self.image = cv.resize(self.image,(int(self.image_zoom_rows/self.proportion),int(self.image_zoom_cols/self.proportion)))
                self.image_rows, self.image_cols, self.image_channels = self.image.shape
                self.bytesPerLine = self.image_channels * self.image_cols
                QImg = QImage(self.image.data, self.image_cols, self.image_rows, self.bytesPerLine, QImage.Format_RGB888)
                self._signal.emit(QImg)
                time.sleep(1.5)
                #playsound("/home/pi/test/音频文件/请说出视标方向/请说出视标方向.wav",block=True)
                print("开始录音")
                #录音
                self.voice_record()
                #录音结束
                if(self.stt(WAVE_OUTPUT_FILENAME)==self.list[i]):#识别正确
                    self.test_result[self.test_sight-40]=self.test_result[self.test_sight-40]+1
                    print("正确")
                else:
                    print("错误")
                time.sleep(0.2)  # 休眠
            for i in range(13):
                if(self.test_result[i]>=2 and 0<=self.test_result[i+1]<2 ):
                    self.result_flag = 1
                    self.right_sight = i+40
                    break
                else:
                    self.result_flag = 0
            if(self.result_flag):
                break
            else:
                if(self.test_result[self.test_sight-40]>=2):
                    self.test_sight=self.test_sight+1
                else:
                    self.test_sight=self.test_sight-1
            if(self.test_sight>54):
                self.right_sight=54
                break
            elif(self.test_sight<40):
                self.right_sight=40
                break
            else:
                pass
        self.sight_signal.emit(self.left_sight,self.right_sight)
    def pause(self):
        self.thd_on = 0
    def resume(self):
        self.thd_on = 1
    def voice_record(self):
        p = pyaudio.PyAudio()

        stream =  p.open(format=FORMAT,
                                    channels=CHANNELS,
                                    rate=RATE,
                                    input=True,
                                    frames_per_buffer=CHUNK)
        frame =[]
        for i in range(0,int(RATE/CHUNK*RECORE_SEDCONDS)):
            data=stream.read(CHUNK)
            frame.append(data)
        #print("录音结束")
        stream.stop_stream()
        stream.close()
        p.terminate()

        wf = wave.open(WAVE_OUTPUT_FILENAME,'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))     
        wf.setframerate(RATE) 
        wf.writeframes(b"".join(frame))  
        wf.close()
        #print("录音结束")
    def get_file_content(self,filePath):   #filePath  待读取文件名
        with open(filePath, 'rb') as fp:
            return fp.read()
    def stt(self,filename):
        # 识别本地文件 参数：文件  文件格式  采样频率  PID 1537
        pos = [-1,-1,-1,-1]
        result = client.asr(self.get_file_content(filename),
                            'wav',
                            16000,
                            {'dev_pid': 1537,}      # dev_pid参数表示识别的语言类型 1536表示普通话
                            )
        
        # 解析返回值，打印语音识别的结果
        if result['err_msg']=='success.':
            word = result['result'][0]       # utf-8编码
            if word!='':
                print(word)
                #print(type(word))
                pos[0] = word.rfind("上",0,len(word)-1)
                pos[1] = word.rfind("下",0,len(word)-1)
                pos[2] = word.rfind("左",0,len(word)-1)
                pos[3] = word.rfind("右",0,len(word)-1)
                max_index = pos.index(max(pos))
                if(pos[max_index]==-1):
                    return '中'
                else:
                    if (max_index==0): return '上'
                    elif (max_index==1): return '下'
                    elif (max_index==2): return '左'
                    elif (max_index==3): return '右'
                    else: return '中' #中就表示错误
            else:
                return '中'
        else:
            return '中'
