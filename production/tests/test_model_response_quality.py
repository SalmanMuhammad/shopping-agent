import json
from langchain_core.messages import HumanMessage
from production.agent.shopping_agent import agent
from production.agent.llm_factory import get_guardrail_llm


TEST_CASES = [
    {"query": "organic honey under $20"},
    {"query": "show me snacks"},
    {"query": "I want grains"},
]

JUDGE_PROMPT = """
You are an evaluator for a shopping assistant agent. You will be given a user query and the agent's final response.

Evaluate the response on three criteria, each on a scale of 1 to 10:

1. **Relevance**: Does the response directly address the user's query? Is it on‑topic and helpful?
2. **Correctness**: Does the response list the correct products based on the query? Check if the products match the filters (price, organic, category, etc.). Also check that ratings are correctly shown.
3. **Format Compliance**: The agent must output a numbered list with each product in exactly this format:
   `#<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>`
   Lines should be separated by a blank line. There should be no extra formatting, markdown, or backticks.

Provide your scores as a JSON object with keys "relevance", "correctness", "format", and a brief "explanation" for each.

Query: {query}

Agent response:
{response}

Return ONLY the JSON object.
"""


def get_agent_response(query):
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


def judge_response(query, response):
    judge_llm = get_guardrail_llm()
    prompt = JUDGE_PROMPT.format(query=query, response=response)
    msg = HumanMessage(content=prompt)
    result = judge_llm.invoke([msg])
    try:
        scores = json.loads(result.content)
    except json.JSONDecodeError:
        scores = {
            "relevance": 0,
            "correctness": 0,
            "format": 0,
            "explanation": "Parsing failed",
        }
    return scores


def run_evaluation():
    all_scores = []
    for case in TEST_CASES:
        query = case["query"]
        response = get_agent_response(query)
        scores = judge_response(query, response)
        scores["query"] = query
        all_scores.append(scores)

    avg_relevance = sum(s["relevance"] for s in all_scores) / len(all_scores)
    avg_correctness = sum(s["correctness"] for s in all_scores) / len(all_scores)
    avg_format = sum(s["format"] for s in all_scores) / len(all_scores)

    print(f"Average Relevance: {avg_relevance:.1f}")
    print(f"Average Correctness: {avg_correctness:.1f}")
    print(f"Average Format Compliance: {avg_format:.1f}")
    print("\nDetailed scores:")
    for s in all_scores:
        print(f"- Query: {s['query']}")
        print(
            f"  Relevance: {s['relevance']}, Correctness: {s['correctness']}, Format: {s['format']}"
        )
        print(f"  Explanation: {s.get('explanation', '')}")

    failed = [
        s
        for s in all_scores
        if any(s[k] < 7 for k in ["relevance", "correctness", "format"])
    ]
    if failed:
        print("\n⚠️ Some responses failed the evaluation:")
        for f in failed:
            print(
                f"  Query: {f['query']} - Scores: R={f['relevance']}, C={f['correctness']}, F={f['format']}"
            )
        return False
    else:
        print("\n✅ All quality tests passed.")
        return True


if __name__ == "__main__":
    run_evaluation()
