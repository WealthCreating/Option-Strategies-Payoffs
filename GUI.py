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

def call_payoff(sT, strike_price, premium):
        return np.where(sT > strike_price, sT - strike_price, 0) - premium



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
        fileOpBull.triggered.connect(self.getInt)

        
    def getInt(self):
        i, okPressed = QInputDialog.getInt(self, "Target", "Enter your target of Nifty", 10400, 0, 50000, 50)
        if okPressed:
            x = self.bull(i)


    def bullish(self):
        sub = QDialog()
        layout = QGridLayout(sub)
        self.btn = QPushButton('Submit')
        self.txt = QTextEdit()
        self.lbl1 = QLabel('Enter your target on Nifty')
        layout.addWidget(self.lbl1)
        layout.addWidget(self.txt)
        layout.addWidget(self.btn)
        sub.setWindowTitle('Possible Bullish positions')
        self.mdi.addSubWindow(sub)
        self.btn.clicked.connect(self.check)
            
        sub.show()

    
    def bearish(self):
        sub = QWidget()
        layout = QGridLayout(sub)
        self.btn = QPushButton('Submit')
        self.txt = QTextEdit()
        self.lbl1 = QLabel('Enter your target on Nifty')
        layout.addWidget(lbl1)
        layout.addWidget(txt)
        layout.addWidget(btn)
        sub.setWindowTitle('Possible Bearish positions')
        self.mdi.addSubWindow(sub)
        self.btn.clicked.connect(self.check)
        sub.show()

    def bull(self, vtxt):
        #I will use the value in vtxt to do some calculations
        target = int(vtxt)
        
        #getting the required data for calculation of bull_spread
        udate = date.today()
        y = udate.year
        m = udate.month
        
        edate=get_expiry_date(year=y,month=m,index=True)
        #getting the EOD Premium value of target's call option
        tdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='CE',expiry_date=edate,strike_price=target)

        while tdata.empty:
            udate = udate - timedelta(1)
            y = udate.year
            m = udate.month
            tdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='CE',expiry_date=edate,strike_price=target)
        
        short_call_premium = tdata.loc[udate,'Close']
        short_call_strike_price = target

        #getting the ATM call strike price and premium
        sdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True)
        st = int(sdata.loc[udate,'Close'])
        rst = round(st, -2)
        if rst >= st:
            long_call_strike_price = rst
        else:
            long_call_strike_price = rst + 50

        print(long_call_strike_price)
        ldata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='CE',expiry_date=edate,strike_price=long_call_strike_price)
        long_call_premium = ldata.loc[udate, 'Close']

        sT = np.arange(long_call_strike_price-200,short_call_strike_price+200,50)
               
        long_call_payoff = call_payoff(sT, long_call_strike_price, long_call_premium)
        
        short_call_payoff = call_payoff(sT, short_call_strike_price, short_call_premium) * -1.0
        
        bull_Call_spread = long_call_payoff + short_call_payoff
        
        df = pd.DataFrame({'Nifty_Spot_Price':sT,
                           'Long_Call_Payoff':long_call_payoff,
                           'Short_Call_Payoff':short_call_payoff,
                           'Bull_Call_Spread':bull_Call_spread})
        df.set_index('Nifty_Spot_Price', inplace=True)
        
        

    

    def Wincenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @pyqtSlot()
    def check(self):
        val = self.txt.toPlainText()
        try:
            vtxt = int(val)  #example value would be 10450
            x = self.bull(val)
        except Exception as e:
            self.lbl1.setText("The value you entered is invalid, Please try again")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()   
    sys.exit(app.exec_())