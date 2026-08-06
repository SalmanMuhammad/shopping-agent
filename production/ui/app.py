import os
import sys
import tempfile
import streamlit as st

# Ensure project base directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from production.agent.shopping_agent import agent
from production.agent.guardrail import model_base_guardrail
from production.logger import logger

# ---------------------------------------------------------------------------
# Page Config & Custom Styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Organic Harvest — AI Shopping Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Main Theme Overrides */
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
    }
    
    /* Header Card */
    .header-container {
        background: linear-gradient(135deg, #1e2638 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
    }
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Badge & Tag Pills */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .badge-green {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161e2e;
        border-right: 1px solid #1e293b;
    }

    /* Chat message enhancements */
    .stChatMessage {
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header Section
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="header-container">
        <h1 class="header-title">🛒 Organic Harvest AI Shopping Assistant</h1>
        <p class="header-subtitle">
            <span class="badge badge-green">Production Ready</span>
            Tell me what you need — search products, apply custom preferences, evaluate ratings, or upload product photos.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — Visual Search & Shortcuts
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📸 Visual Product Search")
    st.caption("Upload a photo of any grocery or item to instantly find matching inventory.")

    uploaded_file = st.file_uploader(
        "Upload image", type=["jpg", "jpeg", "png", "webp", "avif"]
    )

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)

    if uploaded_file and st.button("🔍 Find Similar Products", use_container_width=True):
        suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            image_path = tmp.name

        prompt = f"I uploaded a product image. Please analyze it and find similar products in the store. Image path: {image_path}"
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_image = uploaded_file.name
        st.rerun()

    st.markdown("---")
    st.subheader("💡 Quick Prompts")
    quick_prompts = [
        "Organic honey under $20 with 4.5+ rating",
        "Show me snacks",
        "I always want organic oil over $15",
        "What are my stored preferences?",
        "List my order history",
    ]
    for q in quick_prompts:
        if st.button(q, key=f"btn_{q}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Chat History Display
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user" and msg["content"].startswith("I uploaded a product image"):
            st.markdown(f"📷 **Searching by uploaded image**")
        else:
            # Escape dollar signs for clean Streamlit rendering
            content = msg["content"].replace("$", r"\$")
            st.markdown(content)

# ---------------------------------------------------------------------------
# Handle Unprocessed Image Message
# ---------------------------------------------------------------------------
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and "pending_image" in st.session_state
):
    with st.chat_message("assistant"):
        with st.spinner("Analyzing uploaded image & querying catalog..."):
            try:
                result = agent.invoke({"messages": st.session_state.messages})
                response = result["messages"][-1].content.replace("`", "")
            except Exception as e:
                logger.error(f"Error during image agent invocation: {e}")
                response = f"Sorry, an error occurred while processing the image: {e}"

        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    del st.session_state.pending_image
    st.rerun()

# ---------------------------------------------------------------------------
# Interactive Chat Input & Guardrail Processing
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask for organic honey, nuts, coffee, preferences, or orders..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing request..."):
            status = model_base_guardrail(st.session_state.messages)
            logger.info(f"Query guardrail decision: {status}")

            if status == "proceed":
                try:
                    result = agent.invoke({"messages": st.session_state.messages})
                    response = result["messages"][-1].content.replace("`", "")
                except Exception as e:
                    logger.error(f"Agent execution error: {e}")
                    response = f"An error occurred while handling your request: {e}"
            else:
                response = (
                    "⚠️ I am a specialized shopping assistant for Organic Harvest store. "
                    "I can only help you search products, view reviews, manage preferences, and place orders."
                )

        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
