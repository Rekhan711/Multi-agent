import requests
import streamlit as st


def render(api_url: str):
    st.title("Dashboard")
    st.write("Обзор ключевых KPI и простая визуализация показателей бизнеса.")
    try:
        metrics = requests.get(f"{api_url}/metrics", params={"page": "dashboard"}, timeout=15).json()
    except Exception as error:
        st.error(f"Не удалось загрузить метрики: {error}")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${metrics.get('total_revenue', 0):,.0f}")
    col2.metric("Active Deals", metrics.get("active_deals", 0))
    col3.metric("Inventory Value", f"${metrics.get('inventory_value', 0):,.0f}")
    col4.metric("Employee Count", metrics.get("employee_count", 0))

    st.subheader("Revenue by region")
    try:
        sales_data = requests.get(f"{api_url}/metrics", params={"page": "sales"}, timeout=15).json()
    except Exception as error:
        st.warning(f"РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РґР°РЅРЅС‹Рµ РїСЂРѕРґР°Р¶ РґР»СЏ РіСЂР°С„РёРєРѕРІ: {error}")
        sales_data = {}
    region_rows = sales_data.get("sales_by_region", [])
    if region_rows:
        region_df = {
            row["region"]: row["revenue"] for row in region_rows
        }
        st.bar_chart(region_df)
    else:
        st.info("Нет доступных данных по регионам.")

    st.subheader("Monthly revenue trend")
    monthly = sales_data.get("monthly_revenue", [])
    if monthly:
        trend_df = {row["date"]: row["revenue"] for row in monthly}
        st.line_chart(trend_df)
    else:
        st.info("Нет доступных данных по месяцам.")
