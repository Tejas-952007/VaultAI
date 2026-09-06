from backend.app.graph.router import classify_route, router_node


def test_classify_route_document():
    assert classify_route("According to the document, what is the specification?") == "document"
    assert classify_route("What does the report say?") == "document"
    assert classify_route("Check the uploaded PDF file") == "document"


def test_classify_route_coding():
    assert classify_route("Write a python function to compute factorial") == "coding"
    assert classify_route("Debug this javascript script") == "coding"
    assert classify_route("How to write a class in programming?") == "coding"


def test_classify_route_vision():
    assert classify_route("Inspect image of the equipment") == "vision"
    assert classify_route("What is in this diagram photo?") == "vision"
    assert classify_route("Check this visual figure") == "vision"


def test_classify_route_override_by_document_ids():
    # If explicit document_ids are provided, route must be document
    assert classify_route("Write a python script", document_ids=["doc123"]) == "document"


def test_router_node_execution():
    state = {"request_id": "req1", "message": "Write a python function"}
    res_state = router_node(state)
    assert res_state["route"] == "coding"
