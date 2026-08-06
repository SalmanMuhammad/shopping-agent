import base64
import os
from typing import Optional, Any
from langchain_core.messages import HumanMessage

from logger import logger


class VisionService:
    def __init__(self, vision_llm: Optional[Any] = None):
        self.vision_llm = vision_llm

    def describe_product_image(self, image_path: str) -> str:
        """
        Analyzes a product image and returns key attributes as a text/JSON string.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return f"Error: Image file '{image_path}' does not exist."

        logger.info(f"Analyzing product image: {image_path}")
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        ext = os.path.splitext(image_path)[1].lower().lstrip(".")
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{image_data}"},
                },
                {
                    "type": "text",
                    "text": (
                        "Look at this product image and extract its key attributes. "
                        "Return ONLY a JSON object with these fields:\n"
                        "- product_type: what kind of product it is (e.g. honey, olive oil, almonds)\n"
                        "- search_query: a short keyword to search for it (e.g. 'honey', 'olive oil')\n"
                        "- is_organic: true if the label says organic, false if not, null if unclear\n"
                        "- description: one sentence describing the product"
                    ),
                },
            ]
        )

        if not self.vision_llm:
            from agent.llm_factory import get_vision_llm
            self.vision_llm = get_vision_llm()

        response = self.vision_llm.invoke([message])
        content = response.content

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    return item.get("text", "")
                elif isinstance(item, str):
                    return item
            return str(content)
        return str(content)
