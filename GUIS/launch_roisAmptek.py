import sys
import PyQt4.Qt as Qt
from  ui_roisAmptek import Ui_MainWindow



class Form(Qt.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, designMode=False):
        Qt.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.pushButton.setEnabled(False)
        self.dialog = Dialog()
        
        #In Initialize the GUI we read the Device Values
        self.readValues()
      
        #Signals from Low SCA
        Qt.QObject.connect(self.spinSCA1Min, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA2Min, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA3Min, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA4Min, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
      
        #Signals from High SCA
        Qt.QObject.connect(self.spinSCA1Max, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA2Max, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA3Max, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
        Qt.QObject.connect(self.spinSCA4Max, Qt.SIGNAL("valueChanged(int)"), self.roisChanged)
      
        Qt.QObject.connect(self.pushButton, Qt.SIGNAL("clicked()"), self.applyChanges)



    def roisChanged(self, index):
        self.pushButton.setEnabled(True)        

    def applyChanges(self):
        error = False

        #Check for each sca that the Low Threshold are lower than High Threshold
        for i in range(1,5):
          minim = self.__getattribute__('spinSCA%dMin' %i).value()
          maxim = self.__getattribute__('spinSCA%dMax' %i).value()
          ##Is not possible that the LOW Threshold is lower than HIGH Threshold
          if minim >= maxim :
              error = True

        if error:
           msg = "\nError in Values. \n Any of Low Thresholds are Equal/Higher than High Thresholds.\n"
           self.dialog.message.setText(msg)
           self.dialog.message.setAlignment(Qt.Qt.AlignCenter)
           self.dialog.show()
        else:
           #print "The values are correct, sending command to Amptek..."
           self.writeValues()
            
    def readValues(self):
        cmd = ''
        for i in range(1,5):
            minim = self.__getattribute__('spinSCA%dMin' %i).value()
            maxim = self.__getattribute__('spinSCA%dMax' %i).value()
            cmd += "SCAI=%d;SCAL;SCAH;" %(i+1)
        cmd = cmd[:-1]
        print "Command to ask Actual Values:"
        print cmd
        values = "SCAI=2;SCAL=1;SCAH=8192SCAI=3;SCAL=0;SCAH=8192SCAI=4;SCAL=0;SCAH=8192SCAI=5;SCAL=0;SCAH=8192"


    def writeValues(self):
        cmd = 'AUO1=ICR;CON1=AUXOUT1;'
        for i in range(1,5):
            minim = self.__getattribute__('spinSCA%dMin' %i).value()
            maxim = self.__getattribute__('spinSCA%dMax' %i).value()
            cmd += "SCAI=%d;SCAL=%d;SCAH=%d;" %(i+1, minim, maxim)
        cmd = cmd[:-1]
        print "Command to write values in Device:"
        print cmd


  
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
