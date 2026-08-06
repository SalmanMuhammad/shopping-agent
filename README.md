# 🛒 AI Shopping Assistant (Production Grade)

An enterprise-ready conversational AI shopping agent built with **LangChain**, **LangGraph**, **Groq**, **Ollama**, and **Streamlit**. The assistant helps users discover organic products, apply category-specific and global preferences, view aggregated customer reviews/ratings, perform visual image searches, and manage checkouts and order history.

---

## ✨ Features

- **🔍 Smart Product Search**: Natural language search with automatic filtering by price, category, and organic attributes.
- **⚙️ Context-Aware Preference Management**: Set global or category-specific user preferences (e.g. *"I always want organic oil over $15"*).
- **⭐ Review & Rating Aggregation**: Real-time batch and individual product rating queries.
- **📸 Visual Search (Multimodal)**: Upload product images to automatically extract product attributes via vision models (Ollama Llava) and search matching store inventory.
- **🛡️ Query Guardrail Classifier**: Intelligent safety guardrail ensuring non-shopping queries are intercepted gracefully.
- **🛍️ Seamless Order Management**: Place orders and track complete order history.
- **🎨 Modern Streamlit UI**: Dark mode UI with custom CSS, interactive quick-prompt shortcuts, image previews, and clean markdown formatting.

---

## 📁 Repository Architecture

The project has been refactored into a production package in [`production/`](file:///Users/macbook/Desktop/work/ollama/agents/shopping-agent/production):

```
shopping-agent/
├── production/
│   ├── config.py              # Application settings & environment configurations
│   ├── logger.py              # Standardized structured logging framework
│   │
│   ├── database/              # Data persistence layer
│   │   ├── connection.py      # Thread-safe SQLite context manager
│   │   ├── repository.py      # Repositories for Products, Reviews, Preferences, Orders
│   │   └── setup.py           # DB migration & seed data initializer
│   │
│   ├── models/                # Pydantic schemas
│   │   └── schemas.py         # Type validation definitions
│   │
│   ├── services/              # Domain business services
│   │   ├── product_service.py # Product search & preference inheritance
│   │   ├── review_service.py  # Rating aggregations
│   │   ├── order_service.py   # Checkout & order history
│   │   ├── preference_service.py # Global/category preference CRUD
│   │   └── vision_service.py  # Image attribute extraction
│   │
│   ├── agent/                 # LangChain & LangGraph agent orchestration
│   │   ├── llm_factory.py     # Safe LLM initialization (Groq primary, Ollama fallback)
│   │   ├── guardrail.py       # Query classification guardrail
│   │   ├── prompts.py         # Externalized prompt templates
│   │   ├── tools.py           # Strongly-typed agent tools
│   │   └── shopping_agent.py  # Agent graph runner
│   │
│   ├── ui/                    # Presentation layer
│   │   └── app.py             # Streamlit application
│   │
│   └── tests/                 # Test suite
│       ├── test_services.py   # Unit tests for domain services & database
│       ├── test_tool_call_acc.py # Tool calling precision tests
│       └── test_model_response_quality.py # Response quality judge tests
│
├── store.db                   # SQLite database
├── .env                       # Environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** (optional for local models like `llama3.2` and `llava`)

### 2. Environment Setup & Dependency Installation

Clone the repository and install the dependencies:

```bash
# Install required Python packages
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Create or update your `.env` file in the root directory:

```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEXT_MODEL=llama3.2
OLLAMA_VISION_MODEL=llava
LOG_LEVEL=INFO
```

### 4. Database Setup

Initialize the SQLite database schema and load seed data:

```bash
python -m production.database.setup
```

---

## 🏃 Running the Application

Launch the Streamlit web application:

```bash
streamlit run production/ui/app.py
```

---

## 🧪 Running Tests

### Run Domain Unit Tests
```bash
python -m production.tests.test_services
```

### Run Agent Tool Calling Accuracy Tests
```bash
python -m production.tests.test_tool_call_acc
```

### Run Model Response Quality Judge Evaluation
```bash
python -m production.tests.test_model_response_quality
```
