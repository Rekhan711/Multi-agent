import pandas as pd
import requests
import streamlit as st


def render(api_url: str):
    st.title("HR Analytics")
    st.write("Показатели по сотрудникам: headcount, turnover и распределение по отделам.")
    try:
        data = requests.get(f"{api_url}/metrics", params={"page": "hr"}, timeout=15).json()
    except Exception as error:
        st.error(f"Не удалось получить HR-метрики: {error}")
        return

    st.metric("Headcount", data.get("headcount", 0))
    st.metric("Turnover", data.get("turnover", 0))

    distribution = data.get("department_distribution", [])
    if distribution:
        df = pd.DataFrame(distribution).set_index("department")
        st.bar_chart(df["count"])
    else:
        st.info("Нет данных по распределению сотрудников.")
