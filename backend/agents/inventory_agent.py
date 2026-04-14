from sqlalchemy.orm import Session

from ..core.llm_client import detect_language
from ..core.metrics import gather_inventory_metrics
from ..db.models import Inventory
from ..db.warehouse import WarehouseClient


class InventoryAgent:
    def __init__(self, db: Session):
        self.db = db
        self.warehouse = WarehouseClient(db)

    def summary(self) -> str:
        metrics = gather_inventory_metrics(self.db)
        return f"Inventory holds {len(metrics['inventory_by_category'])} categories and {metrics['low_stock_items']} low-stock items."

    def answer_question(self, question: str) -> str:
        metrics = gather_inventory_metrics(self.db)
        lower = question.lower()
        lang = detect_language(question)

        if ("low" in lower and "stock" in lower) or ("\u043d\u0438\u0437\u043a" in lower and "\u043e\u0441\u0442\u0430\u0442" in lower):
            if lang == "ru":
                return f"Товаров с низким остатком: {metrics['low_stock_items']}."
            if lang == "uz":
                return f"Past zaxirali pozitsiyalar soni: {metrics['low_stock_items']}."
            return f"There are {metrics['low_stock_items']} items with low stock levels."

        if "category" in lower or "\u043a\u0430\u0442\u0435\u0433\u043e\u0440" in lower:
            categories = ", ".join([f"{row['category']} (${row['value']:.0f})" for row in metrics["inventory_by_category"]])
            if lang == "ru":
                return f"Стоимость запасов по категориям: {categories}."
            if lang == "uz":
                return f"Kategoriyalar bo'yicha ombor qiymati: {categories}."
            return f"Inventory value by category: {categories}."

        if "total" in lower or "value" in lower or "\u0441\u0442\u043e\u0438\u043c" in lower or "qiymat" in lower:
            if lang == "ru":
                return f"Общая стоимость запасов: ${metrics['total_inventory_value']:.2f}."
            if lang == "uz":
                return f"Omborning umumiy qiymati: ${metrics['total_inventory_value']:.2f}."
            return f"Total inventory value is ${metrics['total_inventory_value']:.2f}."

        if lang == "ru":
            return "Доступна информация по складу: стоимость по категориям и товары с низким остатком."
        if lang == "uz":
            return "Ombor bo'yicha ma'lumot mavjud: kategoriya kesimida qiymat va past zaxira pozitsiyalari."
        return "Inventory information is available, including stock by category and low-stock item counts."
