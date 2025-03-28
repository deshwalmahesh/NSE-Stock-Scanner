from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from agents.fundamental_agent import (ToFundamentalAnalysisAssistant, fundamental_analysis_runnable, 
fundamental_analysis_tools, route_fundamental_analysis)
from agents.news_agent import (ToNewsAnalysisAssistant, news_analysis_runnable, news_analysis_tools, 
route_news_analysis)
from agents.technical_agent import (ToTechnicalAnalysisAssistant, technical_analysis_runnable, technical_analysis_tools, 
route_technical_analysis)
from agents.primary_agent import primary_assistant_tools, primary_assistant_runnable, route_primary_assistant
from agents.utils import *

from dotenv import load_dotenv

load_dotenv()



builder = StateGraph(State)

builder.add_node(
    "enter_fundamental_analysis",
    create_entry_node("Fundamental Analysis Assistant", "fundamental_analysis"),
)
builder.add_node("fundamental_analysis", Assistant(fundamental_analysis_runnable))
builder.add_edge("enter_fundamental_analysis", "fundamental_analysis")

builder.add_node(
    "fundamental_analysis_tools",
    create_tool_node_with_fallback(fundamental_analysis_tools),
)


builder.add_edge("fundamental_analysis_tools", "fundamental_analysis")
builder.add_conditional_edges(
    "fundamental_analysis",
    route_fundamental_analysis,
    ["fundamental_analysis_tools", "leave_skill", END],
)


builder.add_node("leave_skill", pop_dialog_state)
builder.add_edge("leave_skill", "primary_assistant")


builder.add_node(
    "enter_news_analysis",
    create_entry_node("News Analysis Assistant", "news_analysis"),
)
builder.add_node("news_analysis", Assistant(news_analysis_runnable))
builder.add_edge("enter_news_analysis", "news_analysis")
builder.add_node(
    "news_analysis_tools",
    create_tool_node_with_fallback(news_analysis_tools),
)


builder.add_edge("news_analysis_tools", "news_analysis")
builder.add_conditional_edges(
    "news_analysis",
    route_news_analysis,
    [
        "news_analysis_tools",
        "leave_skill",
        END,
    ],
)


builder.add_node(
    "enter_technical_analysis", create_entry_node("Technical Analysis Assistant", "technical_analysis")
)
builder.add_node("technical_analysis", Assistant(technical_analysis_runnable))
builder.add_edge("enter_technical_analysis", "technical_analysis")
builder.add_node(
    "technical_analysis_tools",
    create_tool_node_with_fallback(technical_analysis_tools),
)



builder.add_edge("technical_analysis_tools", "technical_analysis")
builder.add_conditional_edges(
    "technical_analysis",
    route_technical_analysis,
    ["leave_skill", "technical_analysis_tools", END],
)

# Primary agent Flow
builder.add_node("primary_assistant", Assistant(primary_assistant_runnable))
builder.add_node(
    "primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools)
)


# The assistant can route to one of the delegated assistants,
# directly use a tool, or directly respond to the user
builder.add_conditional_edges(
    "primary_assistant",
    route_primary_assistant,
    [
        "enter_fundamental_analysis",
        "enter_news_analysis",
        "enter_technical_analysis",
        "primary_assistant_tools",
        END,
    ],
)
builder.add_edge("primary_assistant_tools", "primary_assistant")


builder.add_edge(START, "primary_assistant")

# Compile graph
memory = MemorySaver()
final_compiled_graph = builder.compile(
    checkpointer=memory,
)