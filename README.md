# 🔥 🔥  Now Supports `[2,3,4,5,10,15,30,60]` minutes Historical as well as Live data🔥 🔥

# Disclaimer:
STOCK MARKET IS VERY RISKY UNTIL YOU DO IT PROPERLY. PLEASE DO NOT TAKE TRADES JUST BECAUSE THIS TOOL GIVES YOU THE NAME. APPLY YOUR OWN LEARNINGS, CREATE YOUR OWN STRATEGY, ASSESS RISK & TRADE THE PLAN.

```diff
-Trade at you own risk as No one will be held responsible for the losses incurred exept the trader.
```

I personally have lost some money in intraday without plan and own judgement. This tool can help you with manual effort of selecting stocks from listed 1600 stocks but you have to use your knowledge after that.

## Currently Working On (Long term project): 
```diff
+ Live News based AI model to predict the sentiment of news related to stock. Predict probability whether a stock will go up or down based on the sentiment of the news.
+ RL (Reinforcement Learning) for trades suggestion given different conditions.
```
_______________________________________________________________
## STOCK-SCANNING-TOOL:

**India's first and only free open source tool to have it all such as: Live data, Scan stocks based on Swing / momentum strategies, intraday strategies, candlestick patterns, Indicator values, Charts, Backtesting, Online Broker Platform connection, ebooks, Risk management and one of the few to add concept of Live Market Mood. 
Ebooks will be added as I read them and find useful**

_______________________________________________________________
## Usage Steps: 

