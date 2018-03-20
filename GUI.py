from PyQt5.QtWidgets import *
import sys, os
from datetime import date, timedelta
import datetime
from time import sleep
import nsepy as ns
from nsepy.derivatives import get_expiry_date
from nsepy.history import get_price_list, get_dprice_list
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtCore import *
import seaborn as sns   

'''
Known Errors:
1. Giving a target value which is not a strike price will return error or might crash the program.
2. When calling some functions of nsepy via PyQt5, an extra parameter self is passed to nsepy which causes error, 
   I have worked around it by altering nsepy module and adding **kwargs to the functions which were returning the error
3. Option pain: when playing around with the various available symbols and expiry dates and then clicking suggested action button the program crashes with the error coming from nsepy module
   most likely a connection is aborted and AttributeError: 'ThreadReturns' object has no attribute 'result'
   Temporary Solution for this problem is to reboot the script and select whichever symbol and expiry you wanted to check, plot it's chart and then click suggested action.
'''

def call_payoff(sT, strike_price, premium):
    return np.where(sT > strike_price, sT - strike_price, 0) - premium

def put_payoff(sT, strike_price, premium):
    return  np.where(sT<strike_price, strike_price - sT, 0) - premium

def myround(x, base=50):
    return int(base * round(float(x)/base))

def variance_calculator(series,series_average,win_len):
    sma = win_len
    temp = series.subtract(series_average) #a-b
    temp2 = temp.apply(lambda x: x**2)     #(a-b)^2
    temp3 = temp2.rolling(sma-1).mean()    # summation[(a-b)^2]/(sma-1)
    sigma = temp3.apply(lambda x: math.sqrt(x))#sigma is the standard deviation
    return sigma


