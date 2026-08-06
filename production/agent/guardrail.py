from typing import List, Dict, Any, Union
from production.agent.llm_factory import get_guardrail_llm
from production.agent.prompts import GUARDRAIL_SYSTEM_PROMPT
from production.logger import logger


def model_base_guardrail(messages: List[Union[Dict[str, Any], Any]]) -> str:
    """
    Classifies whether the latest user query is shopping-related.
    Returns 'proceed' or 'abort'.
    """
    if not messages:
        return "proceed"

    last_msg = messages[-1]
    if isinstance(last_msg, dict):
        user_text = last_msg.get("content", "")
    elif hasattr(last_msg, "content"):
        user_text = last_msg.content
    else:
        user_text = str(last_msg)

    # Image upload query is automatically shopping-related
    if "I uploaded a product image" in user_text:
        return "proceed"

    try:
        guardrail_llm = get_guardrail_llm()
        formatted_messages = [
            ("system", GUARDRAIL_SYSTEM_PROMPT),
            ("human", user_text),
        ]
        res = guardrail_llm.invoke(formatted_messages)
        result = res.content.strip().lower()
        logger.info(f"Guardrail classification for '{user_text[:30]}...': {result}")
        if "proceed" in result:
            return "proceed"
        return "abort"
    except Exception as e:
        logger.error(f"Guardrail execution exception: {e}. Defaulting to 'proceed'")
        return "proceed"
