from agent.shopping_agent import agent


def normalise_value(val):
    """Convert string representations to actual types."""
    if isinstance(val, str):
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return val
    return val


TEST_CASES = [
    {
        "query": "organic honey under $20",
        "expected": [
            {"tool": "search_products", "args": {"query": "honey", "is_organic": True, "max_price": 20.0}}
        ]
    },
    {
        "query": "show me snacks",
        "expected": [
            {"tool": "search_products", "args": {"query": "snacks"}}
        ]
    },
    {
        "query": "I always want organic",
        "expected": [
            {"tool": "set_preferences", "args": {"prefer_organic": True}}
        ]
    },
    {
        "query": "what are my preferences?",
        "expected": [
            {"tool": "get_preferences", "args": {}}
        ]
    }
]


def extract_tool_calls_from_messages(messages):
    tool_calls = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "tool": tc["name"],
                    "args": tc["args"]
                })
    return tool_calls


def test_agent_tool_calling_accuracy():
    for case in TEST_CASES:
        result = agent.invoke({"messages": [{"role": "user", "content": case["query"]}]})
        messages = result["messages"]
        actual_calls = extract_tool_calls_from_messages(messages)
        expected = case["expected"]

        for i, exp in enumerate(expected):
            if i >= len(actual_calls):
                raise AssertionError(f"Test failed for '{case['query']}': missing tool call {exp}")
            act = actual_calls[i]
            assert act["tool"] == exp["tool"], f"Expected {exp['tool']}, got {act['tool']}"

            for k, v in exp["args"].items():
                actual_val = act["args"].get(k)
                normalised_actual = normalise_value(actual_val)
                normalised_expected = normalise_value(v)
                assert normalised_actual == normalised_expected, \
                    f"Expected {k}={v} (type {type(v)}), got {actual_val} (type {type(actual_val)})"

        print(f"✅ Passed tool accuracy check: {case['query']}")


if __name__ == "__main__":
    test_agent_tool_calling_accuracy()
