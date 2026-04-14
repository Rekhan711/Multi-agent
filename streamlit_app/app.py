import streamlit as st

from components.ui import (
    check_api_availability,
    get_api_url,
    init_session_state,
    load_page_module,
    render_chat,
)


PAGE_FILES = {
    "Dashboard": "1_Dashboard.py",
    "Sales": "2_Sales_Analysis.py",
    "Inventory": "3_Inventory.py",
    "Finance": "4_Finance.py",
    "HR": "5_HR_Analytics.py",
}


def main():
    st.set_page_config(page_title="Multi-Agent BI", layout="wide")
    init_session_state()

    with st.sidebar:
        st.title("BI Multi-Agent")
        page = st.radio("Навигация", list(PAGE_FILES.keys()))
        st.markdown("---")
        st.write("Задайте вопрос внизу чата.")

    api_url = get_api_url()
    api_available, api_error = check_api_availability(api_url)
    page_file = PAGE_FILES[page]
    page_module = load_page_module(page_file)

    if not api_available:
        with st.sidebar:
            st.error("Backend API is not reachable.")
            st.caption(f"Configured API URL: {api_url}")
            st.caption("Start backend: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000")
            if api_error:
                st.caption(f"Connection detail: {api_error}")

    page_module.render(api_url)
    render_chat(api_url, page, api_available=api_available)


if __name__ == "__main__":
    main()
