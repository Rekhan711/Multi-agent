import importlib.util
import os
from pathlib import Path
from typing import Optional, Tuple

import requests
import streamlit as st


def _rerun_streamlit() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
        return
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def get_api_url() -> str:
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url

    try:
        return st.secrets.get("api_url", "http://localhost:8000")
    except Exception:
        return "http://localhost:8000"


def check_api_availability(api_url: str, timeout: int = 3) -> Tuple[bool, Optional[str]]:
    try:
        response = requests.get(
            f"{api_url}/metrics",
            params={"page": "dashboard"},
            timeout=timeout,
        )
        response.raise_for_status()
        return True, None
    except requests.RequestException as error:
        return False, str(error)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Привет! Задайте бизнес-вопрос, и я помогу объединить ответы от нескольких агентов."}
        ]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def load_page_module(file_name: str):
    page_path = Path(__file__).parent / ".." / "pages" / file_name
    spec = importlib.util.spec_from_file_location(file_name, page_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_chat(api_url: str, current_page: str, api_available: bool = True):
    st.markdown("---")
    st.subheader("Multi-Agent Chat")

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])

    prompt = st.chat_input(
        "Введите вопрос для BI-системы...",
        disabled=not api_available,
    )
    if not api_available:
        st.info("Chat is temporarily unavailable because API is not reachable.")
        return
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Send a short window of history so backend can resolve context.
        # Keep it small to avoid large requests and latency.
        history = st.session_state.messages[-12:]
        payload = {"question": prompt, "page": current_page, "messages": history}
        try:
            response = requests.post(
                f"{api_url}/chat",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            answer = data.get("answer", "Не удалось получить ответ.")
        except Exception as error:
            answer = f"Ошибка при обращении к API: {error}"
        st.session_state.messages.append({"role": "assistant", "content": answer})
        _rerun_streamlit()
