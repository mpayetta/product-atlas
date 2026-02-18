import os
import requests

# Values come from config/settings.env via app/__init__.py
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3:8b")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

def chat(messages, temperature=None):
    if temperature is None:
        temperature = LLM_TEMPERATURE

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": LLM_MAX_TOKENS,
        },
    }
    resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]

def ask_system(user_message, system_prompt):
    """
    Convenience helper: set system + user message, get answer text.
    """
    msgs = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return chat(msgs)

def chat_with_history(history, user_message, system_prompt=None, temperature=None):
    """
    history: list of {"role": "user"|"assistant", "content": str}
    user_message: latest user message (str)
    system_prompt: optional system-level instruction (str)
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    return chat(messages, temperature=temperature)