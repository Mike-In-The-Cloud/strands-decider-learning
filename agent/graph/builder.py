from langgraph.graph import END, START, StateGraph

from graph.edges import after_evaluate, after_route
from graph.nodes.ask import ask
from graph.nodes.classify import classify
from graph.nodes.clarify import clarify
from graph.nodes.create import create
from graph.nodes.evaluate import evaluate
from graph.nodes.explain import explain
from graph.nodes.extract import extract
from graph.nodes.finalize import finalize
from graph.nodes.route import route
from graph.nodes.summarize import summarize
from graph.state import AgentState
from graph.workflows import WORKFLOWS

_graph = None


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route", route)
    graph.add_node("clarify", clarify)
    graph.add_node("summarize", summarize)
    graph.add_node("classify", classify)
    graph.add_node("create", create)
    graph.add_node("extract", extract)
    graph.add_node("evaluate", evaluate)
    graph.add_node("explain", explain)
    graph.add_node("ask", ask)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "route")
    graph.add_conditional_edges("route", after_route, [*WORKFLOWS, "clarify"])
    for name in WORKFLOWS:
        graph.add_edge(name, "evaluate")
    graph.add_conditional_edges("evaluate", after_evaluate, [*WORKFLOWS, "explain", "ask"])
    graph.add_edge("explain", "finalize")
    graph.add_edge("clarify", END)
    graph.add_edge("ask", END)
    graph.add_edge("finalize", END)
    return graph.compile(name="decision_agent")


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
