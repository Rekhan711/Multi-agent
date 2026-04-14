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

        # "How many items are in stock?" can mean either:
        # - total units (sum of stock), or
        # - number of SKUs/positions.
        asks_how_many = any(token in lower for token in ["how many", "сколько", "количеств"])
        mentions_inventory = any(token in lower for token in ["inventory", "stock", "warehouse", "склад", "остат", "запас"])
        mentions_units = any(token in lower for token in ["unit", "units", "единиц", "штук", "шт", "кол-во единиц"])
        mentions_sku = any(token in lower for token in ["sku", "позици", "наименован", "номенклатур", "ассортимент"])

        if asks_how_many and mentions_inventory:
            if mentions_units and not mentions_sku:
                if lang == "ru":
                    return f"Единиц товара на складе (сумма остатков): {metrics['total_units_in_stock']}."
                if lang == "uz":
                    return f"Ombordagi birliklar soni (qoldiq summasi): {metrics['total_units_in_stock']}."
                return f"Total units in stock (sum of quantities): {metrics['total_units_in_stock']}."
            if mentions_sku and not mentions_units:
                if lang == "ru":
                    return f"SKU/позиций на складе: {metrics['sku_count']}."
                if lang == "uz":
                    return f"Ombordagi SKU/pozitsiyalar soni: {metrics['sku_count']}."
                return f"SKUs/positions in inventory: {metrics['sku_count']}."

            # Ambiguous: ask a concrete clarifying question (multi-turn UX).
            if lang == "ru":
                return (
                    "Под «сколько товаров на складе» вы имеете в виду:\n"
                    "1) единиц (сумма остатков в штуках)\n"
                    "2) позиций/SKU (кол-во наименований)\n"
                    "Напишите: «1» или «2»."
                )
            if lang == "uz":
                return (
                    "«Omborda nechta mahsulot bor?» deganda nimani nazarda tutyapsiz:\n"
                    "1) birliklar (qoldiq summasi)\n"
                    "2) SKU/pozitsiyalar (nomlar soni)\n"
                    "Yozing: «1» yoki «2»."
                )
            return (
                "By “how many items are in stock” do you mean:\n"
                "1) total units (sum of quantities)\n"
                "2) SKUs/positions (number of product names)\n"
                "Reply with “1” or “2”."
            )

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
            return (
                "Доступна информация по складу: количество единиц (сумма остатков), число SKU/позиций, "
                "стоимость по категориям, общая стоимость и товары с низким остатком."
            )
        if lang == "uz":
            return (
                "Ombor bo'yicha ma'lumot mavjud: birliklar soni (qoldiq summasi), SKU/pozitsiyalar soni, "
                "kategoriyalar bo'yicha qiymat, umumiy qiymat va past zaxira pozitsiyalari."
            )
        return "Inventory information is available, including stock by category and low-stock item counts."
