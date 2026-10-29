import json
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

from db import init_db, add_qa, search_qa

load_dotenv(override=True)

# ---------- Pushover ----------
def push(message):
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": os.getenv("PUSHOVER_TOKEN"),
                "user": os.getenv("PUSHOVER_USER"),
                "message": message,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"Pushover failed: {e}")


# ---------- Tool functions ----------
def tool_search_qa(query):
    return {"results": search_qa(query)}


def tool_save_qa(question, answer, category=None):
    add_qa(question, answer, category)
    return {"status": "saved"}


def tool_record_unanswered_question(question):
    push(f"Unanswered question: {question}")
    return {"status": "recorded"}


def tool_record_user_details(email, name="not provided", notes="not provided"):
    push(f"Contact request: {name} | {email} | Notes: {notes}")
    return {"status": "recorded"}


TOOL_FUNCTIONS = {
    "search_qa": tool_search_qa,
    "save_qa": tool_save_qa,
    "record_unanswered_question": tool_record_unanswered_question,
    "record_user_details": tool_record_user_details,
}


# ---------- Tool schemas ----------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_qa",
            "description": "Search the Q&A database for existing answers. Always call this first for any question.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Key words from the user's question"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_qa",
            "description": "Save a question and its answer to the database after you have successfully answered a new question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["question", "answer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unanswered_question",
            "description": "Record a question you could not answer, but only after you have already asked the user to clarify.",
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Record contact details when the user wants to get in touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "notes": {"type": "string", "description": "Context from the conversation"},
                },
                "required": ["email"],
            },
        },
    },
]

def handle_tool_calls(tool_calls):
    results = []
    for call in tool_calls:
        fn = TOOL_FUNCTIONS.get(call.function.name)
        args = json.loads(call.function.arguments)
        print(f"Tool: {call.function.name} {args}", flush=True)
        result = fn(**args) if fn else {"error": "unknown tool"}
        results.append({
            "role": "tool",
            "content": json.dumps(result),
            "tool_call_id": call.id,
        })
    return results
