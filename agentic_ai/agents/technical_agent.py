# Technical Analysis Agent
from agents.utils import *
from datetime import datetime
import ta
import yfinance as yf
from langchain_core.tools import tool

@tool
def get_technical_analysis(stock_symbol: str) -> dict:
    """
    Provides technical analysis of the stock symbol provided for Daily, Monthly and Weekly data signals
    """
    stock_symbol = stock_symbol.upper().strip()
    if not stock_symbol.endswith(".NS"):
        stock_symbol = f"{stock_symbol}.NS"

    ticker = yf.Ticker(stock_symbol)
    df = ticker.history(period="max")
    if df.shape[0] < 600:
        raise ValueError(f"Insufficient data for {stock_symbol} to be used for Monthly. Use another stock")

    df.rename(columns={"Volume": "Volume_BTC"}, inplace=True)
    df.drop(["Dividends", "Stock Splits"], axis=1, inplace=True)

    daily_df = ta.utils.dropna(df)

    weekly_df = daily_df.resample('W-FRI').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min',
        'Close': 'last', 'Volume_BTC': 'sum'
    })
    
    monthly_df = daily_df.resample('ME').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min',
        'Close': 'last', 'Volume_BTC': 'sum'
    })

    daily_results = ta.add_all_ta_features(
        daily_df.copy(deep=True), 
        "Open", "High", "Low", "Close", "Volume_BTC", fillna=True).to_dict(orient="records")[0]

    weekly_results = ta.add_all_ta_features(
        weekly_df.copy(deep=True), 
        "Open", "High", "Low", "Close", "Volume_BTC", fillna=True).to_dict(orient="records")[0]

    monthly_results = ta.add_all_ta_features(
        monthly_df.copy(deep=True), 
        "Open", "High", "Low", "Close", "Volume_BTC", fillna=True).to_dict(orient="records")[0]
    
    return {"daily": daily_results, "weekly": weekly_results, "monthly": monthly_results}


technical_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling technical analysis of a stock. "
            "The primary assistant delegates work to you whenever the user needs help with technical stock analysis. "
            "Provide detailed technical analysis based on the data received from the get_technical_analysis tool. "
            "If you need more information or clarification, escalate the task back to the main assistant. "
            "Remember that an analysis isn't completed until after the relevant tool has successfully been used. "
            "\nCurrent time: {time}."
            '\n\nIf the user needs help, and none of your tools are appropriate for it, then "CompleteOrEscalate" the dialog to the host assistant. '
            "Do not waste the user's time. Do not make up invalid tools or functions."
            "\n\nSome examples for which you should CompleteOrEscalate:\n"
            " - 'What's the company's recent news?'\n"
            " - 'I think I'll analyze fundamentals instead'\n"
            " - 'I need to check the overall market conditions'\n"
            " - 'Oh wait, I haven't decided on a stock yet'\n"
            " - 'Technical analysis completed'",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

technical_analysis_tools = [get_technical_analysis]
technical_analysis_runnable = technical_analysis_prompt | llm.bind_tools(
    technical_analysis_tools + [CompleteOrEscalate]
)

class ToTechnicalAnalysisAssistant(BaseModel):
    """Transfer work to a specialized assistant to handle technical stock analysis."""

    stock_symbol: str = Field(
        description="Symbol of the Stock that is needed for the analysis"
    )
    request: str = Field(
        description="Any necessary followup questions the technical analysis assistant should clarify before proceeding."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "stock_symbol": "SBIN.NS",
            }
        }

def route_technical_analysis(
    state: State,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    return "technical_analysis_tools"