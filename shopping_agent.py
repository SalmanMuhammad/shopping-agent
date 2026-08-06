import base64
import json
import os
import re
import sqlite3
from typing import Optional, Union

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from reviews_api import get_product_rating
from user_preferences import (
    get_user_preferences,
    set_user_preference,
    get_all_category_preferences,
)

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "store.db")
llm_groq = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

# llm_groq = ChatGroq(model="qwen/qwen3.6-27b", temperature=0)

llm = ChatOllama(model="llama3.2", temperature=0)
vision_llm = ChatOllama(model="llava", temperature=0)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool
def get_order_history(
    limit: Optional[int] = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """
    Get a summary of the user's order history.
    Returns a JSON array of orders with: order_id, product_name, price, ordered_at.
    Can filter by date range and limit the number of results.

    Args:
        limit: Maximum number of orders to return (default: 10)
        start_date: Filter orders after this date (format: YYYY-MM-DD)
        end_date: Filter orders before this date (format: YYYY-MM-DD)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    sql = "SELECT id, product_name, price, ordered_at FROM orders WHERE 1=1"
    params: list = []

    if start_date:
        sql += " AND ordered_at >= ?"
        params.append(start_date)

    if end_date:
        sql += " AND ordered_at <= ?"
        params.append(end_date)

    sql += " ORDER BY ordered_at DESC"

    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    orders = [
        {
            "order_id": row[0],
            "product_name": row[1],
            "price": row[2],
            "ordered_at": row[3],
        }
        for row in rows
    ]

    return json.dumps(orders)


@tool
def search_products(
    query: str,
    min_price: Optional[float] = None,  # NEW
    max_price: Optional[float] = None,
    is_organic: Optional[Union[bool, str]] = None,
    category: Optional[str] = None,
) -> str:
    """
    Search the product database by keyword (matched against name, description, and category).
    If max_price, min_price or is_organic are not provided,
    If category is provided, load category-specific preference
    the user's stored preferences are applied.
    Optionally filter by maximum price and/or organic status.
    Returns a JSON array of matching products, each with: id, name, category, price,
    description, is_organic.
    """

    prefs = get_user_preferences(category)

    # Apply stored preferences only if parameter is None
    if min_price is None and prefs["min_price"] is not None:
        min_price = prefs["min_price"]
    if max_price is None and prefs["max_price"] is not None:
        max_price = prefs["max_price"]
    if is_organic is None and prefs["prefer_organic"] is not None:
        is_organic = prefs["prefer_organic"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sql = "SELECT id, name, category, price, description, is_organic FROM products WHERE 1=1"
    params = []
    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like, like])
    if min_price is not None:
        sql += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        sql += " AND price <= ?"
        params.append(max_price)
    if is_organic is not None:
        sql += " AND is_organic = ?"
        params.append(1 if is_organic else 0)

    print("sql query:   \n\n", query)
    print("sql params:  \n\n", params)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    products = [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "price": row[3],
            "description": row[4],
            "is_organic": bool(row[5]),
        }
        for row in rows
    ]

    print("\n\n products query \n\n", products)
    return json.dumps(products)


# @tool
# def get_rating(product_id: int) -> str:
#     """
#     Get the average customer rating and total review count for a product by its ID.
#     Returns a JSON object with: product_id, average_rating, review_count.
#     """
#     result = get_product_rating(product_id)
#     return json.dumps(result)


# @tool
# def get_rating(product_id: int) -> str:
#     """
#     IMPORTANT: Call this for EACH product returned by search_products.
#     The argument MUST be named 'product_id' and be an integer (the product ID from the search results).
#     Example: get_rating(product_id=25)
#     Returns a JSON with average_rating and review_count.
#     """
#     result = get_product_rating(product_id)
#     return json.dumps(result)


@tool
def get_rating(product_id: int) -> str:
    """
    Get the average customer rating and total review count for a product_id.
    ARGUMENT:'`product_id' (integer) - the exact product ID from the search results.
    You MUST pass this argument with the name 'product_id' (e.g., get_rating('product_id'=25)).
    Returns a JSON object with: product_id, average_rating, review_count.
    """
    result = get_product_rating(product_id)
    print("\n\n get_rating \n\n", result)
    return json.dumps(result)


@tool
def checkout(product_id: int) -> str:
    """
    Place an order for the given product ID. Saves the order to the database and returns
    a confirmation message with the order ID, product name, and price.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return f"Error: product with ID {product_id} not found."

    name, price = row
    cursor.execute(
        "INSERT INTO orders (product_id, product_name, price) VALUES (?, ?, ?)",
        (product_id, name, price),
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return (
        f"Order #{order_id} confirmed! '{name}' has been successfully ordered for ${price:.2f}. "
        f"Your order will arrive in 3-5 business days. Thank you for shopping with us!"
    )


@tool
def describe_product_image(image_path: str) -> str:
    """
    Analyze a product image and return its key attributes as a JSON object.
    Use this when the user uploads a photo of a product they are interested in.
    The returned attributes can be used directly with search_products.
    """
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

    response = vision_llm.invoke([message])

    print("\n\n vision response \n\n", response)

    # Extract the text content - handle both string and list responses
    if isinstance(response.content, list):
        # Get the text part from the response
        for item in response.content:
            if isinstance(item, dict) and item.get("type") == "text":
                print("\n\n vision response in if \n\n", item.get("text", ""))
                return item.get("text", "")
            elif isinstance(item, str):
                print("\n\n vision response in else \n\n", item)
                return item
        print("\n\n vision response main if \n\n", str(response.content))
        return str(response.content)
    else:
        print("\n\n vision response else \n\n", response.content)
        return response.content


@tool
def set_preferences(
    category: Optional[str] = None,
    prefer_organic: Optional[bool] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """Set preferences for a category or globally."""
    return set_user_preference(category, prefer_organic, min_price, max_price)


@tool
def get_preferences(category: Optional[str] = None) -> str:
    """
    Get preferences. If category is given, return that category’s preferences.
    If no category, return all (global + every category).
    """
    if category:
        return json.dumps(get_user_preferences(category))
    else:
        return json.dumps(get_all_category_preferences())


def model_base_guardrail(input_text):
    """
    used to classify whether its product relevant query or not

    Args:
        input_text (_type_): _description_
    """

    sys_prompt = """
            You are a strict binary classifier for an e‑commerce assistant.
    
            Your task: classify the user's query as either shopping‑related or not.
    
            Return **exactly one** of these two words (no punctuation, no extra text):
            - `proceed` if the query is about products, prices, orders, reviews, inventory, carts, purchases, or recommendations.
            - `abort` for everything else (weather, news, general knowledge, personal info, etc.).
    
            Here are clear examples:
    
            User: "show me organic honey under $20" → proceed
            User: "what are the ratings for olive oil?" → proceed
            User: "I want to buy almonds" → proceed
            User: "list my purchase history" → proceed
            User: "are there any nuts in stock?" → proceed
            User: "how much did I spend last month?" → proceed
            User: "order product id 5" → proceed
            User: "tell me about the honey" → proceed
    
            User: "what's the weather like today?" → abort
            User: "who won the football match?" → abort
            User: "tell me a joke" → abort
            User: "how to cook pasta" → abort
            User: "what is the capital of France?" → abort
            User: "who are you?" → abort
    
            Now classify the following user input. Only respond with `proceed` or `abort`.
        """
    # print(f"\n\n {input_text[-1]} \n\n")

    messages = [("system", sys_prompt), ("human", input_text[-1]["content"])]
    res = llm.invoke(messages)
    return res.content.strip().lower()


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

agent = create_agent(
    tools=[
        search_products,
        get_rating,
        checkout,
        describe_product_image,
        get_order_history,
        set_preferences,
        get_preferences,
    ],
    model=llm_groq,
    system_prompt=(
        "You are a helpful shopping assistant. Follow these rules strictly.\n\n"
        "PREFERENCES — you can store and apply preferences per product category:"
        "- If the user says:"
        "I always want organic” → call set_preferences(prefer_organic=True)"
        "Never show me items over $20” → call set_preferences(max_price=20)"
        "I only want items over $15” → call set_preferences(min_price=15)"
        "I always want oil greater than $15” → call set_preferences(min_price=15, category=oil)\n"
        "I want oil between $15 and $30” → call set_preferences(category=oil, min_price=15, max_price=30)"
        "I don't care about price” → call set_preferences(min_price=None, max_price=None)"
        "- When searching, you can pass min_price and/or max_price explicitly to override stored preferences."
        "If you don't pass them, the stored preferences will be applied automatically."
        "When searching, if the user mentions a product type (e.g., “show me honey”), pass that as the category parameter to search_products so the correct preferences are applied."
        "Example: search_products(query=honey, category=honey)"
        "- If the user asks: what are my preferences? (without a specific product type)"
        "call get_preferences() - this returns all preferences (global and per category)."
        "Then present them in a readable list:"
        "- Global: Organic = ..., Min price = ..., Max price = ..."
        "- For honey: ..."
        "- For grains: ..."
        "etc."
        "- If the user asks: what are my honey preferences? (with a category),"
        "call get_preferences(category=honey) and show only those."
        "- If they say: show me my global preferences, call get_preferences(category=None)"
        "but that's the same as the first case."
        "- When searching for products, you do NOT need to pass the preference filters explicitly;\n"
        "IMAGE SEARCH — when the user provides an image path:\n"
        "1. Call describe_product_image with the path to identify the product.\n"
        "2. Use the returned search_query and is_organic to call search_products.\n"
        "3. Continue with the BROWSING flow from step 2 onwards.\n\n"
        # "BROWSING — when the user describes what they want to buy:\n"
        # "1. Call search_products to find matching items (apply any price/organic filters given).\n"
        # "2. For each candidate, call get_rating to retrieve its average rating.\n"
        # "3. Filter by the user's minimum rating if specified.\n"
        # "4. Present qualifying products as a numbered list. For each item use this exact format "
        # "   (plain text, no backticks, no code blocks, no bold, no italic):\n\n"
        # "   #<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n\n"
        # "   Add a blank line between each product entry for readability. "
        # "   Always include (ID:X) so you can reference it later.\n"
        # "5. If only one product qualifies, still show it in the list and ask: "
        # "   'Would you like to order it? Just say yes or give me the number.'\n"
        # "6. Do NOT call checkout at this stage.\n\n"
        "BROWSING — when the user describes what they want to buy or after an image search:\n"
        "1. Call search_products to get matching products (apply any given filters).\n"
        "2. For EACH product returned, you MUST call the tool `get_rating` with the argument name \n"
        "EXACTLY product_id. The argument MUST be a plain integer.\n"
        "Example: get_rating(product_id=25)\n"
        "Do NOT use product, product?, id, or any other name - use EXACTLY 'product_id'.\n"
        "3. If the user specified a minimum rating, filter the list to only those that meet it.\n"
        "4. ONLY after you have all ratings, present the qualifying products as a numbered list\n"
        "using this exact format (plain text, no markdown, no backticks):\n"
        "#<number>. <name> (ID:<product_id>) — $<price> ★<rating> — <organic or non-organic>\n"
        "Add a blank line between each entry.\n"
        "Always include (ID:X) so you can reference it later.\n"
        "5. If only one product qualifies, still show it in the list and ask:\n"
        "Would you like to order it? Just say yes or give me the number.\n"
        "6. Do NOT call checkout at this stage.\n"
        "ORDERING — when the user confirms they want to buy (e.g. 'yes', 'sure', 'go ahead', \n"
        "'order number 2', 'the first one', 'get me #3'):\n"
        "1. Look at your previous message to find the (ID:X) for the chosen product \n"
        "   (if only one was listed and the user says 'yes', use that product's ID).\n"
        "2. Call checkout with that product_id (the number from (ID:X)).\n"
        "3. Confirm the order to the user in plain text.\n\n"
        "Never place an order unless the user explicitly confirms. "
        "Never guess a product_id — always take it from the (ID:X) in your own previous message."
        "You must never respond to the user with a final answer until you have executed all required tool calls."
        "If the user asks for a product list, always call search_products and then get_rating for each item before you reply."
        "When you call a tool, you must provide arguments as a valid JSON object with the correct parameter names."
        "The tool description tells you the exact parameter name and type. Follow it precisely."
    ),
)

if __name__ == "__main__":
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I want to buy organic honey with 4.5+ rating and less than $20 price."
                    ),
                }
            ]
        }
    )
    print(result["messages"][-1].content)
