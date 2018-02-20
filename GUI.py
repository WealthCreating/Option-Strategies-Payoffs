from PyQt5.QtWidgets import *
import sys, os
from datetime import date, timedelta
import nsepy as ns
from nsepy.derivatives import get_expiry_date
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
import traceback


class MainWindow(QMainWindow):                  


    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        self.iniUI()
    def iniUI(self):
        #resize, put the win at center and give it a title
        self.resize(1280, 720)
        self.Wincenter()
        self.setWindowTitle('Abinash\'s Project')

        #setting up the Main window with a Mdi Area, so we can create sub windows
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        #setting up a menu Bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        fileTRIN = QAction('TRIN', self) #defination of the action
        fileMenu.addAction(fileTRIN) #adding the action to the file menu

        fileOp = QMenu('Option Strategies', self)
        fileOpBull = QAction('Bullish', self)
        fileOpBear = QAction('Bearish', self)
        fileOp.addAction(fileOpBull)
        fileOp.addAction(fileOpBear)

        fileMenu.addMenu(fileOp)
        
        #Below codes will define the actions that will occur on the click of items in menu bar
        '''
        fileTRIN.triggered.connect()
        fileOpBear.triggered.connect()
        '''
        fileOpBull.triggered.connect(self.bullish)
        
    
    def bullish(self):
        sub = QWidget()
        layout = QGridLayout(sub)
        btn = QPushButton('Submit')
        txt = QTextEdit()
        lbl1 = QLabel('Enter your target on Nifty')
        layout.addWidget(lbl1)
        layout.addWidget(txt)
        layout.addWidget(btn)
        sub.setWindowTitle('Possible Bullish positions')
        self.mdi.addSubWindow(sub)
        vtxt = txt.toPlainText()
        event = btn.clicked
        while event == True:
            try:
                vtxt = int(vtxt)  #example value would be 10450
                event.connect(self.bull(vtxt))
            except Exception as e:
                lbl1.setText("The value you entered is invalid, Please try again")
        sub.show()

    def bearish(self):
        sub = QWidget()
        layout = QGridLayout(sub)
        btn = QPushButton('Submit')
        txt = QTextEdit()
        lbl1 = QLabel('Enter your target on Nifty')
        layout.addWidget(lbl1)
        layout.addWidget(txt)
        layout.addWidget(btn)
        sub.setWindowTitle('Possible Bullish positions')
        self.mdi.addSubWindow(sub)
        
        sub.show()

    def bull(self, vtxt):
        #I will use the value in vtxt to do some calculations
        value = vtxt
        print(value)



    def Wincenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()   
    sys.exit(app.exec_())