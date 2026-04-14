import pandas as pd
import requests
import streamlit as st


def render(api_url: str):
    st.title("Finance")
    st.write("Финансовые показатели, динамика прибыли и расходов.")
    try:
        data = requests.get(f"{api_url}/metrics", params={"page": "finance"}, timeout=15).json()
    except Exception as error:
        st.error(f"Не удалось получить финансовые метрики: {error}")
        return

    trend = data.get("finance_trend", [])
    if trend:
        latest = trend[-1]
        st.metric("Latest Revenue", f"${latest.get('revenue', 0):,.0f}")
        st.metric("Latest Profit", f"${latest.get('profit', 0):,.0f}")
        st.metric("Latest Expense", f"${latest.get('expense', 0):,.0f}")
        df = pd.DataFrame(trend).set_index("date")
        st.line_chart(df[["revenue", "expense", "profit"]])
    else:
        st.info("Нет данных по финансам.")