1. **Download and Install** [Python 3.7 and above](https://www.python.org/downloads/)
2. `Fork` or `Clone` the project. For Non- tech, Windows users, find `Fork` button on upper right hand corner, fork it. Look for the **Green** `Code` button and download the zip file, extract it.
3. Find and open the directory by the name **NSE-Stock-Scanner** inside above zip file. Open Terminal ( For Linux) or Command Prompt or Git Shell in Windows inside the directory.
4. Run the following Commands:
```
cd ./NSE-Stock-Scanner
pip install -r requirements.txt
jupyter lab
```
4. Open `Tutorial.ipynb` in your browser for Documentation and usage
5. Go to first cell (just below *Imports, Defaults and Initializations* where some code is written) and press `Shit + Enter`.
6. To run any cell, just do the same. [Read the commands here if you need help in running it](https://www.tutorialspoint.com/jupyter/jupyter_notebook_editing.htm)

7. I am updating this code on a regular basis so if you want to keep updated, just run `git pull` inside the same folder

For usage, see the docstring of code or the example ipython Notebook `Test.ipynb`

```diff
- NOTE: There is some bug in fetching live data and data refresh so if you are not ubale to get some data, or get an error; restart kernal and run cells again
```


**Please share your ideas, views, requirements, knowledge, bug reports, fixes and most importantly; reviews.**

Enjoy the power of computing and trade safely ;)

_______________________________________________________________________________
## Supports (still in development phase. Growing as learning):
**[Candlesticks patterns](https://www.google.com/search?q=candlestick+patterns&tbm=isch&source=iu&ictx=1&fir=9Lm-Dk5oFkUTmM%252C6hxFMBJvKNiUmM%252C%252Fm%252F0cmdn32&vet=1&usg=AI4_-kSzAUZ8FhvyUPSuBBIE3AeEuZXkiQ&sa=X&ved=2ahUKEwjSwYDFmJXzAhWYXSsKHSGMBKgQ_B16BAhDEAE#imgrc=9Lm-Dk5oFkUTmM)**

1. Marubozu
2. Harami
3. Doji ( Couple of versions)
4. Hammer / Shooting Star
5. V Pattern
6. Reverse Pattern
7. 3 White Soldiers
8. Bullish and Bearish Engulfing

________________________________________________________________________________
**[Swing Trading](https://www.businessinsider.in/finance/news/what-to-know-about-swing-trading-and-how-to-minimize-risks-of-this-speculative-trading-strategy/articleshow/84778123.cms#:~:text=Swing%20trading%20is%20a%20speculative,while%20the%20market%20is%20closed.):** National Stock Exchange (NSE), India based Stock suggestion/ scanning program for Swing / Momentum based Trading. 

Supports:
1. Auto risk management: Entry ( Default is buy above above High and Stop-loss Below the lower of current close or prev close; can also be overridden), Target (default is based on 1:2), Expected Change (how much change you are expecting from it to give you a realistic measure)
2. Risk Control and Management: (Whether you should buy the stocks or not based on your risk apetite and budget, it suggests you stocks)
3. Daily Pivot Points with CPR
4. Breakout Support: Stocks which are in tight consolidation for the past `n` days within `x%` range of recent candle. Might breakout
5. CCI
6. MACD
7. Stochastic
8. Ichimoku Suggestion (Count out of 3 conditions: Lines Crossing or not, Chikou Lagging inside Prices or Not, Cloud Below the Price or Not)
9. Moving Average Support (Whether Price is on the Above Side of Moving Average or not)
10. Bollinger Bands (2 STD Positive and Negative Bollinger Band Support)
11. RSI Value ( Relative Strength Index)
12. ATR Value (Average True Range)
13. ADX (Directional Index to give you idea about momentum)
14. Stock Movement: Rising or Falling ( `x%` (Default is 5%) near 52 Week high or Low. 
15. Journal Analysis: Fetches the Spreadsheet where you have provided the data for buy and sell for future analysis [Refer to this](https://drive.google.com/file/d/1JipUU6Im1YVKSdufw4VHitwS010nFigL/view)
16. Automatic New Stock data Change and Download
17. Moving Average Crossover strategy: Gives you stocks if Moving Average 1 (Fast, say 50) crosses above Moving Average 2 (slow, say 200) within `N` days.

_______________________________________________________________________________________________________________________________
**[Intra-Day Trading](https://groww.in/p/intraday-trading/#:~:text=Intraday%20trading%20is%20the%20process,earn%20profits%20from%20stock%20trading.)**:
1. Live Market Mood such as TICK, TRIN, No of stocks trading currently at 52 Week High or Low
2. Stock Selection for `Open == Low / High` at whole number (`x.00`) strategy.
3. Probability based stock: Sorted Top`K` stocks based on probability which can give you atleast `x%` return either on Long or Short side. Based on `N` days data of your choice.
4. Narrow Range Strategy where the most recent day candle has the lowest range from the previous `N` ( default 7) days days candle, so the next day is most likely to breakout in either side.
5. Marlet Mood and Sentiment analysis: % change of every Sector / Indices in Live Market. Gives you a mood of overall market right now based on which sector is performing with which mood live. Opens the top performing stocks from each sector 

_____________________________________________________________________________
**Backtesting**: Backtesting support and results.
Class to implement just the Buy and sell conditions. Some strategies already implemented:
1. CCI
2. MACD
3. RSI
4. Stochastic
5. Moving Average
_____________________________________________________________________________
**[Futures and Deratives](https://www.investopedia.com/terms/f/futures.asp)**: F&O basi support.
1. List of available F&O
2. [Option Chain Analysis](https://www.quora.com/How-do-I-read-analyse-the-option-chain-of-a-stock-to-intraday-trade-with-clarity-NSE). Useful for Swing as well as Intra Day Trading

_________________________________________________________________________
**Ebooks**: Annotations added as I've read the books
1. [Trading in the zone](https://g.co/kgs/BSuHyC). Best book on psychology I could find till now. 
2. [High Probability Trading](https://www.amazon.in/High-Probability-Trading-Marcel-Link/dp/0071381562) Good book on strategies

_________________________________________________________________________
**Coming Next**:
1. Optimization: Find optimal values for each individual stocks because give good results for 35 MA, some give for Stochastic strategy, some for breakout.. etc etc.
2. Algo Trading
3. New Strategies and backtesting support

______________________________________________________________________________
## Starting Motivation?
[Financial Literacy in India](https://www.financialexpress.com/market/only-27-indians-are-financially-literate-sebis-garg/2134842/)


## Initial Work:
**Basic Usage**: 
1. Download of more than 1800 NSE stocks for 1 days. Run it after 11:30 PM IST to get day's stocks results as the market is closed at that time.
2. Plot Candle Sticks of stocks with moving average support.
3. Pick and Scan all the stocks based on your budget, loss threshold, profit apetite, `K` Moving Average etc


**Note**: I started out as an enthusiast for this concept of `44 SMA` style but backtested it using my own written code and found out that it gives you around `40-45%` Hit-Loss %. So? Learn More.

[See this video to know what is mimicks](https://youtu.be/dFibByGQWak?t=3747). All it does is to save your time rather when you have to go through 1800 stocks to pick. You can click and scan the stocks of your moving average. It does not support `Short Selling` but can be implementd by changing the code easily.


**This is not a trading Bot or software** but a mere tool to see the live charts, candlesticks for the stocks of your choice. **All it does is tell you all the available stocks** which are closest to and are on the upper side of 44 Moving Average. 

For more info on [44 Moving Average and Swing Trading, see this Most Popular videos of this channel](https://www.youtube.com/c/SIDDHARTHBHANUSHALI/videos?view=0&sort=p&shelf_id=0)
