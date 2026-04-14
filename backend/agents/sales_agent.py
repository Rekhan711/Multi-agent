from sqlalchemy.orm import Session

from ..core.llm_client import detect_language
from ..core.metrics import gather_sales_metrics
from ..db.models import Sales
from ..db.warehouse import WarehouseClient


class SalesAgent:
    def __init__(self, db: Session):
        self.db = db
        self.warehouse = WarehouseClient(db)

    def summary(self) -> str:
        metrics = gather_sales_metrics(self.db)
        total = sum(item["revenue"] for item in metrics["sales_by_region"])
        return (
            f"Sales reported {len(metrics['sales_by_product'])} top products and total region revenue of ${total:.2f}."
        )

    def answer_question(self, question: str) -> str:
        lower = question.lower()
        lang = detect_language(question)
        metrics = gather_sales_metrics(self.db)

        if ("top" in lower and "product" in lower) or ("\u0442\u043e\u043f" in lower and "\u043f\u0440\u043e\u0434\u0443\u043a\u0442" in lower):
            products = sorted(metrics["sales_by_product"], key=lambda item: item["revenue"], reverse=True)
            top_products = ", ".join([f"{item['product']} (${item['revenue']:.0f})" for item in products[:3]])
            if lang == "ru":
                return f"Топ-3 продукта по выручке: {top_products}."
            if lang == "uz":
                return f"Daromad bo'yicha top-3 mahsulot: {top_products}."
            return f"Top sales products are: {top_products}."

        if "region" in lower or "\u0440\u0435\u0433\u0438\u043e\u043d" in lower or "hudud" in lower:
            regions = metrics["sales_by_region"]
            region_lines = ", ".join([f"{row['region']} (${row['revenue']:.0f})" for row in regions])
            if lang == "ru":
                return f"Выручка по регионам: {region_lines}."
            if lang == "uz":
                return f"Hududlar bo'yicha daromad: {region_lines}."
            return f"Revenue by region: {region_lines}."

        if any(
            token in lower
            for token in [
                "increase sales",
                "grow sales",
                "\u0443\u0432\u0435\u043b\u0438\u0447",
                "\u0440\u043e\u0441\u0442 \u043f\u0440\u043e\u0434\u0430\u0436",
                "\u043f\u043e\u0434\u043d\u044f\u0442\u044c \u043f\u0440\u043e\u0434\u0430\u0436\u0438",
                "savdoni oshir",
                "savdo o'sishi",
                "savdo osishi",
                "savdoni ko'paytir",
                "savdoni kopaytir",
            ]
        ) or ("savdo" in lower and "oshir" in lower):
            products = sorted(metrics.get("sales_by_product", []), key=lambda item: item["revenue"], reverse=True)
            regions = sorted(metrics.get("sales_by_region", []), key=lambda item: item["revenue"], reverse=True)
            top_product = products[0]["product"] if products else "N/A"
            top_region = regions[0]["region"] if regions else "N/A"
            if lang == "ru":
                return (
                    "Чтобы увеличить продажи, опирайтесь на данные: "
                    f"1) масштабируйте лучший продукт '{top_product}', "
                    f"2) усиливайте каналы в сильном регионе '{top_region}' и переносите практики в слабые регионы, "
                    "3) повышайте конверсию через пакетные предложения и допродажи для средних продуктов, "
                    "4) ускоряйте обработку открытых сделок и контролируйте недельную долю закрытия."
                )
            if lang == "uz":
                return (
                    "Savdoni oshirish uchun ma'lumotlarga tayangan reja: "
                    f"1) eng kuchli mahsulot '{top_product}' bo'yicha investitsiyani ko'paytiring, "
                    f"2) kuchli hudud '{top_region}' dagi kanallarni kengaytirib, tajribani sust hududlarga ko'chiring, "
                    "3) o'rta mahsulotlar uchun bundle/upsell orqali konversiyani oshiring, "
                    "4) ochiq bitimlar bilan ishlash tezligini va weekly close-rate ni nazorat qiling."
                )
            return (
                "To increase sales, prioritize these actions: "
                f"1) scale top product '{top_product}', "
                f"2) expand winning region '{top_region}' and replicate channel mix, "
                "3) improve conversion with bundle/upsell offers, "
                "4) improve pipeline follow-up speed and weekly close-rate."
            )

        total_revenue = self.db.query(Sales).with_entities(Sales.revenue).all()
        if total_revenue:
            total = sum([r[0] for r in total_revenue])
            if lang == "ru":
                return f"Суммарная выручка по продажам: ${total:.2f}."
            if lang == "uz":
                return f"Savdo bo'yicha jami daromad: ${total:.2f}."
            return f"Total sales revenue is ${total:.2f}."

        if lang == "ru":
            return "Данные по продажам пока недоступны."
        if lang == "uz":
            return "Savdo ma'lumotlari hozircha mavjud emas."
        return "Sales data is currently unavailable."
