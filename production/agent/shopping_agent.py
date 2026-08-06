from typing import Optional, Any
from langchain.agents import create_agent
from production.agent.llm_factory import get_primary_llm
from production.agent.prompts import AGENT_SYSTEM_PROMPT
from production.agent.tools import tools
from production.agent.guardrail import model_base_guardrail
from production.logger import logger


def build_shopping_agent(model: Optional[Any] = None) -> Any:
    """Builds and returns the shopping agent runnable."""
    llm = model or get_primary_llm()
    logger.info("Building AI Shopping Agent executor...")
    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
    )


# Agent instance for export
agent = build_shopping_agent()


if __name__ == "__main__":
    test_input = {
        "messages": [
            {
                "role": "user",
                "content": "I want to buy organic honey with 4.5+ rating and less than $20 price.",
            }
        ]
    }
    logger.info("Executing sample CLI agent invocation...")
    result = agent.invoke(test_input)
    print("\n--- Agent Response ---")
    print(result["messages"][-1].content)
