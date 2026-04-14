import pandas as pd
import requests
import streamlit as st


def render(api_url: str):
    st.title("Inventory")
    st.write("Оценка запасов, стоимость и распределение по категориям.")
    try:
        data = requests.get(f"{api_url}/metrics", params={"page": "inventory"}, timeout=15).json()
    except Exception as error:
        st.error(f"Не удалось получить данные инвентаря: {error}")
        return

    st.metric("Total stock value", f"${data.get('total_inventory_value', 0):,.0f}")
    st.metric("Low stock items", data.get("low_stock_items", 0))

    st.subheader("Inventory value by category")
    if data.get("inventory_by_category"):
        df = pd.DataFrame(data["inventory_by_category"]).set_index("category")
        st.bar_chart(df["value"])
    else:
        st.info("Нет данных по категориям.")
