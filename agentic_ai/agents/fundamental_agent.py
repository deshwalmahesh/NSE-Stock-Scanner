"""
Fundamental Analysis Agent

This module implements a fundamental analysis agent that examines financial
statements, company fundamentals, and valuation metrics to provide investment
recommendations.
"""
from langgraph.graph import END
import yfinance as yf
from agents.utils import *
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

def clean_info(info):
    fundamental_analysis_keys = [
    # Company profile
    'sector', 'industry', 'fullTimeEmployees',
    
    # Financial metrics
    'marketCap', 'enterpriseValue', 'trailingPE', 'forwardPE', 'priceToBook', 'priceToSalesTrailing12Months',
    'profitMargins', 'operatingMargins', 'grossMargins', 'returnOnEquity',
    
    # Growth metrics
    'revenueGrowth', 'earningsGrowth', 'revenuePerShare', 'trailingEps', 'forwardEps',
    
    # Debt and cash
    'totalCash', 'totalCashPerShare', 'totalDebt', 'debtToEquity',
    
    # Dividends
    'dividendRate', 'dividendYield', 'payoutRatio', 'fiveYearAvgDividendYield',
    
    # Analyst opinions
    'targetMeanPrice', 'recommendationMean', 'recommendationKey', 'numberOfAnalystOpinions',
    
    # Institutional ownership
    'heldPercentInsiders', 'heldPercentInstitutions',
    
    # Revenue and profit
    'totalRevenue', 'grossProfits', 'netIncomeToCommon',
    
    # Dates for financial reporting
    'lastFiscalYearEnd', 'nextFiscalYearEnd', 'mostRecentQuarter'
    ]
    res = {}
    for key in fundamental_analysis_keys:
        val = str(info.get(key, "")).strip()
        if val: res[key] = val
    return res


@tool
def get_fundamental_analysis(stock_symbol: str):
    """
    Retrieve fundamental analysis information for a given stock symbol.
    """
    stock_symbol = stock_symbol.upper().strip()
    if not stock_symbol.endswith(".NS"):
        stock_symbol = f"{stock_symbol}.NS"

    ticker = yf.Ticker(stock_symbol)
    
    
    # Helper function to safely convert dataframe to dict if it exists and has data
    def safe_to_dict(df):
        if df is not None and hasattr(df, 'shape') and df.shape[0] > 0:
            return df.to_dict()
        return None
    
    result = {
        "info": clean_info(ticker.info),
        }

    # Add dataframes that need conversion to dict
    major_holders_dict = safe_to_dict(ticker.major_holders)
    if major_holders_dict:
        result["major_holders"] = major_holders_dict
    
    recommendations_dict = safe_to_dict(ticker.recommendations)
    if recommendations_dict:
        result["recommendations"] = recommendations_dict
    
    revenue_estimate_dict = safe_to_dict(ticker.revenue_estimate)
    if revenue_estimate_dict:
        result["revenue_estimate"] = revenue_estimate_dict

    balance_sheet_dict = safe_to_dict(ticker.balance_sheet)
    if balance_sheet_dict:
        result["balance_sheet"] = balance_sheet_dict
    
    cash_flow_dict = safe_to_dict(ticker.cash_flow)
    if cash_flow_dict:
        result["cash_flow"] = cash_flow_dict
    
    earnings_history_dict = safe_to_dict(ticker.earnings_history)
    if earnings_history_dict:
        result["earnings_history"] = earnings_history_dict

    eps_trend_dict = safe_to_dict(ticker.eps_trend)
    if eps_trend_dict:
        result["eps_trend"] = eps_trend_dict
    
    financials_dict = safe_to_dict(ticker.financials)
    if financials_dict:
        result["financials"] = financials_dict
    
    income_stmt_dict = safe_to_dict(ticker.income_stmt)
    if income_stmt_dict:
        result["income_stmt"] = income_stmt_dict
    
    return result

fundamental_analysis_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a specialized assistant for handling fundamental analysis of a stock. "
            "The primary assistant delegates work to you whenever the user needs help with fundamental analysis. "
            "Provide detailed insights based on the financial data and metrics. "
            "When analyzing, be thorough and consider multiple factors. "
            "If you need more information or the analysis is inconclusive, escalate the task back to the main assistant. "
            "Remember that an analysis isn't completed until after you've provided a clear recommendation. "
            "\n\nCurrent stock symbol:\n<Stock>\n{stock_symbol}\n</Stock>"
            "\nCurrent time: {time}."
            "\n\nIf the user needs help, and none of your tools are appropriate for it, then"
            ' "CompleteOrEscalate" the dialog to the host assistant. Do not waste the user\'s time. Do not make up invalid tools or functions.',
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

fundamental_analysis_tools = [get_fundamental_analysis]
fundamental_analysis_runnable = fundamental_analysis_prompt | llm.bind_tools(
    fundamental_analysis_tools + [CompleteOrEscalate]
)

class ToFundamentalAnalysisAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle fundamental analysis of a stock to suggest Buy, Sell or Hold"""

    stock_symbol: str = Field(
        description="Symbol of the Stock that is needed for the analysis"
    )
    request: str = Field(
        description="Any necessary followup questions the fundamental analysis assistant should clarify before proceeding."
    )

def route_fundamental_analysis(
    state: State,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    return "fundamental_analysis_tools"
