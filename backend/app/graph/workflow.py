from langgraph.graph import StateGraph, START, END
from backend.app.graph.state import VaultAIState
from backend.app.graph.router import router_node, route_decision
from backend.app.graph.nodes.document_agent import document_agent_node
from backend.app.graph.nodes.coding_agent import coding_agent_node
from backend.app.graph.nodes.vision_agent import vision_agent_node


def create_vaultai_graph():
    """Build and compile VaultAI controlled routing StateGraph."""
    workflow = StateGraph(VaultAIState)

    # Add Nodes
    workflow.add_node("router", router_node)
    workflow.add_node("document_agent", document_agent_node)
    workflow.add_node("coding_agent", coding_agent_node)
    workflow.add_node("vision_agent", vision_agent_node)

    # Set Entry Point
    workflow.add_edge(START, "router")

    # Add Conditional Edges from Router to Agents
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "document": "document_agent",
            "coding": "coding_agent",
            "vision": "vision_agent"
        }
    )

    # Connect Agent Nodes to END
    workflow.add_edge("document_agent", END)
    workflow.add_edge("coding_agent", END)
    workflow.add_edge("vision_agent", END)

    return workflow.compile()


vaultai_graph_app = create_vaultai_graph()
