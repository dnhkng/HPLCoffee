from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtSvg
import datetime, time
import serial
import binascii
import sys
import time


connection_string = 'W7= Edit        Manual   Run               '


class gsioc:
    def __init__(self,serial=None):
        self.serial = serial

    def createSerial(self,port=0,timeout=0.1):
        self.port = port
        self.timeout = timeout
        # Initiate serial connection
        s = serial.Serial(port)
        #s = serial.serial_for_url("loop://")  # loop for testing
        s.baudrate = 9600
        s.bytesize = 8
        s.parity = serial.PARITY_NONE
        s.stopbits = 1
        s.timeout = timeout
        self.serial = s
        try :
            s.open()
            print(s)
        except :
            print(s)

    def closeSerial(self):
        self.serial.close()

    def connect(self,ID=0):
        if( int(ID) not in range(64) ):
            raise Exception("ID out of range [0,63]")
        ID += 128
        s = self.serial
        s.flushInput()
        s.write(bytes.fromhex('ff'))
        time.sleep(self.timeout)   # Passively wait for all devices to disconnect
        s.write(ID.to_bytes(1,byteorder='big'))
        resp = s.read(1)    # Will raise serialTimoutException after timeout
        print(str(datetime.datetime.now()) + " -- Connected to device ", ID-128)

    # returns byte array
    # Use str(resp,'ascii') or resp.decode('ascii') to get ascii string
    def iCommand(self,commandstring):
        command = binascii.a2b_qp(commandstring)
        if(command[0] not in range(0,255)):     # Change this to correct range
            raise Exception("Command out of range")
        s = self.serial
        s.flushInput()
        s.write(command[0:1])
        resp = bytearray(0)
        while(True):
            resp.append(s.read(1)[0])
            if(resp[len(resp)-1] > 127):
                resp[len(resp)-1] -= 128
                # print(str(datetime.datetime.now()) + " -- Immediate response complete")
                break
            else:
                s.write(bytes.fromhex("06"))
        return resp.decode("ascii")

    def bCommand(self,commandstring):
        data = binascii.a2b_qp("\n" + commandstring + "\r")
        s = self.serial
        s.flushInput()
        resp = bytearray(0)

        # begin buffered command by sending \n until the device echos \n or times out
        firstErrorPrinted = False # This is used to prevent repetitive printing 
        # begin loop
        while(True):
            s.write(data[0:1])    # send line feed
            readySig = s.read(1)[0]
            if(readySig == 10):
                print(str(datetime.datetime.now()) + " -- Starting Buffered command")
                break
            elif(readySig == 35):
                if(not firstErrorPrinted):
                    print("Device busy. Waiting...")
                    firstErrorPrinted = True
            else:
                raise Exception("Did not recieve \\n (0x0A) or # as response")
        resp.append(readySig)

        # Send buffered data
        for i in range(1,len(data)):
            s.write(data[i:i+1])
            resp.append(s.read(1)[0])
            if( resp[i] != data[i] ):
                raise Exception("Recieved " + str(resp,'ascii') + " instead of " + str(data[i:i+1]))
            if( resp[i] == 13 ):
                print(str(datetime.datetime.now()) + " -- Buffered command complete")
                return resp

        # This will happen if sending the data failed
        print(str(datetime.datetime.now()) + " -- Buffered command FAILED")
        resp_no_whitespace = resp[1:len(resp)-2]
        return resp_no_whitespace.decode("ascii")

