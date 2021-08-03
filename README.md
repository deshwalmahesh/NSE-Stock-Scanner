# **STOCK-SCANNING-TOOL**
National Stock Exchange (NSE), India based Stock suggestion program for Swing / Momentum based Trading. 
Supports:
1. Auto risk management Entry(above High), Stop-loss (Below the lower of current close or prev close), Target (based on 2:1), Expoected Change
2. Risk Control and Management. (Whether you should buy the stocks or not based on your risk apetite and budget, it suggests you stocks)
3. Ichimoku Suggestion (Count out of 3 conditions: Lines Crossing or not, Chikou Lagging inside Prices or Not, Cloud Below the Price or Not)
4. Moving Average Support (Whether Price is on the Above Side of Moving Average or not)
5. Bollinger Bands (2 STD Positive and Negative Bollinger Band Support)
6. RSI Value ( Relative Strength Index)
7. ATR Value (Average True Range)
8. Stock Movement: Rising or Falling
9. Journal Analysis: Fetches the Spreadsheet where you have provided the data for buy and sell for future analysis (Refer to this](https://drive.google.com/file/d/1JipUU6Im1YVKSdufw4VHitwS010nFigL/view)
10. Automatic New Stock data Change and Download

# Usage: 
**Download and Install** `Python 3.7 and above`
```
git clone https://github.com/deshwalmahesh/NSE-Stock-Scanner.git
cd ./NSE-Stock-Scanner
pip install -r requirements.txt
jupyter lab
```
Enjoy ;)

For usage, see the docstring of code or the example ipython Notebook `Test.ipynb`

# Motivation?
[Financial Literacy in India](https://www.financialexpress.com/market/only-27-indians-are-financially-literate-sebis-garg/2134842/)


**Note**: I started out as an enthusiast for this concept of `44 SMA` style but backtested it using my own written code and found out that it gives you around `40-45%` Hit-Lose %. So? Learn More.

[See this video to know what is mimicks](https://youtu.be/dFibByGQWak?t=3747). All it does is to save your time rather when you have to go through 1800 stocks to pick. You can click and scan the stocks of your moving average. It does not support `Short Selling` but can be implementd by changing the code easily.


**This is not a trading Bot or software** but a mere tool to see the live charts, candlesticks for the stocks of your choice. **All it does is tell you all the available stocks** which are closest to and are on the upper side of 44 Moving Average. 

For more info on [44 Moving Average and Swing Trading, see this Most Popular videos of this channel](https://www.youtube.com/c/SIDDHARTHBHANUSHALI/videos?view=0&sort=p&shelf_id=0)

It supports:
1. Download of more than 1800 NSE stocks for 1 days
2. Plot Candle Sticks of stocks
3. Pick and Scan all the stocks based on your budget, loss threshold, profit apetite, `K` Moving Average etc


