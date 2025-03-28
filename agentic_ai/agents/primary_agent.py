from typing import Annotated, Literal, Optional
from langgraph.graph.message import AnyMessage, add_messages
from agents.fundamental_agent import ToFundamentalAnalysisAssistant
from agents.technical_agent import ToTechnicalAnalysisAssistant
from agents.news_agent import ToNewsAnalysisAssistant
from datetime import datetime
from agents.utils import *


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
def get_online_info(query: str):
    """
    Retrieve information related to the query and return an answer if available. Query needs to be properly formed in order to be searched
    Can be used for getting any crucial info required for the other agents. For example stock symbol info from company name, symbol to company name etc etc
    args:
        query: str - Query to retrieve information for.
    """
    web_search_results = web_search.invoke({"query": query})

    ans = ""
    if web_search_results: ans = web_search_results[0]["content"]

    return ans


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an advanced stock analysis assistant. Your role is to get recommendations from EACH and EVERY one of News, Technical, and fundamental analysis agents to provide a comprehensive investment recommendation. "
            "By default, the market is National Stock Exchange (NSE) India. You must collect info from ALL the specialized assistants until unless any one is explicitly mentioned."
            "When given inputs from specialized assistants, analyze and combine their insights to form a coherent recommendation on whether to buy, sell, or hold a stock. "
            "Always provide a detailed explanation for your recommendation, citing specific data points from each analysis type. "
            "If you need more information, request it from the appropriate specialized assistant using the provided tools. "
            "Be thorough in your analysis and consider potential risks and opportunities from all angles. "
            "If info on Symbol or stock  is not clear, then form a proper query and use tool to search online properly to get info "
            "Current time: {time}\n"
            "Remember, in the End, yu have to provide a clear buy, sell, or hold recommendation along with a comprehensive explanation ONLY and ONLY when there are analysis present from ALL the specialized assistants (News, Technical and Fundamental). Make sure ALL of the agents have given their insights with reasoning before you show it to user"
            "If any of them are missing, then get the results from missing agents and then aggregate",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now)

primary_assistant_tools = [get_online_info]
primary_assistant_runnable = primary_assistant_prompt | llm.bind_tools(
    primary_assistant_tools
    + [
        ToFundamentalAnalysisAssistant,
        ToNewsAnalysisAssistant,
        ToTechnicalAnalysisAssistant,
    ]
)

def route_primary_assistant(
    state: State,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToFundamentalAnalysisAssistant.__name__:
            return "enter_fundamental_analysis"
        elif tool_calls[0]["name"] == ToNewsAnalysisAssistant.__name__:
            return "enter_news_analysis"
        elif tool_calls[0]["name"] == ToTechnicalAnalysisAssistant.__name__:
            return "enter_technical_analysis"
        return "primary_assistant_tools"
    raise ValueError("Invalid route")