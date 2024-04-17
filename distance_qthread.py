from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import time
import serial

# 继承QThread
class Distance_Thread(QThread):  # 线程1
    dis_signal = pyqtSignal(int)  
    def __init__(self):
        super().__init__()
        self.thd_on = 1
        self.dis = 0
        self.ser = serial.Serial("/dev/ttyAMA0", 115200)
    def run(self):
        self.ser.write(b'\x5A\x05\x07\x01\x00') #使能输出
        while self.thd_on:
          # 获得接收缓冲区字符
            self.count = self.ser.inWaiting()
            if self.count != 0:
                # 树莓派读取电脑端发送数据，并将此数据重新发送至电脑端
                self.recv = self.ser.read(self.count)
                if(self.recv[0]==0x59 and self.recv[1]==0x59):
                    self.dis = (self.recv[3]<<8)|self.recv[2]
                else:
                    self.dis = 0
                #print(self.recv)
                #ser.write(recv)
            # 清空接收缓冲区
            self.ser.flushInput()
            self.dis_signal.emit(self.dis)
            # 必要的软件延时
            time.sleep(0.1)
        self.ser.write(b'\x5A\x05\x07\x00\x00') #使能输出
    def stop(self):
        self.thd_on = 0