def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()
        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False
    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("CoffeeMachine.ui", self)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.running = False
        self.is_connected = False
        self.volume = 50

        self.h = gsioc()


        font_units = QFont("Syntha", 10)
        font_values = QFont("Syntha", 24)
        self.show()
        self.flowrate = 30
        self.volume = 50
        self.temperature = 50
        self.setFixedSize(800,480)
        self.label_flow.setText(str(self.flowrate))
        self.label_temp.setText(str(self.temperature)+"\N{DEGREE SIGN}")
        self.label_volume.setText(str(self.volume))
        self.label_flow.setFont(font_values)
        self.label_flow.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_flow_unit.setFont(font_units)
        self.label_flow_unit.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_pressure.setText("400")
        self.label_pressure.setFont(font_values)
        self.label_pressure.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_pressure_unit.setFont(font_units)
        self.label_pressure_unit.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_volume.setFont(font_values)
        self.label_volume.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_volume_unit.setFont(font_units)
        self.label_volume_unit.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_volumeinput.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_flowinput.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_tempinput.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_temp.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_temp.setFont(font_values)
        self.pb_flowup.clicked.connect(self.flowup)
        self.pb_flowdown.clicked.connect(self.flowdown)
        self.pb_tempup.clicked.connect(self.tempup)
        self.pb_tempdown.clicked.connect(self.tempdown)
        self.pb_volup.clicked.connect(self.volup)
        self.pb_voldown.clicked.connect(self.voldown)
        self.pb_start.clicked.connect(self.start_stop)
        self.label_connection.setFont(font_units)
        self.label_connection.setAttribute(Qt.WA_TranslucentBackground, True)
        self.label_connection.setText("waiting for pump")
        QApplication.processEvents()
        self.timer = QTimer()
        while not self.getConnection():
            QApplication.processEvents()
            time.sleep(0.1)
        self.label_connection.setText("connected")
        self.timer.timeout.connect(self.checkConnection)
        self.timer.start(1000)

    def getConnection(self):
        try:
            self.h.closeSerial()
        except:
            pass

        try:
            self.h.createSerial(port='COM5',timeout=0.1)
        except:
            return False

        for i in range(200):
            self.h.connect(ID=1)
            try:
                if self.h.iCommand("%") == '331V1.10':
                    print('Connected')
                    self.is_connected = True
                    return True
            except:
                pass
            
        print('Connection Failed')
        return False

    # check if we started up correctly
    def checkConnection(self):
        self.is_connected = False
        print('in timer')
        try:
            if self.h.iCommand("%") == '331V1.10':
                self.is_connected = True
                print('connected')
        except:
            self.is_connected = False
            print('not connected')

        if self.is_connected:
            self.label_connection.setText("pump connected")
            QApplication.processEvents()

        else:
            self.label_connection.setText("waiting for pump")
            QApplication.processEvents()
            self.is_connected = False
            self.timer.stop()

            while not self.getConnection():
                QApplication.processEvents()
                time.sleep(0.1)

            self.timer.start(1000)

    def startPriming(self):
        self.h.bCommand("K=c|")
        time.sleep(0.1)
        self.h.bCommand("K=c|")
        time.sleep(0.1)
        self.h.bCommand("K=a|")

    def stopPriming(self):
        self.h.bCommand("K=a|")
        time.sleep(0.2)
        self.h.bCommand("K=X|")
        time.sleep(0.2)
        self.h.bCommand("K=X|")
        time.sleep(0.2)
        self.h.bCommand("K")

    def startExtraction(self, file_num):
        self.h.bCommand("?R" + str(file_num/10))

    def stopExtraction(self):
        self.h.iCommand("$")
        time.sleep(1)
        self.getConnection()
        self.pb_start.setText("Start")

    def getPressure(self):
        return self.h.iCommand("Q")


    def start_stop(self):
        if (not self.running) and self.is_connected:
            self.pb_start.clicked.connect(self.start_stop)
            self.startExtraction(int(self.flowrate))
            pumptime = self.volume / self.flowrate * 60 * 1000
            QTimer.singleShot(pumptime, self.stoptimer)
            print("Stop timer started with " + str(int(pumptime))+"ms")
            self.running = True
            self.pb_start.setText("Stop")
            print("starting")
        elif self.running and self.is_connected:
            self.pb_start.setText("resetting")
            self.pb_start.clicked.disconnect(self.start_stop)
            self.stopExtraction()
            self.running = False
            print("stopping")
        else:
            pass

    def stoptimer(self):
        if self.running:
            self.start_stop()

    def flowup(self):
        if not self.flowrate >= 50:
            self.flowrate = self.flowrate + 10
        self.label_flow.setText(str(self.flowrate))

    def flowdown(self):
        if not self.flowrate <= 10:
            self.flowrate = self.flowrate - 10
        self.label_flow.setText(str(self.flowrate))

    def volup(self):
        if not self.volume >= 200:
            self.volume = self.volume + 5
        self.label_volume.setText(str(self.volume))

    def voldown(self):
        if not self.volume <= 5:
            self.volume = self.volume - 5
        self.label_volume.setText(str(self.volume))

    def tempup(self):
        if not self.temperature >= 110:
            self.temperature = self.temperature + 1
        self.label_temp.setText(str(self.temperature)+"\N{DEGREE SIGN}")

    def tempdown(self):
        if not self.temperature <= 0:
            self.temperature = self.temperature - 1
        self.label_temp.setText(str(self.temperature)+"\N{DEGREE SIGN}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
