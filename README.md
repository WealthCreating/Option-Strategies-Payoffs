Known Errors:
1. Giving a target value which is not a strike price will return error or might crash the program.
2. When calling some functions of nsepy via PyQt5, an extra parameter self is passed to nsepy which causes error, 
   I have worked around it by altering nsepy module and adding **kwargs to the functions which were returning the error
3. Option pain: when playing around with the various available symbols and expiry dates and then clicking suggested action button the program crashes with the error coming from nsepy module
   most likely a connection is aborted and AttributeError: 'ThreadReturns' object has no attribute 'result'.
   Temporary Solution for this problem is to reboot the script and select whichever symbol and expiry you wanted to check, plot it's chart and then click suggested action.

# Option-Strategies-Payoffs + Market's Sentiments
My Script will provide the user with possible option strategies and their payoffs, based on the user's view of the market aka bullish,bearish or neutral and I have also added TRIN indicator along with Options pain

<b><u>NIFTY OPTIONS ONLY FOR NOW</b></u>

List of strategies and their respective payoffs that I want to add:

Bullish Strategies 

1. Bull Call Spread 2. Bull Put Spread 3. Call Ratio Back Spread 4. Bear Call Ladder 5. Call Butterfly 6. Synthetic Call 7. Straps 
 
Bearish Spreads 

1. Bear Call Spread 2. Bear Put Spread 3. Bull Put Ladder 4. Put Ratio Back spread 5. Strip 6. Synthetic Put 
 
Neutral Strategies 

1. Long & Short Straddles 2. Long & Short Strangles 3. Long & Short Iron Condor 4. Long & Short Butterfly 5. Box 


<b>Status of the code:</b>
Edit: The code now works and has a lot of features added to it. Some of the features takes a while to load, I have not implemented multithreading on purpose because I do not want to user to spam other stuffs while asking the program to get an indicator.

Very early stages, I am still trying to figure out how to accept user input, check if the input is correct and if it is pass the input to another function where the calculations will happen.

20-02-2018:

Today I added a way to get user input Target and calculated a Bull Spread by going long in approximate ATM Call and going short in Target Call option. This Spread will give highest returns when the Spot Price of Nifty is equal to or higher than the user's target. Right now my code only returns a Dataframe, Later I will find a way to present the same to the user.

21-02-2018

Added a chart to show the Bull Call Spread. Next Target is to find ways to use the same chart to show multiple Dataframes.


19-03-2018

The program now works and is based on nsepy module, so all thanks goes to https://github.com/swapniljariwala
Features working:

1. TRIN Indicator - takes a while to load of course as I had to manually make the Advances to Decline Ratio.

2. Option Strategies - have only added 2, I still can not decide which all strategies I am going to add to the "Bullish Category" and "Bearish Category"

3. Option Pain along with Put Call Ratio is working completely.

Features that I have plan to add, Customized strike price selection for the various strategies that I will add eventually and also my own proprietory indicator to support the market trend indicators like TRIN, PCR and Option Pain.

21-03-2018

Bearish Option Strategies added - Now the code has 4 strategies and their customisation working.
Optimisation of Bull Call Spread based on your target and risk has been added. No optimisation when you customise a strategy.
