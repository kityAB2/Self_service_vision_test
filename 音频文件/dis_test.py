import sys
from playsound import playsound
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from display_ui import Ui_Form
from distance_qthread import Distance_Thread
from vision_test_qthread import Vision_Test_Thread
import numpy as np
import time
#定义系统相关状态
system_close = 0
system_wait_test = 1
system_dis_demarcate = 2
system_version_testing = 3
system_test_ending = 4
#定义多久未操作则复位
un_operate_time = 20*1000
#定义模式对应的标定距离
dis_demarcate = [0,50,250,500,0]
dis_people_on_range = [[],[25,75],[150,350],[200,700],[]]
dis_biay = [0,5,10,20,0]
class myputpic(QtWidgets.QWidget,Ui_Form):
    voice_signal = pyqtSignal(int) 
    def __init__(self):
        super(myputpic,self).__init__()
        self.setupUi(self)
        self.vision_label.setText("系统未启动，请点击启动系统按钮")
        self.vision_label.setStyleSheet("background-color: rgb(211, 211, 211);")#211
        # imgName, imgType = QFileDialog.getOpenFileName(self, "打开图片", "", "*.jpg;;*.png;;All Files(*)")
        # jpg = QtGui.QPixmap(imgName).scaled(self.label.width(), self.label.height())
        #jpg = QtGui.QPixmap(r'/home/pi/test/视力检测E/视力检测E40树莓派.jpg').scaled(self.vision_label.width(), self.vision_label.height())
        #self.vision_label.setPixmap(jpg)
        #初始化所用的变量参数优先
        self.mode = 0           #指示装置的
        self.dis_dem = 0        #标定的距离
        self.dis_dem_cnt = 0    #标定距离过程中的次数
        self.state = system_close       #指示装置的显示模式
        self.dis_current = 0
        self.dis_voice = 0      #声音阻塞
        self.people_on = 0      #指示是否有人
        #初始化定时器相关任务
        self.timer = QTimer()  # 初始化定时器用于无响应系统复位
        self.timer.timeout.connect(self.time_out) #链接超时函数
        self.timer.setSingleShot(True) #超时只执行一次
        #距离标定过程中防阻塞定时器
        '''
        self.timer2 = QTimer()  # 初始化定时器用于无响应系统复位
        self.timer2.timeout.connect(self.time_out) #链接超时函数
        self.timer2.setSingleShot(True) #超时只执行一次
        '''
        self.voice_signal.connect(self.distance_voice)  #绑定距离标定的声音进程
        #初始距离化线程
        self.thread_1 = Distance_Thread()
        self.thread_1.dis_signal.connect(self.dis_update)
        self.thread_1.terminate()
        self.thread_2 = None
        #下拉框改变绑定槽函数
        self.mode_comboBox.currentIndexChanged.connect(self.selectionChange)
        #设置关闭系统案件点击槽函数
        self.close_pushButton.clicked.connect(self.close_app)
        #系统开始按键绑定槽函数
        self.start_pushButton.clicked.connect(self.system_start)
        #开始测试按键绑定函数
        self.starttest_pushButton.clicked.connect(self.system_start_test)
        #复位按键绑定函数
        self.init_pushButton.clicked.connect(self.system_init)
    #self返回的是控件本身  
    def selectionChange(self,i):
        #for count in range(self.mode_comboBox.count()):
            #print('item'+str(count)+'='+self.mode_comboBox.itemText(count))
            #print('current index',i,'selection changed',self.mode_comboBox.currentText())
        if(self.state == system_wait_test):
            self.mode = i   #更新所选择的模式，并重置无操作时间
            self.dis_dem = dis_demarcate[i] #确定标定距离
            print("当前模式为",self.mode_comboBox.itemText(i))
            self.timer.start(un_operate_time)
        else:
            self.mode_comboBox.setCurrentIndex(self.mode)#其他状态下不可修改

            
    #案件系统启动程序
    def system_start(self):
        #self.thread_1.start()
        #初始化界面刷新线程
        #self.thread_2 = Vision_Test_Thread(distance=dis_demarcate[2])
        #self.thread_2._signal.connect(self.version_update)
        #self.thread_2.start() #开始测量视力
        #playsound("/home/pi/test/音频文件/欢迎使用/欢迎使用.mp3",block=True)
        
        if(self.state == system_close):     #说明装置还未开启
            self.state = system_wait_test
            self.vision_label.setText("系统已启动")
            self.vision_label.setStyleSheet("background-color: rgb(255, 255, 255);")
            playsound("/home/pi/test/音频文件/欢迎使用/欢迎使用.wav",block=True)
            #self.thread_1.start()
            '''
            print("欢迎使用智能测量视力装置，请根据语音提示完成操作，\
请选择模式后点击开始按钮，若未检测到操作，则系统自动关闭")
            '''
            print("定时器已经开启")
            self.timer.start(un_operate_time)
         
           
    #设置屏幕居中    
    def center(self):
        #设置水平居中
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        newLeft = (screen.width()-size.width())/2
        newTop = (screen.height()-size.height())/2
        self.move((int)(newLeft),0)
        
    def close_app(self):
        if self.thread_1!=None:#关闭测距
            self.thread_1.terminate()
        if self.thread_2!=None:   
            self.thread_2.terminate()
        sender = self.sender()
        print(sender.text()+'按钮被按下')
        app = QApplication.instance()
        app.quit()
    def dis_update(self,distance):
        self.distance = distance
        #print(type(distance))
        self.distance_label_dis.setText(format(distance, 'd')+"cm")
        #print("距离数据开始更新",distance)
        #self.thread_1.terminate()#终止线程
        if(self.state == system_dis_demarcate):#距离标定状态
            if(self.mode != 0 and self.mode != 4):
                if(distance<dis_people_on_range[self.mode][1]) and distance>dis_people_on_range[self.mode][0]: #检测到有人
                    self.timer.start() #如果标定距离在误差范围内则停止
                    if(distance-self.dis_dem>dis_biay[self.mode]):
                        self.dis_dem_cnt = 0 #一次未标定则清零
                        self.people_on=0
                        #playsound("/home/pi/test/音频文件/请上前/请上前.mp3",block=True)
                        #time.sleep(5)
                        if self.dis_voice == 0:
                            self.dis_voice = 1
                            self.voice_signal.emit(0)
                            
                        print("请靠近点")
                    elif (self.dis_dem-distance>dis_biay[self.mode]):
                        self.people_on=0
                        self.dis_dem_cnt = 0 #一次未标定则清零
                        #playsound("/home/pi/test/音频文件/请后退/请后退.mp3",block=True)
                        #time.sleep(5)
                        if self.dis_voice == 0:
                            self.dis_voice = 1
                            self.voice_signal.emit(1)
                            
                        print("请离远点")
                    else:
                        if self.dis_voice == 0 and self.people_on==0:
                            self.people_on=1
                            self.dis_voice = 1 
                            self.voice_signal.emit(2)
                                                   
                        print("请保持此距离")
                        #playsound("/home/pi/test/音频文件/请保持此距离/请保持此距离.mp3",block=True)
                        #time.sleep(5)
                        self.dis_dem_cnt = self.dis_dem_cnt+1   #在误差范围内次数就加一
                        if(self.dis_dem_cnt>100):
                            self.state = system_version_testing #计数次数达标  进入测试状态
                            self.timer.stop() #终止10s未操作检测
                            #初始化界面刷新线程
                            if self.thread_2!=None:
                                self.thread_2.resume()
                            else:
                                self.thread_2 = Vision_Test_Thread(distance=dis_demarcate[self.mode])
                                self.thread_2._signal.connect(self.version_update)
                                self.thread_2.sight_signal.connect(self.result_get)
                                self.thread_2.voice_signal.connect(self.vision_voice)
                                self.thread_2.start() #开始测量视力
                  
                else:
                    print("未检测不到人")
                    self.people_on=0
                    if self.dis_voice == 0:
                        self.dis_voice = 1
                        self.voice_signal.emit(3)
                        
                    #playsound("/home/pi/test/音频文件/未检测到有人/未检测到有人.mp3",block=True)
                    #time.sleep(5)
                    self.dis_dem_cnt = 0 #一次未标定则清零
            else: #标定距离模式
                pass
        elif(self.state == system_version_testing):
            if(distance<self.dis_dem-dis_biay[self.mode] or distance>self.dis_dem+dis_biay[self.mode]):
                self.thread_2.pause() #距离不再指定范围内就挂起
                self.dis_dem_cnt = 0
                self.people_on=1
                print("偏离方向")
                if self.dis_voice == 0:
                    self.state = system_dis_demarcate
                    self.dis_voice = 1
                    self.voice_signal.emit(4)
            
    def time_out(self):
        #self.thread_1.terminate()
        #self.thread_2.terminate()
        if self.thread_1!=None:#关闭测距
            self.thread_1.terminate()
        if self.thread_2!=None:#关闭线程 
            self.thread_2.terminate()
        
        self.vision_label.setText("系统未启动，请点击启动系统按钮")
        self.vision_label.setStyleSheet("background-color: rgb(211, 211, 211);")
        '''
        self.state = system_close       #指示装置的显示模式
        self.mode = 0
        self.mode_comboBox.setCurrentIndex(self.mode)
        '''
        #类似初始化
        self.mode = 0           #指示装置的
        self.mode_comboBox.setCurrentIndex(self.mode)
        self.dis_dem = 0        #标定的距离
        self.dis_dem_cnt = 0    #标定距离过程中的次数
        self.state = system_close       #指示装置的显示模式
        self.dis_current = 0
        self.people_on = 0      #指示是否有人
        #初始化定时器相关任务
        self.timer = QTimer()  #初始化定时器用于无响应系统复位
        self.timer.timeout.connect(self.time_out) #链接超时函数
        self.timer.setSingleShot(True) #超时只执行一次
        #初始距离化线程
        self.thread_1 = Distance_Thread()
        self.thread_1.dis_signal.connect(self.dis_update)
        #self.thread_1.terminate()
        self.thread_2 = None
        #self.thread_1.terminate()#关闭超声波线程
        print("未进行任何操作，系统复位")
    def system_start_test(self):
        if(self.state == system_wait_test):
            if(self.mode != 0):    #模式不为空白
                print("开始检测视力")
                self.label_dis_left.setText('   ')
                self.label_dis_right.setText('   ')
                self.timer.start(un_operate_time)#启动定时器线程
                self.state = system_dis_demarcate #开始标定距离
                self.thread_1.start()#超声波波线程启动
            else:
                print("未选择正确的模式")
    def version_update(self,QImage):
        #self.vision_label.setPixmap(QImage)
       
        self.vision_label.setPixmap(QPixmap(""))
        #print(self.vision_label.size())
        self.vision_label.setPixmap(QPixmap.fromImage(QImage))
        playsound("/home/pi/test/音频文件/请说出视标方向/请说出视标方向.wav")
    def result_get(self,left_sight,right_sight):
        self.state = system_test_ending
        self.vision_label.setText("检测结束")
        left_str = str(left_sight)
        right_str = str(right_sight)
        left_str = left_str[:1]+"."+left_str[1:]
        right_str = right_str[:1]+"."+right_str[1:]
        self.label_dis_left.setText(left_str)
        self.label_dis_right.setText(right_str)
        
        playsound("/home/pi/test/音频文件/您的左眼视力为/您的左眼视力为.mp3")
        playsound("/home/pi/test/音频文件/数字无间隔/"+str(left_sight//10)+".mp3")
        playsound("/home/pi/test/音频文件/数字无间隔/点.mp3",block=True)
        playsound("/home/pi/test/音频文件/数字无间隔/"+str(left_sight%10)+".mp3")
        playsound("/home/pi/test/音频文件/您的右眼视力为/您的右眼视力为.mp3")
        playsound("/home/pi/test/音频文件/数字无间隔/"+str(right_sight//10)+".mp3")
        playsound("/home/pi/test/音频文件/数字无间隔/点.mp3",block=True)
        playsound("/home/pi/test/音频文件/数字无间隔/"+str(right_sight%10)+".mp3")
        if self.thread_1!=None:#关闭测距
            self.thread_1.terminate()
        if self.thread_2!=None:#关闭线程 
            self.thread_2.terminate()
 
        self.mode = 0           #指示装置的
        self.dis_dem = 0        #标定的距离
        self.dis_dem_cnt = 0    #标定距离过程中的次数
        self.state = system_close       #指示装置的显示模式
        self.dis_current = 0
        self.people_on = 0      #指示是否有人
        #初始化定时器相关任务
        self.timer = QTimer()  #初始化定时器用于无响应系统复位
        self.timer.timeout.connect(self.time_out) #链接超时函数
        self.timer.setSingleShot(True) #超时只执行一次
        #初始距离化线程
        self.thread_1 = Distance_Thread()
        self.thread_1.dis_signal.connect(self.dis_update)
        #self.thread_1.terminate()
        self.thread_2 = None
        self.timer.start(un_operate_time)
    def vision_voice(self,voice_ide):
        if(voice_ide==0):
            playsound("/home/pi/test/音频文件/请闭上你的左眼/请闭上你的左眼.wav",block=True)
        else:
            playsound("/home/pi/test/音频文件/请闭上你的右眼/请闭上你的右眼.wav",block=True)
    def distance_voice(self,ide):
        self.dis_voice = 1
        if(ide==0):
            playsound("/home/pi/test/音频文件/请上前/请上前.mp3",block=True)
        elif(ide==1):
            playsound("/home/pi/test/音频文件/请后退/请后退.mp3",block=True)
        elif(ide==2):
            playsound("/home/pi/test/音频文件/请保持此距离/请保持此距离.mp3",block=True)
        elif(ide==3):
            playsound("/home/pi/test/音频文件/未检测到有人/未检测到有人.mp3",block=True)
        elif(ide==4):
            playsound("/home/pi/test/音频文件/你已偏离距离/你已偏离距离.mp3",block=True)

        else:
            pass
        time.sleep(1)
        self.dis_voice = 0
    def system_init(self):
        if self.thread_1!=None:#关闭测距
            self.thread_1.terminate()
        if self.thread_2!=None:#关闭线程 
            self.thread_2.terminate()
        self.vision_label.setText("系统未启动，请点击启动系统按钮")
        self.vision_label.setStyleSheet("background-color: rgb(211, 211, 211);")#211
        # imgName, imgType = QFileDialog.getOpenFileName(self, "打开图片", "", "*.jpg;;*.png;;All Files(*)")
        # jpg = QtGui.QPixmap(imgName).scaled(self.label.width(), self.label.height())
        #jpg = QtGui.QPixmap(r'/home/pi/test/视力检测E/视力检测E40树莓派.jpg').scaled(self.vision_label.width(), self.vision_label.height())
        #self.vision_label.setPixmap(jpg)
        #初始化所用的变量参数优先
        self.mode = 0           #指示装置的
        self.mode_comboBox.setCurrentIndex(self.mode)#其他状态下不可修改
        self.dis_dem = 0        #标定的距离
        self.dis_dem_cnt = 0    #标定距离过程中的次数
        self.state = system_close       #指示装置的显示模式
        self.dis_current = 0
        self.dis_voice = 0      #声音阻塞
        self.people_on = 0      #指示是否有人
        #初始化定时器相关任务
        self.timer.stop()
        #距离标定过程中防阻塞定时器
        #初始距离化线程
        self.thread_1 = Distance_Thread()
        self.thread_1.dis_signal.connect(self.dis_update)
        self.thread_1.terminate()
        self.thread_2 = None    
if __name__=='__main__':
    app=QApplication(sys.argv)
    a=myputpic()
    a.center()
    a.show()

    sys.exit(app.exec_())
