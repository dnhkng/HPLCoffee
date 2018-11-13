from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtSvg

import sys


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

        font_units = QFont("Syntha", 10)
        font_values = QFont("Syntha", 24)
        self.show()
        self.flowrate = 30
        self.volume = 50
        self.temperature = 50
        self.setFixedSize(800,480)
        self.running = False
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

    def start_stop(self):
        if not self.running:
            #self.startExtraction(int(self.flowrate))
            pumptime = self.volume/self.flowrate*60*1000
            print(pumptime)
            QTimer.singleShot(pumptime, self.start_stop)
            self.running = True
            self.pb_start.setText("Stop")
            print("starting")
        else:
            self.pb_start.setText("resetting")
            #self.stopExtraction()
            self.running = False

            print("stopping")

    def stopflow(self):
        if self.running:
            self.running = True
            self.start_stop()

    def flowup(self):
        if not self.flowrate >= 40:
            self.flowrate = self.flowrate + 1
        self.label_flow.setText(str(self.flowrate))

    def flowdown(self):
        if not self.flowrate <= 1:
            self.flowrate = self.flowrate - 1
        self.label_flow.setText(str(self.flowrate))

    def volup(self):
        if not self.volume >= 200:
            self.volume = self.volume + 1
        self.label_volume.setText(str(self.volume))

    def voldown(self):
        if not self.volume <= 1:
            self.volume = self.volume - 1
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
