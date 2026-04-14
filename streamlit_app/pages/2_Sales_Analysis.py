import pandas as pd
import requests
import streamlit as st


def render(api_url: str):
    st.title("Sales Analysis")
    st.write("Маркетинговый и продажный обзор с фильтрами по продуктам и регионам.")
    try:
        data = requests.get(f"{api_url}/metrics", params={"page": "sales"}, timeout=15).json()
    except Exception as error:
        st.error(f"Не удалось получить данные продаж: {error}")
        return

    products = [row["product"] for row in data.get("sales_by_product", [])]
    regions = [row["region"] for row in data.get("sales_by_region", [])]
    product_filter = st.selectbox("Продукт", options=["Все"] + products)
    region_filter = st.selectbox("Регион", options=["Все"] + regions)

    sales_rows = []
    for row in data.get("sales_by_product", []):
        if product_filter != "Все" and row["product"] != product_filter:
            continue
        sales_rows.append(row)

    st.metric("Monthly revenue", f"${sum(row['revenue'] for row in data.get('monthly_revenue', [])):.0f}")
    st.metric("Top product", products[0] if products else "—")

    st.subheader("Revenue by product")
    if sales_rows:
        df = pd.DataFrame(sales_rows)
        st.bar_chart(df.set_index("product")["revenue"])
    else:
        st.info("Нет выбранных данных.")

    st.subheader("Revenue by region")
    if data.get("sales_by_region"):
        df_region = pd.DataFrame(data["sales_by_region"]).set_index("region")
        st.bar_chart(df_region["revenue"])
    else:
        st.info("Нет данных по регионам.")