class MainWindow(QMainWindow):                  

    

    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        self.iniUI()

    def iniUI(self):
        global edate, st, udate, debhav, CE, PE  #Since the latest Nifty close price is used by us for multiple calculation, I am making them a global value and computing their value as soon as the program begins
        #resize, put the win at center and give it a title
        self.resize(1280, 720)
        self.Wincenter()
        self.setWindowTitle('Abinash\'s Project')

        #setting up the Main window with a Mdi Area, so we can create sub windows
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)
        QToolTip.setFont(QFont('SansSerif', 10))
        #setting up a menu Bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        fileTRIN = QAction('TRIN', self) #defination of the action
        fileMenu.addAction(fileTRIN) #adding the action to the file menu

        #Next Action in File menu with sub menu
        fileOp = QMenu('Option Strategies', self)
        fileOpBull = QAction('Bullish', self)
        fileOpBear = QAction('Bearish', self)
        fileOp.addAction(fileOpBull)
        fileOp.addAction(fileOpBear)
        fileMenu.addMenu(fileOp)
        
        filePain = QAction('Option Pain',self)
        fileMenu.addAction(filePain)

        #Below codes will define the actions that will occur on the click of items in menu bar
        
        fileTRIN.triggered.connect(self.TRIN)
        
        fileOpBull.triggered.connect(self.getbullInt)
        fileOpBear.triggered.connect(self.getbearInt)
        filePain.triggered.connect(self.option_pain)

        edate, st, udate, debhav, CE, PE = self.set_params()

        print(edate,st, udate)
        self.showMaximized()

    def set_params(self):
        #setting basic dates
        udate = date.today()
        def_dt = udate
        y = udate.year
        m = udate.month
        target = 10500
        #Getting the last data available to us online and setting the start date of data based on that

        sdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True)
        while sdata.empty:
            udate = udate - timedelta(1)
            y = udate.year
            m = udate.month
            sdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True)
        st = int(sdata.loc[udate,'Close'])

        edate=get_expiry_date(year=y,month=m,index=True)
        if udate > edate:
            edate=get_expiry_date(year=y,month=m+1,index=True)

        #print('inside function {}'.format(edate))
        #Now we will test if the expiry date we got is correct or if that thursday is a holiday and adjust the expiry according to it.
        test = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='CE',expiry_date=edate,strike_price=target)
        lim = 0
        while test.empty:
            edate = edate - timedelta(1)
            #print('inside loop edate fix {}'.format(edate))
            test = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='CE',expiry_date=edate,strike_price=target)
            #print('inside loop {}'.format(test))
            lim = lim + 1
            if lim >= 4:
                break

        #Getting the Derivatives Bhav and setting it as a global Dataframe
        max_tries = 5
        if os.path.isfile('derivativesbhav.xlsx'):
            df = pd.read_excel('derivativesbhav.xlsx')
            check_date= df['TIMESTAMP'].iloc[1]
    
            dt = datetime.datetime.strptime(check_date, '%d-%b-%Y').strftime('%Y-%m-%d')

            td = str(date.today())

            if dt == td:
                debhav = df
            else:
                try:
                        dbhav = get_dprice_list(dt=def_dt)
                        debhav = dbhav
                except Exception as e:
                    new_dt = def_dt - timedelta(1)
                        
                    for x in range(0,max_tries):
                        #str_error = 'defining variable'
                        try:
                            #print('attempting with new_Dt {}'.format(new_dt))
                            dbhav = get_dprice_list(dt=new_dt)
                            debhav = dbhav
                            break
                        except Exception as e:
                            #print(e)
                            new_dt = new_dt - timedelta(1)
                
                debhav.to_excel('derivativesbhav.xlsx')
                debhav = pd.read_excel('derivativesbhav.xlsx')
        else:
            try:
                    dbhav = get_dprice_list(dt=def_dt)
                    debhav = dbhav
            except Exception as e:
                new_dt = def_dt - timedelta(1)
                        
                for x in range(0,max_tries):
                    #str_error = 'defining variable'
                    try:
                        #print('attempting with new_Dt {}'.format(new_dt))
                        dbhav = get_dprice_list(dt=new_dt)
                        debhav = dbhav
                        break
                    except Exception as e:
                        #print(e)
                        new_dt = new_dt - timedelta(1)

            debhav.to_excel('derivativesbhav.xlsx')
            debhav = pd.read_excel('derivativesbhav.xlsx')

        #bifurcation of the derivative bhav to be able to use the call and put data for the strategies
        df = debhav
        fil_inst = df['INSTRUMENT'].isin(['OPTIDX'])
        temp_df = df[fil_inst]
        fil_symb = temp_df['SYMBOL'].isin(['NIFTY'])
        temp2_df = temp_df[fil_symb]
        for e in temp2_df['EXPIRY_DT']:
            expdate = e
            break
        temp2_df = temp2_df[temp2_df['EXPIRY_DT']==expdate]
        CE = temp2_df[temp2_df['OPTION_TYP']=='CE']
        PE = temp2_df[temp2_df['OPTION_TYP']=='PE']

        CE = CE.reset_index(drop=True)
        PE = PE.reset_index(drop=True)

        return edate, st, udate, debhav, CE, PE 

    def TRIN(self):
        try:
            if os.path.isfile('Data.csv'):

                
                df = pd.read_csv('Data.csv')
                l = len(df.index)
                l = l - 1
                #print('Your Data file has Data available upto :' + df['Date'].loc[l])
                #QMessageBox.information(self, '', 'Your Data file has Data available upto :{}'.format(df['Date'].loc[l]), QMessageBox.Ok, QMessageBox.Ok)
                dt = df['Date'].loc[l] #datetime.datetime.strptime(check_date, '%d-%b-%Y').strftime('%Y-%m-%d')
                #self.data_date = dt
                ytd = date.today() - timedelta(1)
                yt = str(ytd)
                td = str(date.today())
                #checking if the data available is outdated
                year, month, day = map(int, dt.split("-"))
                data_date = date(year,month,day)
                diff = date.today() - data_date
                diff =  int(diff.days)
                ytdf = ns.get_history(symbol = 'SBIN', start=ytd, end=ytd)
                if dt == td:
                    #print('You already have the lastest DATA. \n Potting the Chart')
                    od = self.TRIN_plot(df)
                elif dt == yt:
                    test = ns.get_history(symbol = 'SBIN', start=date.today(), end=date.today())
                    if test.empty:
                    
                        #print('Today\'s Data has not been updated by NSE, plotting the chart with the Data available till yesterday')
                        QMessageBox.information(self, 'TRIN', 'Today\'s Data has not been updated by NSE, plotting the chart with the Data available till yesterday', QMessageBox.Ok, QMessageBox.Ok)
                        od = self.TRIN_plot(df)
                    else:
                        #print('Your Data outdated, getting the latest data')
                        os.remove('Data.csv')
                        #print('Fetching latest Data')
                        gd = self.TRIN_update_data()
                        #print('Calculating TRIN')
                        cd = self.TRIN_calculation(gd)
                        #print('Updated TRIN values are being stored in Data.csv file')
                        cd.to_csv("Data.csv")
                        Data = pd.read_csv("Data.csv")  #updating the csv file with latest data
                        pc = self.TRIN_plot(Data)
                elif diff > 2:
                    test = ns.get_history(symbol = 'SBIN', start=date.today(), end=date.today())
                    if test.empty:
                    
                        #print('Today\'s Data has not been updated by NSE, plotting the chart with the Data available till yesterday')
                        QMessageBox.information(self, 'TRIN', 'Today\'s Data has not been updated by NSE, plotting the chart with the Data available till {}'.format(dt), QMessageBox.Ok, QMessageBox.Ok)
                        od = self.TRIN_plot(df)
                    else:
                        #print('Your Data File seems to be more than 2 days old, updating the Data file')
                        os.remove('Data.csv')
                        #print('Fetching latest Data')
                        gd = self.TRIN_update_data()
                        #print('Calculating TRIN')
                        cd = self.TRIN_calculation(gd)
                        #print('Updated TRIN values are being stored in Data.csv file')
                        cd.to_csv("Data.csv")
                        Data = pd.read_csv("Data.csv")  #updating the csv file with latest data
                        pc = self.TRIN_plot(Data)
                elif diff == 2:
                    if ytdf.empty:
                        QMessageBox.information(self, 'TRIN', 'Either today\'s data has not been updated by NSE or It is a Holiday, Plotting the TRIN with the available data', QMessageBox.Ok, QMessageBox.Ok)                     
                        od = self.TRIN_plot(df)
                    else:
                        os.remove('Data.csv')
                    
                        gd = self.TRIN_update_data()
                        
                        cd = self.TRIN_calculation(gd)
                       
                        cd.to_csv("Data.csv")
                        Data = pd.read_csv("Data.csv")  #updating the csv file with latest data
                        pc = self.TRIN_plot(Data)
                else:
                    test = ns.get_history(symbol = 'SBIN', start=date.today(), end=date.today()) 

                    if test.empty:
                        #print ('Either today\'s data has not been updated by NSE or \n It is a Holiday')
                        QMessageBox.information(self, 'TRIN', 'Either today\'s data has not been updated by NSE or It is a Holiday, Plotting the TRIN with the available data', QMessageBox.Ok, QMessageBox.Ok)
                        #uo = input('Do you want to continue with the Data available upto {} Y/N ? '.format(dt))
                        
                        od = self.TRIN_plot(df)
                        
                    else:
                        #print('New Data available, removing the old Data file')
                        os.remove('Data.csv')
                        #print('Fetching latest Data')
                        gd = self.TRIN_update_data()
                        #print('Calculating TRIN')
                        cd = self.TRIN_calculation(gd)
                        #print('Updated TRIN values are being stored in Data.csv file')
                        cd.to_csv("Data.csv")
                        Data = pd.read_csv("Data.csv")  #updating the csv file with latest data
                        pc = self.TRIN_plot(Data)
                        
            
            else:
                #print('Old Data Not found, Constructing latest Data file')
                #print('Fetching latest Data')
                gd = self.TRIN_update_data()
                #print('Calculating TRIN')
                cd = self.TRIN_calculation(gd)
                #print('Updated TRIN values are being stored in Data.csv file')
                cd.to_csv("Data.csv")
                Data = pd.read_csv("Data.csv")  #updating the csv file with latest data
                
                pc = self.TRIN_plot(Data)
            
        except Exception as e:
                    print('There was an error {} in completing your request'.format(e))  
    
    def TRIN_update_data(self):
        """
        Getting The required data for calculation of TRIN indicator
        ___________________________________________________________
        """

        #setting default dates
        end_date = date.today()
        start_date = end_date - timedelta(365)
        month = end_date.month
        year = end_date.year


        #Deriving the names of 50 stocks in Nifty 50 Index
        nifty_50 = pd.read_html('https://en.wikipedia.org/wiki/NIFTY_50')

        nifty50_symbols = nifty_50[1][1]

        nifty_index_future = ns.get_history(symbol='NIFTY',
                                            start=start_date, end=end_date, index=True, futures=True, 
                                                   expiry_date=get_expiry_date(year,month))

        results = []
        for x in nifty50_symbols:
            data = ns.get_history(symbol = x, start=start_date, end=end_date)
            results.append(data)

        df = pd.concat(results)

        output = []
        lim =[]

        for x in df.index:
            Dates = df[df.index == x]
            adv = 0
            dec = 0
            net = 0
            advol = 0
            devol = 0
            netvol = 0
            if (not x in lim):
                for s in Dates['Symbol']:
                    y = Dates[Dates['Symbol'] == s]
                    #print(y.loc[x,'Close'])
                    cclose = y.loc[x,'Close']
                    #print(cclose)
                    copen = y.loc[x,'Open']
                    #print(copen)
                    cvol = y.loc[x,'Volume']
                    if cclose > copen:
                        adv = adv + 1
                        advol = advol + cvol
                        
                    elif copen > cclose:
                        dec = dec + 1
                        devol = devol + cvol
                        
                    else:
                        net = net + 1
                        netvol = netvol + cvol
                        
                    data = [x,adv,dec,advol,devol]
                    
                output.append(data)
                lim.append(x)

            
        final = pd.DataFrame(output, columns = ['Date','Advance','Decline','Adv_Volume','Dec_Volume'])
        final.set_index('Date', inplace = True)
        final['Future'] = nifty_index_future['Last']
        return final

    def TRIN_calculation(self, df):
        Data = df
        """
        We are now equipped to calculate the value of TRIN. The variable ‘tem1’ stores the value of 
        AD ratio, variable ‘tem2’ stores the value of AD volume ratio and ‘tem’ stores the ratio of 
        ‘tem1’ by ‘tem2’ (or the value of TRIN). We then store the value of ‘tem’ into the ‘Data’ 
        array under the header ‘TRIN’. As the value of TRIN is lopsided, we take its logarithm and 
        replace the values stored earlier with the logarithmic values calculated using the math 
        library. We will be using the closing values of the futures contract while placing buy/sell 
        orders, these closing prices have been stored in the colum ‘Future’. 
        """

        tem1 = Data['Advance'].divide(Data['Decline'])
        tem2 = Data['Adv_Volume'].divide(Data['Dec_Volume'])
        tem = tem1.divide(tem2)    #TRIN Value
        Data['TRIN'] = tem

        #applying log to the lopsided TRIN and storing the new TRIN
        Data['TRIN'] = Data['TRIN'].apply(lambda x: math.log(x))

        """
        We then initialize several variables which will be used later in the code
        """
        sma = 22 #the moving average window length
        k = 1.5 #constant represting 'k' times sigma away from moving average for Bollinger Band
        l = 2  #constant represting 'l' times sigma away from Bollinger Bands for stop loss band
        lot_size = 75 #lot size of futures contract

        """
        we compute the moving average of TRIN using the rolling.mean() function, here we 
        specify the window length of the average to be the variable ‘sma’, which has been initialized 
        with a value of 22 trading days. The moving average is stored in the ‘Data’ array under the 
        header ‘mAvg’. Under the header ‘TRIN_prev’, we store the value of TRIN shifted by one 
        trading day, using the shift() function.  
        """
        Data['mAvg'] = Data['TRIN'].rolling(sma).mean() #calculating the moving average of TRIN
        Data['TRIN_prev']= Data['TRIN'].shift(1) #moving average shifted ahead to check for crossover

        #calculating the standard deviation
        sigma = variance_calculator(Data['TRIN'],Data['mAvg'],sma) #calling the function
        k_sigma = k*sigma
        l_sigma = l*sigma

        Data['UBB'] = Data['mAvg'].add(k_sigma) #upper Bollinger band
        Data['LBB'] = Data['mAvg'].subtract(k_sigma) #lower Bollinger band
        Data['USL'] = Data['UBB'].add(l_sigma) #upper stoploss band
        Data['LSL'] = Data['LBB'].subtract(l_sigma) #lower stoploss band
        Data['Order'] = pd.Series() #order is a list which contains the orders: BUY/SELL/DO_nothing

        return Data

    def TRIN_plot(self,Data):
        l = len(Data.index)
        l = l - 1
                
        self.data_date = Data['Date'].loc[l]
        
        #setting up the GUI to show TRIN
        chart = QWidget()
        grid = QGridLayout()
        chart.setLayout(grid)
        self.mdi.addSubWindow(chart)
        #self.setGeometry(600,300, 1000, 600)
        chart.setToolTip("This index was developed by Richard Arms in 1967, also known as Short Term TRading INdex (TRIN), is a popular breadth indicator. It helps us to understand the buying and selling pressures in the market and acts as a valuable indicator to forecast the direction in which the market would move. \n When TRIN index crosses the Upper Band, it indicates a bearish sentiment. \n Similarly, when TRIN index crosses the Lower Band, it indicates a bullish sentiment.\n When TRIN index is around average, it is considered a balanced Market")

        #canvas and toolbar
        self.Figure = plt.figure(figsize=(15,5))
        self.Canvas = FigureCanvas(self.Figure)
        self.toolbar = NavigationToolbar(self.Canvas, self)
        grid.addWidget(self.Canvas, 2,0,1,2)
        grid.addWidget(self.toolbar, 1,0,1,2)
        
                
        #plotting the data
        plt.clf()
        sns.set(style="whitegrid")
        ax = self.Figure.add_subplot(111)
       
        self.Figure.suptitle('TRIN as on {} is {}'.format(self.data_date,Data['TRIN'].iloc[-1]))
        
        #plt.xticks(Data['Date'],check,Rotation=90)

        ax.plot(Data['Date'],Data['TRIN'])
        ax.plot(Data['mAvg'], label='Average TRIN')
        ax.plot(Data['UBB'], label='Upper Band')
        ax.plot(Data['LBB'], label='Upper Band')
        
        #print('No error till here')
        
        #print('No error')
        plt.xticks(rotation=90)
        ax.set_ylabel('TRIN Values')
                      
        ax.legend(loc='best')
        sns.despine()
        chart.showMaximized()
        self.Canvas.draw()

    def getbullInt(self):
        n = int(round(st,-2))
        i, okPressed = QInputDialog.getInt(self, "Target", "Enter your target of Nifty", n, 0, 50000, 50)
        if okPressed:
            self.bull(i)

    def getbearInt(self):
        n = int(round(st,-2))
        i, okPressed = QInputDialog.getInt(self, "Target", "Enter your target of Nifty", n, 0, 50000, 50)
        if okPressed:
            self.bear(i)
    
    '''
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
    '''
    

    def bull(self, target):
        """
        Bullish Strategies:

        1. Bull Call Spread 2. Bull Put Spread 3. Call Ratio Back Spread 4. Bear Call Ladder 5. Call Butterfly 6. Synthetic Call 7. Straps
        """
        #I will use the value in vtxt to do some calculations
        #target = vtxt
        #global edate
       
        if st > target:
            return QMessageBox.question(self, 'What the F', "Your Target {} is less than last closing price of Nifty : {}".format(target,st), QMessageBox.Ok, QMessageBox.Ok)
       
        
        #I will now call all the different types of bullish strategies and they will return their respective payoffs, which we will show to the user.
        bull_call_spread_data = self.bull_call_spread(st, target, udate, edate)
        bull_put_spread_data = self.bull_put_spread(st, target, udate, edate)
        
        
        
        #We will create a sub window with grid layout which will consist of labels each explaining the payoffs of different strategies
        payoff_win = QWidget()
        payoff_lay = QGridLayout()
        payoff_win.setLayout(payoff_lay)
        lblBCS = QLabel() #Bull Call spread Label
        lblBCS.setFont(QFont('SansSerif', 14))
        btnBCS = QPushButton('Pay off Chart')
        btnBCScus = QPushButton('Customise')
        btnBCSopt = QPushButton('Optimise')
        lblBPS = QLabel() #Bull Put Spread Label
        lblBPS.setFont(QFont('SansSerif', 14))
        btnBPS = QPushButton('Pay off Chart')
        btnBPScus = QPushButton('Customise')
        btnBPSopt = QPushButton('Optimise')
        payoff_win.setWindowTitle('Possible Bullish positions')
        payoff_lay.addWidget(lblBCS, 0,0)
        payoff_lay.addWidget(btnBCS, 0,1)
        payoff_lay.addWidget(btnBCScus, 0,2)
        payoff_lay.addWidget(btnBCSopt, 0,3)
        payoff_lay.addWidget(lblBPS, 1,0)
        payoff_lay.addWidget(btnBPS, 1,1)
        payoff_lay.addWidget(btnBPScus, 1,2)
        payoff_lay.addWidget(btnBPSopt, 1,3)
        self.mdi.addSubWindow(payoff_win)
        payoff_win.resize(payoff_win.sizeHint())
        payoff_lay.setSpacing(10)
        
        #Setting the label text with their respective details
        BCSprofit = max(self.bull_Call_spreadc) * 75
        BCSloss = min(self.bull_Call_spreadc) * 75
        lblBCS.setText("Bull Call Spread(Moderately Bullish): \n Buy 1 lot of Nifty {} Strike Price Call Option at around {} and Sell 1 lot of Nifty {} Strike Price Call Option at around {}\n For a Net debit of : {} \n The Maximum Profit of this strategy is : Rs.{}\n The Maximum Loss of this strategy is : Rs.{}\n Your Position will reach Breakeven if NIFTY closes at : {}".format(self.BCSbuy,self.BCSlong_call_premium,self.BCSsell,self.BCSshort_call_premium,self.BCSnet_debit,BCSprofit,BCSloss,self.BCSBreakeven))
        lblBPS.setText("Bull Put Spread(Moderately Bullish): \n Sell 1 lot of Nifty {} Strike Price Put Option at around {} and Buy 1 lot of Nifty {} Strike Price Put Option at around {}\n For a Net Credit of : {} \n The Maximum Profit of this strategy is : Rs.{}\n The Maximum Loss of this strategy is : Rs.{}\n Your Position will reach Breakeven if NIFTY closes at : {}".format(self.BPSsell,self.BPSshort_put_premium,self.BPSbuy,self.BPSlong_put_premium,self.BPSnet_credit,self.BPS_Profit,self.BPS_Loss,self.BPS_Breakeven))


        #connect a click event to the Buttons
        btnBCS.clicked.connect(lambda: self.show_charts(bull_call_spread_data))
        btnBCScus.clicked.connect(self.custom_bull_call_spread)
        btnBCSopt.clicked.connect(lambda: self.optimise_bull_call_spread(target))
        btnBPS.clicked.connect(lambda: self.show_charts(bull_put_spread_data))
        btnBPScus.clicked.connect(self.custom_bull_put_spread)
        btnBPSopt.setEnabled(False)

        
        payoff_win.showNormal()

    def bear(self, target):
        """
        Bearish Strategies:

        
        """
        
        if st < target:
            return QMessageBox.question(self, 'What the F', "Your Target {} is greater than last closing price of Nifty : {}".format(target,st), QMessageBox.Ok, QMessageBox.Ok)
       
        
        #I will now call all the different types of bearish strategies and they will return their respective payoffs, which we will show to the user.
        #bull_call_spread_data = self.bull_call_spread(st, target, udate, edate)
        bear_put_spread_data = self.bear_put_spread(st, target)
        bear_call_spread_data = self.bear_call_spread(st, target)
        
        
        
        #We will create a sub window with grid layout which will consist of labels each explaining the payoffs of different strategies
        payoff_win = QWidget()
        payoff_lay = QGridLayout()
        payoff_win.setLayout(payoff_lay)
        lblBRPS = QLabel() #Bear Put spread Label
        lblBRPS.setFont(QFont('SansSerif', 14))
        btnBRPS = QPushButton('Pay off Chart')
        btnBRPScus = QPushButton('Customise')
        btnBRPSopt = QPushButton('Optimise')
        lblBRCS = QLabel() #Bear Call Spread Label
        lblBRCS.setFont(QFont('SansSerif', 14))
        btnBRCS = QPushButton('Pay off Chart')
        btnBRCScus = QPushButton('Customise')
        btnBRCSopt = QPushButton('Optimise')
        payoff_win.setWindowTitle('Possible Bullish positions')
        payoff_lay.addWidget(lblBRPS, 0,0)
        payoff_lay.addWidget(btnBRPS, 0,1)
        payoff_lay.addWidget(btnBRPScus, 0,2)
        payoff_lay.addWidget(btnBRPSopt, 0,3)
        payoff_lay.addWidget(lblBRCS, 1,0)
        payoff_lay.addWidget(btnBRCS, 1,1)
        payoff_lay.addWidget(btnBRCScus, 1,2)
        payoff_lay.addWidget(btnBRCSopt, 1,3)
        self.mdi.addSubWindow(payoff_win)
        payoff_win.resize(payoff_win.sizeHint())
        payoff_lay.setSpacing(10)
        
        #Setting the label text with their respective details
        lblBRPS.setText("Bear Put Spread(Moderately Bearish on Market): \n Buy 1 lot of Nifty {} Strike Price Put Option at around {} and Sell 1 lot of Nifty {} Strike Price Put Option at around {}\n For a Net debit of : {} \n The Maximum Profit of this strategy is : Rs.{}\n The Maximum Loss of this strategy is : Rs.{}\n Your Position will reach Breakeven if NIFTY closes at : {}".format(self.BRPSbuy,self.BRPSlongpremium ,self.BRPSsell ,self.BRPSshortpremium ,self.BRPSnetdebit ,self.BRPSprofit ,self.BRPSloss ,self.BRPSbreakeven ))
        #lblBPS.setText("Bull Put Spread: \n Sell 1 lot of Nifty {} Strike Price Put Option at around {} and Buy 1 lot of Nifty {} Strike Price Put Option at around {}\n For a Net Credit of : {} \n The Maximum Profit of this strategy is : Rs.{}\n The Maximum Loss of this strategy is : Rs.{}\n Your Position will reach Breakeven if NIFTY closes at : {}".format(self.BPSsell,self.BPSshort_put_premium,self.BPSbuy,self.BPSlong_put_premium,self.BPSnet_credit,self.BPS_Profit,self.BPS_Loss,self.BPS_Breakeven))
        lblBRCS.setText("Bear Call Spread(Mildly Bearish on Market): \n Sell 1 lot of Nifty {} Strike Price Put Option at around {} and Buy 1 lot of Nifty {} Strike Price Put Option at around {} \n For a Net Credit of : {} \n The Maximum Profit of this strategy is : Rs.{}\n The Maximum Loss of this strategy is : Rs.{}\n Your Position will reach Breakeven if NIFTY closes at : {}".format(self.BRCSsell,self.BRCSshort_call_premium,self.BRCSbuy,self.BRCSlong_call_premium,self.BRCSnetcredit,self.BRCSprofit,self.BRCSloss,self.BRCSbreakeven))

        #connect a click event to the Buttons
        btnBRPS.clicked.connect(lambda: self.show_charts(bear_put_spread_data))
        btnBRPScus.clicked.connect(self.custom_bear_put_spread)
        #btnBCSopt.clicked.connect(lambda: self.optimise_bull_call_spread(target))
        btnBRCS.clicked.connect(lambda: self.show_charts(bear_call_spread_data))
        btnBRCScus.clicked.connect(self.custom_bear_call_spread)

        payoff_win.showNormal()
        
    def show_charts(self, all_datas):
        self.data_list = all_datas
        #this part will create a GUI where I will show the chart and Table containing the DataFrame of the payouts
        chart = QWidget()
        grid = QGridLayout()
        chart.setLayout(grid)
        self.mdi.addSubWindow(chart)
        #self.setGeometry(600,300, 1000, 600)
        

        #canvas and toolbar
        self.Figure = plt.figure(figsize=(15,5))
        self.Canvas = FigureCanvas(self.Figure)
        self.toolbar = NavigationToolbar(self.Canvas, self)
        grid.addWidget(self.Canvas, 2,0,1,2)
        grid.addWidget(self.toolbar, 1,0,1,2)

        #creating a table
        s = self.data_list.shape
        rows_lenght = s[0]
        columns_lenght = s[1]
        self.Table = QTableWidget(self)
        self.Table.setRowCount(rows_lenght)
        self.Table.setColumnCount(columns_lenght)
        grid.addWidget(self.Table, 3,0,1,2)
        '''
        #Next Button
        next_btn = QPushButton('Plot', self)
        next_btn.resize(next_btn.sizeHint())
        grid.addWidget(next_btn, 0,0)
        next_btn.clicked.connect(self.plot_bull_call_spread)
        #Exit Button
        explain_btn = QPushButton('Exit', self)
        explain_btn.resize(explain_btn.sizeHint())
        explain_btn.clicked.connect(chart.close)
        grid.addWidget(explain_btn, 0,1)
        '''
        tcol = self.data_list.columns.tolist()
        if 'Bull_Call_Spread' in tcol:
            self.plot_bull_call_spread()
        elif 'Bull_Put_Spread' in tcol:
            self.plot_bull_put_spread()
        elif 'Bear_Put_Spread' in tcol:
            self.plot_bear_put_spread()
        elif 'Bear_Call_Spread' in tcol:
            self.plot_bear_call_spread()

        chart.showMaximized()

    #-----------------------------------BULL CALL SPREAD SECTION------------------------------------------------
    def bull_call_spread(self, lcsp, scsp, udate, edate):
        
        #get the premium of the short call
        
        short_call_strike_price = scsp

        sp = (CE['STRIKE_PR'] == short_call_strike_price).nonzero()
        short_call_premium = CE.loc[int(sp[0]),'CLOSE']

        #set the long call strike price approximately
        if lcsp == st:        
            rst = round(st, -2)
            if rst >= st:
                long_call_strike_price = rst
            else:
                long_call_strike_price = rst + 50
        else:
            long_call_strike_price = lcsp        
        
        z = (CE['STRIKE_PR'] == long_call_strike_price).nonzero()
        long_call_premium = CE.loc[int(z[0]),'CLOSE']

        #setting the price range in which pay off is calculated
        sT = np.arange(long_call_strike_price-200,short_call_strike_price+300,50)

        long_call_payoff = call_payoff(sT, long_call_strike_price, long_call_premium)
        
        short_call_payoff = call_payoff(sT, short_call_strike_price, short_call_premium) * -1.0
        
        self.bull_Call_spreadc = long_call_payoff + short_call_payoff
        
        df = pd.DataFrame({'Nifty_Spot_Price':sT,
                           'Long_Call_Payoff':long_call_payoff,
                           'Short_Call_Payoff':short_call_payoff,
                           'Bull_Call_Spread':self.bull_Call_spreadc})
        df = df[['Nifty_Spot_Price','Long_Call_Payoff','Short_Call_Payoff','Bull_Call_Spread']]        
        """df.set_index('Nifty_Spot_Price', inplace=True)"""
        self.BCSBreakeven = long_call_strike_price + (long_call_premium - short_call_premium)
        self.BCSbuy = long_call_strike_price
        self.BCSsell = short_call_strike_price
        self.BCSlong_call_premium = long_call_premium
        self.BCSshort_call_premium = short_call_premium
        self.BCSnet_debit = long_call_premium - short_call_premium
        return df
        
    def plot_bull_call_spread(self):
        plt.clf()
        sns.set(style="ticks")
        x = self.data_list
        x_axis_data = x['Nifty_Spot_Price']
        y_axis_data1 = x['Bull_Call_Spread']
        y_long_call_payoff = x['Long_Call_Payoff']
        y_short_call_payoff = x['Short_Call_Payoff']
        ax = self.Figure.add_subplot(111)
        ax.spines['bottom'].set_position('zero')
        self.Figure.suptitle('Bull Call Spread')
        ax.plot(x_axis_data,y_long_call_payoff,'--',label='Long Call Payoff',color='g')
        ax.plot(x_axis_data,y_short_call_payoff,'--',label='Short Call Payoff',color='r')
        
        ax.plot(x_axis_data, y_axis_data1, label = 'Bull Call Spread')
        ax.set_xlabel('NIFTY Index Values')
        ax.set_ylabel('Profit and loss')
        ax.legend(loc='best')
        sns.despine()
        self.Canvas.draw()

        #table the data
        for i in range(len(self.data_list.index)):
            for j in range(len(self.data_list.columns)):
                self.Table.setItem(i, j, QTableWidgetItem(str(self.data_list.iloc[i, j])))
        cols = self.data_list.columns.tolist()
        self.Table.setHorizontalHeaderLabels(cols)
        self.Table.verticalHeader().setVisible(False)

        self.Table.resizeColumnsToContents()
        self.Table.resizeRowsToContents()
 
    def custom_bull_call_spread(self):
        try:
            n = int(round(st,-2))
            i, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the strike price of Call option that you want to buy", n, 0, 50000, 50)
            if okPressed:
                lcsp = i
            n = lcsp + 100
            j, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the strike price of the call option that you want to sell", n, 0, 50000, 50)
            if okPressed:
                scsp = j

            if scsp <= lcsp:
                return QMessageBox.question(self, 'What the F', "For a Bull Call Spread you buy a lower strike call and sell a higher strike call, since the strike price you have selected doesn't fit this criteria, I will suggest you to study about options strategies and then use the customize feature", QMessageBox.Ok, QMessageBox.Ok)
            else:
                zz = self.bull_call_spread(lcsp, scsp, udate, edate)
                QMessageBox.information(self, 'Customized Bull Call Spread', "As per the customisation :\n Buy {} Strike Call Option and Sell {} Strike Call Option \n This spread will hit breakeven at: {}".format(self.BCSbuy,self.BCSsell,self.BCSBreakeven), QMessageBox.Ok, QMessageBox.Ok)
                self.show_charts(zz)
        except:
            pass        

    def optimise_bull_call_spread(self, target, lot = 1):
        #optimisation is done based on the amount of risk the user is willing to take.
        nifty = int(round(st,-2))
        range_of_analysis = np.arange(nifty-300,target,50)
        range_of_payoff = np.arange(nifty-200,target+200,50)

        sp = (CE['STRIKE_PR'] == target).nonzero()
        short_call_premium = CE.loc[int(sp[0]),'CLOSE']
        short_call_payoff = call_payoff(range_of_payoff,target,short_call_premium) * -1.0
        output = []
        for s in range_of_analysis:
            z = (CE['STRIKE_PR'] == s).nonzero()
            long_call_premium = CE.loc[int(z[0]),'CLOSE']
            bcs_profit = abs(target - s) - (long_call_premium - short_call_premium)
            loss = long_call_premium - short_call_premium
            d = [s,target,bcs_profit,loss]
            output.append(d)

        bcsdf = pd.DataFrame(output, columns=['Long_Call_Strike','Short_Call_Strike','Profit','Risk'])
        bcsdf['Risk_lot'] = bcsdf['Risk'].apply(lambda x: x*75*lot)

        i, okPressed = QInputDialog.getInt(self, "Risk", "Enter the amount that you are willing to risk? Example 3000",2000)
        if okPressed:
            bcsdf = bcsdf[bcsdf['Risk_lot'] <= i]
            bcsdf = bcsdf.reset_index(drop=True)
            min_risk = max(bcsdf['Risk_lot'])
            p = (bcsdf['Risk_lot'] == min_risk).nonzero()
            long_call_SP = bcsdf.loc[int(p[0]),'Long_Call_Strike']
            z = (CE['STRIKE_PR'] == long_call_SP).nonzero()
            long_call_premium = CE.loc[int(z[0]),'CLOSE']
            long_call_payoff = call_payoff(range_of_payoff,long_call_SP,long_call_premium)
            bcs_payoff = long_call_payoff + short_call_payoff
            bdf = pd.DataFrame({'Nifty_Spot_Price':range_of_payoff,
                                    'Long_Call_Payoff':long_call_payoff,
                                    'Short_Call_Payoff':short_call_payoff,
                                    'Bull_Call_Spread':bcs_payoff})
            bdf = bdf[['Nifty_Spot_Price','Long_Call_Payoff','Short_Call_Payoff','Bull_Call_Spread']]
            QMessageBox.information(self, 'Optimized based on Risk specified by the user', "As per the optimisation :\n Buy {} Strike Call Option and Sell {} Strike Call Option \n This spread will have the risk of Rs.{} for your Target of : {}".format(long_call_SP,target,round(min_risk),target), QMessageBox.Ok, QMessageBox.Ok)
            self.show_charts(bdf)
        
    #------------------------------------BULL PUT SPREAD SECTION-------------------------------------------------
    def bull_put_spread(self, lpsp, spsp, udate, edate):
        """
        Buy one lower OTM Put
        Sell one OTM/ITM Put
        when to use: when the investoru is moderately bullish
        risk = Limited to difference between the two strike price - net premium received
        reward = limited to net premium received
        Breakeven = Strike Price of the Short Put - Net Premium Received
        """
        #st is Nifty's latest close price
        short_put_strike_price = spsp
        if lpsp == st:
            rst = round(lpsp, -2)
            if rst >= lpsp:
                long_put_strike_price = rst - 50
            else:
                long_put_strike_price = rst
        else:
            long_put_strike_price = lpsp

        #spdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='PE',expiry_date=edate,strike_price=short_put_strike_price)
        #short_put_premium = spdata.loc[udate,'Close']
        sp = (PE['STRIKE_PR'] == short_put_strike_price).nonzero()
        short_put_premium = PE.loc[int(sp[0]),'CLOSE']
        
        #lpdata = ns.get_history(symbol='NIFTY',start=udate,end=udate,index=True,option_type='PE',expiry_date=edate,strike_price=long_put_strike_price)
        #long_put_premium = lpdata.loc[udate,'Close']
        z = (PE['STRIKE_PR'] == long_put_strike_price).nonzero()
        long_put_premium = PE.loc[int(z[0]),'CLOSE']
       
        #setting the range in which the Bull put spread will be calculated
        pT = np.arange(long_put_strike_price-200,short_put_strike_price+200,50)

        long_put_payoff = put_payoff(pT,long_put_strike_price,long_put_premium)
        short_put_payoff = put_payoff(pT,short_put_strike_price,short_put_premium) * -1.0

        self.bull_put_spreadc = long_put_payoff + short_put_payoff

        df1 = pd.DataFrame({'Nifty_Spot_Price':pT,
                           'Long_Put_Payoff':long_put_payoff,
                           'Short_Put_Payoff':short_put_payoff,
                           'Bull_Put_Spread':self.bull_put_spreadc})
        df1 = df1[['Nifty_Spot_Price','Long_Put_Payoff','Short_Put_Payoff','Bull_Put_Spread']]  
        self.BPS_Profit = (short_put_premium - long_put_premium) * 75
        self.BPS_Loss = (((short_put_strike_price - long_put_strike_price) - (short_put_premium - long_put_premium )) * 75) * -1
        self.BPS_Breakeven = short_put_strike_price - (short_put_premium - long_put_premium)
        self.BPSbuy = long_put_strike_price
        self.BPSsell = short_put_strike_price
        self.BPSshort_put_premium = short_put_premium
        self.BPSlong_put_premium = long_put_premium
        self.BPSnet_credit = (short_put_premium - long_put_premium)
        return df1

    def plot_bull_put_spread(self):
        plt.clf()
        sns.set(style="ticks")
        x = self.data_list
        x_axis_data = x['Nifty_Spot_Price']
        y_axis_data1 = x['Bull_Put_Spread']
        y_long_put_payoff = x['Long_Put_Payoff']
        y_short_put_payoff = x['Short_Put_Payoff']
        ax = self.Figure.add_subplot(111)
        ax.spines['bottom'].set_position('zero')
        self.Figure.suptitle('Bull Put Spread')
        ax.plot(x_axis_data,y_long_put_payoff,'--',label='Long Put Payoff',color='g')
        ax.plot(x_axis_data,y_short_put_payoff,'--',label='Short Put Payoff',color='r')
        
        ax.plot(x_axis_data, y_axis_data1, label = 'Bull Put Spread')
        ax.set_xlabel('NIFTY Index Values')
        ax.set_ylabel('Profit and loss')
        ax.legend(loc='best')
        sns.despine()
        self.Canvas.draw()

        #table the data
        for i in range(len(self.data_list.index)):
            for j in range(len(self.data_list.columns)):
                self.Table.setItem(i, j, QTableWidgetItem(str(self.data_list.iloc[i, j])))
        cols = self.data_list.columns.tolist()
        self.Table.setHorizontalHeaderLabels(cols)
        self.Table.verticalHeader().setVisible(False)

        self.Table.resizeColumnsToContents()
        self.Table.resizeRowsToContents()
    
    def custom_bull_put_spread(self):
        try:
            n = int(round(st,-2))
            i, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of Put option that you want to Sell/Short", n, 0, 50000, 50)
            if okPressed:
                spsp = i
            n = spsp - 100
            j, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of the Put option that you want to Buy/Long", n, 0, 50000, 50)
            if okPressed:
                lpsp = j

            if spsp >= lpsp:
                return QMessageBox.question(self, 'What the F', "For a Bull Put Spread you sell a higher strike Put and then buy a lower strike put to limit the loss of a short put position, since the strike price you have selected doesn't fit this criteria, I will suggest you to study about options strategies and then use the customize feature", QMessageBox.Ok, QMessageBox.Ok)
            else:
                zz = self.bull_put_spread(lpsp, spsp, udate, edate)
                QMessageBox.information(self, 'Customized Bull Put Spread', "As per the customisation :\n Sell {} Strike Put Option and Buy {} Strike Put Option \n This spread will hit breakeven at: {}".format(self.BPSsell,self.BPSbuy,self.BPS_Breakeven), QMessageBox.Ok, QMessageBox.Ok)
                self.show_charts(zz)
        except:
            pass        
    #------------------------------------CALL RATIO BACK SECTION-------------------------------------------------
    def call_ratio_back_spread(self):
        """
         Spread = Higher Strike – Lower Strike
         Net Credit = Premium Received for lower strike – 2*Premium of higher strike
         Max Loss = Spread – Net Credit
         Max Loss occurs at = Higher Strike
         The payoff when market goes down = Net Credit
         Lower Breakeven = Lower Strike + Net Credit
         Upper Breakeven = Higher Strike + Max Loss
        Call ratio back spread works best when you
        sell slightly ITM option and buy slightly OTM option when there is ample time to
        expiry.
        If this strategy is implemented during second half of the month then the best strikes to opt are deep ITM and slightly ITM
        """
        """
        1. The Call Ratio Backspread is best executed when your outlook on the stock/index is bullish 
        2. The strategy requires you to sell 1 ITM CE and buy 2 OTM CE, and this is to be executed in the same ratio i.e for every 1 sold option, 2 options have to be purchased 
        3. The strategy is usually executed for a ‘net Credit’ 
        4. The strategy makes limited money if the stock price goes down, and unlimited profit if the stock price goes up. The loss is pre defined 
        5. There are two break even points – lower breakeven and upper breakeven points 
        6. Spread = Higher Strike – Lower Strike 
        7. Net Credit = Premium Received for lower strike – 2*Premium of higher strike 
        8. Max Loss = Spread – Net Credit 
        9. Max Loss occurs at = Higher Strike 
        10. The payoff when market goes down = Net Credit 
        11. Lower Breakeven = Lower Strike + Net Credit 
        12. Upper Breakeven = Higher Strike + Max Loss 
        13. Irrespective of the time to expiry opt for slightly ITM + Slightly OTM combination of strikes 
        14. Increase in volatility is good for this strategy when there is more time to expiry, but when there is less time to expiry, increase in volatility is not really good for this strategy. 
        """
    #-------------------------------------BEAR PUT SPREAD SECTION------------------------------------------------
    def bear_put_spread(self, lpsp, spsp):
        """
        Generally, Buy 1 ITM put option
              and  Sell 1 OTM put option

        when to use: when you are moderately bearish on the market direction
        Risk : limited to the net debit
        Reward = limited to the difference between the strike prices - net debit
        Breakeven = Strike Price of long put - net debit
        """

        if lpsp == st:
            n = int(round(lpsp,-2))
            if n >= lpsp:
                long_put_strike_price = n
            else:
                long_put_strike_price = n + 50
        else:
            long_put_strike_price = lpsp
        
       
        short_put_strike_price = spsp
        z = (PE['STRIKE_PR'] == long_put_strike_price).nonzero()
        long_put_premium = PE.loc[int(z[0]),'CLOSE']
        sp = (PE['STRIKE_PR'] == short_put_strike_price).nonzero()
        short_put_premium = PE.loc[int(sp[0]),'CLOSE']

        #setting the range in which the Bull put spread will be calculated
        pT = np.arange(short_put_strike_price-200,long_put_strike_price+200,50)

        #calculating the payoffs of each option position
        long_put_payoff = put_payoff(pT,long_put_strike_price,long_put_premium)
        short_put_payoff = put_payoff(pT,short_put_strike_price,short_put_premium) * -1.0

        bear_put_spread = long_put_payoff + short_put_payoff

        df1 = pd.DataFrame({'Nifty_Spot_Price':pT,
                           'Long_Put_Payoff':long_put_payoff,
                           'Short_Put_Payoff':short_put_payoff,
                           'Bear_Put_Spread':bear_put_spread})
        df1 = df1[['Nifty_Spot_Price','Long_Put_Payoff','Short_Put_Payoff','Bear_Put_Spread']]
        self.BRPSloss = (long_put_premium - short_put_premium) * 75 * -1
        self.BRPSprofit = ((long_put_strike_price - short_put_strike_price) - (long_put_premium - short_put_premium)) * 75
        self.BRPSbreakeven = long_put_strike_price - (long_put_premium - short_put_premium)
        self.BRPSbuy = long_put_strike_price
        self.BRPSsell = short_put_strike_price
        self.BRPSnetdebit = (long_put_premium - short_put_premium)
        self.BRPSlongpremium = long_put_premium
        self.BRPSshortpremium = short_put_premium
        return df1

    def plot_bear_put_spread(self):
        plt.clf()
        sns.set(style="ticks")
        x = self.data_list
        x_axis_data = x['Nifty_Spot_Price']
        y_axis_data1 = x['Bear_Put_Spread']
        y_long_put_payoff = x['Long_Put_Payoff']
        y_short_put_payoff = x['Short_Put_Payoff']
        ax = self.Figure.add_subplot(111)
        ax.spines['bottom'].set_position('zero')
        self.Figure.suptitle('Bear Put Spread')
        ax.plot(x_axis_data,y_long_put_payoff,'--',label='Long Put Payoff',color='g')
        ax.plot(x_axis_data,y_short_put_payoff,'--',label='Short Put Payoff',color='r')
        
        ax.plot(x_axis_data, y_axis_data1, label = 'Bear Put Spread')
        ax.set_xlabel('NIFTY Index Values')
        ax.set_ylabel('Profit and loss')
        ax.legend(loc='best')
        sns.despine()
        self.Canvas.draw()

        #table the data
        for i in range(len(self.data_list.index)):
            for j in range(len(self.data_list.columns)):
                self.Table.setItem(i, j, QTableWidgetItem(str(self.data_list.iloc[i, j])))
        cols = self.data_list.columns.tolist()
        self.Table.setHorizontalHeaderLabels(cols)
        self.Table.verticalHeader().setVisible(False)

        self.Table.resizeColumnsToContents()
        self.Table.resizeRowsToContents()
    
    def custom_bear_put_spread(self):
        try:
            n = int(round(st,-2))
            i, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of Put option that you want to Buy/Long", n, 0, 50000, 50)
            if okPressed:
                lpsp = i
            n = lpsp - 100
            j, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of the Put option that you want to Sell/Short", n, 0, 50000, 50)
            if okPressed:
                spsp = j

            if spsp >= lpsp:
                return QMessageBox.question(self, 'What the F', "For a Bear Put Spread you buy a higher strike Put and then sell a lower strike Put, since the strike price you have selected doesn't fit this criteria, I will suggest you to study about options strategies and then use the customize feature", QMessageBox.Ok, QMessageBox.Ok)
            else:
                zz = self.bear_put_spread(lpsp, spsp)
                QMessageBox.information(self, 'Customized Bear Put Spread', "As per the customisation :\n Buy {} Strike Put Option and Sell {} Strike Put Option \n This spread will hit breakeven at: {}".format(self.BRPSbuy,self.BRPSsell,self.BRPSbreakeven), QMessageBox.Ok, QMessageBox.Ok)
                self.show_charts(zz)
        except:
            pass        
    #--------------------------------------BEAR CALL SPREAD SECTION----------------------------------------------
    def bear_call_spread(self,sitmc,botmc):
        short_call_strike_price = botmc

        if sitmc == st:
            rst = round(sitmc, -2)
            if rst >= sitmc:
                long_call_strike_price = rst
            else:
                long_call_strike_price = rst + 50
        else:
            long_call_strike_price = sitmc

        sp = (CE['STRIKE_PR'] == short_call_strike_price).nonzero()
        short_call_premium = CE.loc[int(sp[0]),'CLOSE']
        z = (CE['STRIKE_PR'] == long_call_strike_price).nonzero()
        long_call_premium = CE.loc[int(z[0]),'CLOSE']

        #setting the price range in which pay off is calculated
        sT = np.arange(long_call_strike_price-300,short_call_strike_price+300,50)
        
        long_call_payoff = call_payoff(sT, long_call_strike_price, long_call_premium)
        
        short_call_payoff = call_payoff(sT, short_call_strike_price, short_call_premium) * -1.0
        
        bear_call_spread = long_call_payoff + short_call_payoff

        df = pd.DataFrame({'Nifty_Spot_Price':sT,
                           'Long_Call_Payoff':long_call_payoff,
                           'Short_Call_Payoff':short_call_payoff,
                           'Bear_Call_Spread':bear_call_spread})
        df = df[['Nifty_Spot_Price','Long_Call_Payoff','Short_Call_Payoff','Bear_Call_Spread']]
        self.BRCSloss = ((long_call_strike_price - short_call_strike_price)-(short_call_premium - long_call_premium)) * 75 * -1
        self.BRCSprofit = (short_call_premium - long_call_premium) * 75
        self.BRCSbreakeven = short_call_strike_price + (short_call_premium - long_call_premium)
        self.BRCSbuy = long_call_strike_price
        self.BRCSsell = short_call_strike_price
        self.BRCSnetcredit = (short_call_premium - long_call_premium)
        self.BRCSlong_call_premium = long_call_premium
        self.BRCSshort_call_premium = short_call_premium

        return df

    def plot_bear_call_spread(self):
        plt.clf()
        sns.set(style="ticks")
        x = self.data_list
        x_axis_data = x['Nifty_Spot_Price']
        y_axis_data1 = x['Bear_Call_Spread']
        y_long_call_payoff = x['Long_Call_Payoff']
        y_short_call_payoff = x['Short_Call_Payoff']
        ax = self.Figure.add_subplot(111)
        ax.spines['bottom'].set_position('zero')
        self.Figure.suptitle('Bear Call Spread')
        ax.plot(x_axis_data,y_long_call_payoff,'--',label='Long Call Payoff',color='g')
        ax.plot(x_axis_data,y_short_call_payoff,'--',label='Short Call Payoff',color='r')
        
        ax.plot(x_axis_data, y_axis_data1, label = 'Bear Call Spread')
        ax.set_xlabel('NIFTY Index Values')
        ax.set_ylabel('Profit and loss')
        ax.legend(loc='best')
        sns.despine()
        self.Canvas.draw()

        #table the data
        for i in range(len(self.data_list.index)):
            for j in range(len(self.data_list.columns)):
                self.Table.setItem(i, j, QTableWidgetItem(str(self.data_list.iloc[i, j])))
        cols = self.data_list.columns.tolist()
        self.Table.setHorizontalHeaderLabels(cols)
        self.Table.verticalHeader().setVisible(False)

        self.Table.resizeColumnsToContents()
        self.Table.resizeRowsToContents()

    def custom_bear_call_spread(self):
        try:
            n = int(round(st,-2))
            i, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of Call option that you want to Sell/Short", n, 0, 50000, 50)
            if okPressed:
                scsp = i
            n = scsp + 100
            j, okPressed = QInputDialog.getInt(self, "User's Strike Price", "Enter the Strike Price of the Call option that you want to Buy/Long", n, 0, 50000, 50)
            if okPressed:
                lcsp = j

            if scsp >= lcsp:
                return QMessageBox.question(self, 'What the F', "For a Bear Call Spread you sell a lower strike call and buy a higher strike call, since the strike price you have selected doesn't fit this criteria, I will suggest you to study about options strategies and then use the customize feature", QMessageBox.Ok, QMessageBox.Ok)
            else:
                zz = self.bear_call_spread(lcsp, scsp)
                QMessageBox.information(self, 'Customized Bear Call Spread', "As per the customisation :\n Sell {} Strike Call Option and Buy {} Strike Call Option \n This spread will hit breakeven at: {}".format(self.BRCSsell,self.BRCSbuy,self.BRCSbreakeven), QMessageBox.Ok, QMessageBox.Ok)
                self.show_charts(zz)
        except:
            pass        
    #-------------------------------------OPTION PAIN SECTION-----------------------------------------------------
    def option_pain(self):
        max = self.get_maxpain(debhav)
        plot = self.chart_maxpain(max)

    def get_maxpain(self,df,s='NIFTY',expdate = None):
        #print(expdate)
        #df = pd.read_excel('derivativesbhav.xlsx')
        data_date = df['TIMESTAMP'].iloc[1]
        #df.set_index('SYMBOL', inplace = True)
        #fil_inst = df['INSTRUMENT'].isin(['OPTIDX'])
        temp_df = df#[fil_inst]
        fil_symb = temp_df['SYMBOL'].isin([s])
        temp2_df = temp_df[fil_symb]
        
        CE = temp2_df[temp2_df['OPTION_TYP']=='CE']
        PE = temp2_df[temp2_df['OPTION_TYP']=='PE']
       
        CE = CE.reset_index(drop=True)
        PE = PE.reset_index(drop=True)
        Output_df = pd.DataFrame()
        Output_df['SYMBOL'] = CE['SYMBOL']
        Output_df['STRIKE_PRICE'] = CE['STRIKE_PR']
        Output_df['EXPIRY_DATE'] = CE['EXPIRY_DT']
        Output_df['CALL_OI'] = CE['OPEN_INT']
        Output_df['PUT_OI'] = PE['OPEN_INT']
        Output_df['Call_Close'] = CE['CLOSE']
        Output_df['Put_Close'] = PE['CLOSE']
        Output_df['DATA_DATE'] = CE['TIMESTAMP']
        Output_df.set_index('STRIKE_PRICE', inplace=True)
        Output_df.to_excel('Output.xlsx')
        Output_df = pd.read_excel('Output.xlsx')
        if expdate == None:
            for e in Output_df['EXPIRY_DATE']:
                expdate = e
                break
        test_df = Output_df[Output_df['EXPIRY_DATE']==expdate]
        #test_df.to_excel('Filtered Option.xlsx')
        #test_df = pd.read_excel('Filtered Option.xlsx')
        
        na_date = test_df['DATA_DATE'].iloc[1]
        val = {'CALL_OI':0.0,'PUT_OI':0.0,'DATA_DATE':na_date}
        test_df = test_df.fillna(value=val)


        for s in test_df.index:
            #run the loop assuming the market expires at that strike price
            total_Money_lost_by_CallWriters = 0
            total_Money_lost_by_PutWriters = 0
            for e in test_df.index:
                if s < e:
                    difference = e - s
                    call_loss = 0
                    put_loss = (test_df.loc[e,'PUT_OI']) * difference
                    total_Money_lost_by_CallWriters = total_Money_lost_by_CallWriters + call_loss
                    total_Money_lost_by_PutWriters = total_Money_lost_by_PutWriters + put_loss
                elif s > e:
                    difference = s - e
                    call_loss = (test_df.loc[e,'CALL_OI']) * difference
                    put_loss = 0
                    total_Money_lost_by_CallWriters = total_Money_lost_by_CallWriters + call_loss
                    total_Money_lost_by_PutWriters = total_Money_lost_by_PutWriters + put_loss
                else:
                    call_loss = 0
                    put_loss = 0
                    total_Money_lost_by_CallWriters = total_Money_lost_by_CallWriters + call_loss
                    total_Money_lost_by_PutWriters = total_Money_lost_by_PutWriters + put_loss
    
    
            test_df.loc[s,'LOSS_OF_CALL_WRITERS'] = total_Money_lost_by_CallWriters
            test_df.loc[s,'LOSS_OF_PUT_WRITERS'] = total_Money_lost_by_PutWriters
            test_df.loc[s,'TOTAL_LOSS'] = total_Money_lost_by_CallWriters + total_Money_lost_by_PutWriters
        '''
        test_df.to_excel('MaxPain.xlsx')

        test_df = pd.read_excel('MaxPain.xlsx')
        '''
        return test_df

    def chart_maxpain(self,test_df):
        v1 = test_df[test_df['TOTAL_LOSS'] == min(test_df['TOTAL_LOSS'])].index.tolist()
        self.v2 = test_df.loc[v1[0],'STRIKE_PRICE']
        self.contract = test_df.loc[v1[0],'SYMBOL']
        #this part will create a GUI where I will show the chart and Table containing the DataFrame of the payouts
        chart = QWidget()
        grid = QGridLayout()
        chart.setLayout(grid)
        self.mdi.addSubWindow(chart)
        #self.setGeometry(600,300, 1000, 600)
        chart.setToolTip("Here is how optionspain.com formally defines Option Pain – “In the options market, wealth transfer between option buyers and sellers is a zero sum game. \nOn option expiration days, the underlying stock price often moves toward a point that brings maximum loss to option buyers. This specific price, calculated based on all outstanding options in the markets, is called Option Pain.\n Option Pain is a proxy for the stock price manipulation target by the option selling group”. ")

        #canvas and toolbar
        self.Figure = plt.figure(figsize=(15,5))
        self.Canvas = FigureCanvas(self.Figure)
        self.toolbar = NavigationToolbar(self.Canvas, self)
        grid.addWidget(self.Canvas, 3,0,1,2)
        grid.addWidget(self.toolbar, 2,0,1,2)

        
        #Suggestion Button
        sugg_btn = QPushButton('Suggested Action', self)
        sugg_btn.resize(sugg_btn.sizeHint())
        grid.addWidget(sugg_btn, 1,0)
        sugg_btn.clicked.connect(lambda: self.suggestion_pain(self.v2,self.contract))
        #Plot Button
        explain_btn = QPushButton('Plot', self)
        explain_btn.resize(explain_btn.sizeHint())
        explain_btn.clicked.connect(self.exp_date_selection)
        grid.addWidget(explain_btn, 1,1)
        
        #Combo boxes to list the datas and the expiry dates
        self.instruments = QComboBox()
        grid.addWidget(self.instruments, 0,0)
        
        self.exp_dates = QComboBox()
        grid.addWidget(self.exp_dates, 0,1)

        #logic to add items in the QComboBox Widgets
        list_symbol = []
        list_exp_dates = []
        lim = []
        #first adding the indexes
        fil_inst = debhav['INSTRUMENT'].isin(['OPTIDX'])
        temp_df = debhav[fil_inst]
        for sym in temp_df['SYMBOL']:
            
            if not sym in lim:
                list_symbol.append(sym)
                lim.append(sym)

        #Now adding the list of stocks
        fil_inst = debhav['INSTRUMENT'].isin(['OPTSTK'])
        temp_df = debhav[fil_inst]
        for sym in temp_df['SYMBOL']:
            #first add the name of the symbol to the list
            if not sym in lim:
                list_symbol.append(sym)
                lim.append(sym)

        #set the initial list for expiry dates of Nifty
        temp_df = debhav#[fil_inst]
        fil_symb = temp_df['SYMBOL'].isin(['NIFTY'])
        temp2_df = temp_df[fil_symb]
        CE = temp2_df[temp2_df['OPTION_TYP']=='CE']
        
        for e in CE['EXPIRY_DT']:
            if not e in lim:
                list_exp_dates.append(e)
                lim.append(e)
        
        self.exp_dates.addItems(list_exp_dates)

        self.instruments.addItems(list_symbol)
        self.instruments.setCurrentIndex(2)
        self.instruments.currentIndexChanged.connect(self.selection_change)
        
        
        dd = self.plot_option_pain(test_df)
        chart.showMaximized()

    def plot_option_pain(self,test_df):
        test_df = test_df.reset_index(drop=True)
        #Calculate the PCR
        total_put_OI = np.sum(test_df['PUT_OI'])
        total_call_OI = np.sum(test_df['CALL_OI'])
        PCR = total_put_OI/total_call_OI

        #now plot the data
        plt.clf()
       
        #sns.set(style="whitegrid")
        ax = self.Figure.add_subplot(111)
        v1 = test_df[test_df['TOTAL_LOSS'] == min(test_df['TOTAL_LOSS'])].index.tolist()
        
        self.v2 = test_df.loc[v1[0],'STRIKE_PRICE']
        self.contract = test_df.loc[v1[0],'SYMBOL']
        self.Figure.suptitle('Option Pain Chart for Expiry Date {} as on {} \n Lowest Pain to Option writers will occur if the {} closes at {} and the PCR is {}'.format(test_df['EXPIRY_DATE'].iloc[1],test_df['DATA_DATE'].iloc[1],test_df['SYMBOL'].iloc[1], self.v2, PCR))
        
        x_axis_data = np.arange(len(test_df.index))

        y_axis_call = test_df['LOSS_OF_CALL_WRITERS']
        y_axis_put = test_df['LOSS_OF_PUT_WRITERS']
       
        bar_width = 0.3
        opacity = 0.5
        zz=test_df['STRIKE_PRICE']
        call_chart = plt.bar(x_axis_data,y_axis_call,bar_width,opacity,color='b',label='Call Pain')
        put_chart = plt.bar(x_axis_data + bar_width,y_axis_put,bar_width,color='r',label='Put Pain')
        ax.plot(test_df['TOTAL_LOSS'],'y.-',label='Pain Line', markevery=v1, marker='o', markerfacecolor='blue', markersize=10)
        plt.xlabel('Strike Prices')
        plt.ylabel('Pain')
               
        plt.xticks(x_axis_data + bar_width / 2,zz)

        ax.legend(loc='best')
        plt.tight_layout()
        sns.despine()
        
        self.Canvas.draw()
        
    def volatility(self, symb='NIFTY'):
        #global avg_return, volatility 
        temp_data = ns.get_history(symbol=symb,start=date(2015,1,1),end=udate,index = True)
        if temp_data.empty:
            temp_data = ns.get_history(symbol=symb,start=date(2015,1,1),end=udate,index = False)
        temp_data['Prev Close'] = temp_data['Close'].shift(1)
        close_price = temp_data['Close']
        prev_close = temp_data['Prev Close']

        #calculation part
        temp_v = np.divide(close_price,prev_close)
        temp_log = np.log(temp_v)
        temp_data['RETURNS'] = temp_log
        avg = np.mean(temp_log)
        stand = np.std(temp_log)

        return avg, stand
        
    def suggestion_pain(self,pain_value,contract):
        avg_return, V = self.volatility(contract)
        #print(avg_return, V)
        #calculate the upper and lower price range of Nifty based on volatility and days to expiry
        #first we will get the expiry date, last available closing price and the data date
        diff = edate - udate
        days_left_to_expiry = diff.days
        avg_till_expiry = avg_return * days_left_to_expiry
        V_till_expiry = V * math.sqrt(days_left_to_expiry)

        #calculate the upper and lower band
        #this is 1SD aka 68% chance it will not go beyond this
        upper = round(avg_till_expiry+V_till_expiry,4)       
        lower = abs(round(avg_till_expiry-V_till_expiry,4))
        nifty_up = round(pain_value * (1 + upper))
        nifty_low = round(pain_value * (1 - lower))
        #this is 2SD aka 95% chance that it will not go beyond this
        upper_2SD = round(avg_till_expiry+ 2*V_till_expiry,4)       
        lower_2SD = abs(round(avg_till_expiry- 2*V_till_expiry,4))
        nifty_up_2SD = round(pain_value * (1 + upper_2SD))
        nifty_low_2SD = round(pain_value * (1 - lower_2SD))
        #current_nifty_up = round(st * (1 + upper))
        #current_nifty_low = round(st * (1 - lower))
        QMessageBox.information(self, 'Possible Positions', "-------------------------------------------------------------------------\nBelow suggested range has 68% probability i.e there is 32% probability that {} might go beyond the range.\n-------------------------------------------------------------------------\nShort Call option around strike price of {} \nShort Put option around strike price of {} \nUse this range when there is 15 or less days till expiry\n------------------------------------------------------------------------- \nBelow suggested range has a 95% probability i.e. there is a mere 5% probability that {} might cross this range.\n-------------------------------------------------------------------------\nShort Call option around strike price of {} \nShort Put option around strike price of {} \nUse this range if there is more than 15days till expiry. \n-------------------------------------------------------------------------\nFinal note: It is always safer to go short using Option Pain as a base when there is less than 15 days till expiry \nLastly I will suggest to always short call over put because fear spreads faster than greed ".format(contract,nifty_up,nifty_low,contract,nifty_up_2SD,nifty_low_2SD), QMessageBox.Ok, QMessageBox.Ok)

    def selection_change(self,**kwargs):
        self.exp_dates.clear()
        list_of_exp = []
        lim = []
        #second generate a dataframe based on the SYMBOL to get the expiry dates
        #fil_inst = debhav['INSTRUMENT'].isin(['OPTIDX'])
        temp_df = debhav#[fil_inst]
        select = self.instruments.currentText()
        fil_symb = temp_df['SYMBOL'].isin([select])
        temp2_df = temp_df[fil_symb]
        CE = temp2_df[temp2_df['OPTION_TYP']=='CE']
        
        for e in CE['EXPIRY_DT']:
            if not e in lim:
                list_of_exp.append(e)
                lim.append(e)
        
        self.exp_dates.addItems(list_of_exp)

    def exp_date_selection(self,**kwargs):
        
        var = self.exp_dates.currentText()
        sel = self.instruments.currentText()
        up = self.get_maxpain(debhav,sel,var)
        plot = self.plot_option_pain(up)   
    #-----------------------------------END OF OPTION PAIN SECTION-----------------------------------------------
    def Wincenter(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    
    @pyqtSlot()
    def check(self, *args):
        print(args)

        '''
        val = self.txt.toPlainText()
        try:
            vtxt = int(val)  #example value would be 10450
            x = self.bull(val)
        except Exception as e:
            self.lbl1.setText("The value you entered is invalid, Please try again")
        '''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()   
    sys.exit(app.exec_())
