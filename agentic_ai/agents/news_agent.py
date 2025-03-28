from agents.utils import *
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults
import yfinance as yf
import json
from datetime import datetime

web_search = TavilySearchResults(
    max_results=3,
    include_answer=True,
    include_raw_content=True,
    include_images=True)

@tool  
def get_news(stock_symbol: str):
    """
    Retrieve news related information for a given stock symbol and return in a structured JSON format.
    args:
        stock_symbol: str - Valid NSE stock symbol to retrieve news for. For Example SBI, TCS, etc.
    """
    stock_symbol = stock_symbol.upper().strip()
    if not stock_symbol.endswith(".NS"):
        stock_symbol = f"{stock_symbol}.NS"

    ticker = yf.Ticker(stock_symbol)
    ticker_news = ticker.news

    web_search_results = web_search.invoke({"query": f"{stock_symbol.replace('.NS', '')} Stock News"})

    news_data = []
    for news_item in ticker_news[:3]:  # Limit to 3 news items
        item = news_item["content"]
        news_data.append({
            "summary": item.get("summary", ""),
            "published_date": item.get("pubDate", "")
        })

    for result in web_search_results[:3]:
        if result["score"] <= 0.8: continue # Search score less than this is discarded

        news_data.append({
            "summary": result.get("content", ""),
            "published_date": "",
        })

    return json.dumps({"stock_symbol": stock_symbol.rstrip(".NS"), "news": news_data})


news_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling news-based stock recommendations. "
            "The primary assistant delegates work to you whenever the user needs help analyzing stock news. "
            "Analyze the news data for the given stock and provide insights on its potential impact on the stock price. "
            "When analyzing, be thorough and consider both positive and negative news. "
            "If you need more information or the news is insufficient, escalate the task back to the main assistant. "
            "For any news, pay close attention to the time. If it's very old news, you have to decide if it is really important?"
            "Remember that an analysis isn't complete until after the relevant tool has successfully been used. "
            "\nCurrent time: {time}."
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then "
            '"CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.'
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'What's the current stock price?'\n"
            " - 'Can you predict future stock prices?'\n"
            " - 'I want to buy this stock now'\n"
            " - 'What are the company's financials?'\n"
            " - 'News analysis completed'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

news_analysis_tools = [get_news]
news_analysis_runnable = news_analysis_prompt | llm.bind_tools(
    news_analysis_tools + [CompleteOrEscalate]
)

class ToNewsAnalysisAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle news-based stock recommendations"""

    stock_symbol: str = Field(
        description="Valid NSE stock symbol of the stock that is needed for the analysis"
    )
    request: str = Field(
        description="Any additional information or requests from the user regarding the news analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stock_symbol": "SBIN.NS"
            }
        }

def route_news_analysis(
    state: State,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    return "news_analysis_tools"