#!/usr/bin/env python

import sys
import os
import time
import ConfigParser
import PyQt4.Qt as Qt
from  ui_roisAmptek import Ui_MainWindow
import time


lib_path = os.path.abspath('../lib')
sys.path.append(lib_path)
from AmptekLib import  AmptekPX5


class Form(Qt.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, designMode=False):
        Qt.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.dialog = Dialog()
        if not os.path.exists('config.cfg'):
            raise RuntimeError('There is not config.cfg file')
        config = ConfigParser.RawConfigParser()
        config.read('config.cfg')
        device_name = config.get('AmptekPX5', 'host')
        timeout = config.getint('AmptekPX5', 'timeout')
        self.amptek = AmptekPX5(device_name)

        #In Initialize the GUI we read the Device Values
        self.readValues()
        Qt.QObject.connect(self.pushButton, Qt.SIGNAL('clicked()'),
                           self.applyChanges)
        Qt.QObject.connect(self.RefreshButton, Qt.SIGNAL('clicked()'),
                           self.readValues)

    def applyChanges(self):
        error = False

        #Check for all SCA that Low Threshold is lower than High Threshold
        for i in range(1,9):
          minim = self.__getattribute__('spinSCA%dMin' %i).value()
          maxim = self.__getattribute__('spinSCA%dMax' %i).value()
          ##Is not possible that the LOW Threshold is lower than HIGH Threshold
          if minim >= maxim :
              error = True

        if error:
           msg = ('\nError in Values. \n Any of Low Thresholds are '
                  'Equal/Higher than High Thresholds.\n')
           self.dialog.message.setText(msg)
           self.dialog.message.setAlignment(Qt.Qt.AlignCenter)
           self.dialog.show()
        else:
           #print "The values are correct, sending command to Amptek..."
           self.writeValues()

    def readValues(self):
        cmd = ''
        for i in range(1,9):
            cmd += 'SCAI=%d;SCAL;SCAH;' %i
        print 'Asking to Device...'
        for i in range(10):
            try:
                data = self.amptek.readTextConfig(cmd)
            except:
                if i == 9:
                    msg = ('There is problem with the communication. '
                           'Restart the HW.')
                    self.dialog.message.setText(msg)
                    self.dialog.message.setAlignment(Qt.Qt.AlignCenter)
                    self.dialog.show()
                    return
        print 'Received Values: %s' % data
        values = [value.split('=')[1]
                  for index,value in enumerate(data[:-1].split(';'))
                  if index not in (0,3,6,9,12,15,18,21)]
        print values
        for i in range(1,9):
            low = int(values[2*(i-1)])
            high = int(values[2*(i-1) +1])
            self.__getattribute__('spinSCA%dMin' %i).setValue(low)
            self.__getattribute__('spinSCA%dMax' %i).setValue(high)

    def writeValues(self):
        #Configure the ICR and the first SCA as TCR
        cmd = ('AUO1=ICR;CON1=AUXOUT1;SCAI=1;SCAL=0;SCAH=8191;'
               'SCAO=HIGH;SCAW=100;')
        for i in range(1,9):
            minim = self.__getattribute__('spinSCA%dMin' %i).value()
            maxim = self.__getattribute__('spinSCA%dMax' %i).value()
            cmd += ('SCAI=%d;SCAL=%d;SCAH=%d;SCAO=HIGH;SCAW=100;'
                    %(i, minim, maxim))
        print 'Command to write values in Device:'
        print cmd
        self.amptek.writeTextConfig(cmd)
        self.readValues()



class Dialog(Qt.QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)
         # Create widgets
        self.message = Qt.QLabel("Write my name here")
        self.button = Qt.QPushButton("OK")
        self.setWindowTitle("NOTICE:")
        # Create layout and add widgets
        layout = Qt.QVBoxLayout()
        layout.addWidget(self.message)
        layout.addWidget(self.button)

        # Set dialog layout
        self.setLayout(layout)

        # Add button signal to greetings slot
        Qt.QObject.connect(self.button, Qt.SIGNAL("clicked()"), self.greetings)

        #self.button.clicked.connect(self.greetings)

    # Greets the user
    def greetings(self):
        self.close()
def main():
    app = Qt.QApplication(sys.argv)
    w = Form(None)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
