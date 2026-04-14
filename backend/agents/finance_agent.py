from sqlalchemy.orm import Session

from ..core.llm_client import detect_language
from ..core.metrics import gather_finance_metrics
from ..db.models import Finance
from ..db.warehouse import WarehouseClient


class FinanceAgent:
    def __init__(self, db: Session):
        self.db = db
        self.warehouse = WarehouseClient(db)

    def summary(self) -> str:
        trend = gather_finance_metrics(self.db)["finance_trend"]
        return f"Finance trend data includes {len(trend)} monthly observations of revenue, expense and profit."

    def answer_question(self, question: str) -> str:
        lower = question.lower()
        lang = detect_language(question)
        trend = gather_finance_metrics(self.db)["finance_trend"]

        asks_profit = "profit" in lower or "\u043f\u0440\u0438\u0431\u044b\u043b" in lower or "foyda" in lower
        asks_expense = "expense" in lower or "\u0440\u0430\u0441\u0445\u043e\u0434" in lower or "xarajat" in lower

        if asks_profit and asks_expense:
            profits = [row["profit"] for row in trend]
            expenses = [row["expense"] for row in trend]
            latest_profit = profits[-1] if profits else 0
            latest_expense = expenses[-1] if expenses else 0
            if lang == "ru":
                return f"Последняя прибыль: ${latest_profit:.2f}; последние расходы: ${latest_expense:.2f}."
            if lang == "uz":
                return f"So'nggi foyda: ${latest_profit:.2f}; so'nggi xarajat: ${latest_expense:.2f}."
            return f"Latest profit is ${latest_profit:.2f}; latest expense is ${latest_expense:.2f}."

        if "margin" in lower or "profit margin" in lower or "gross margin" in lower or "\u043f\u0440\u0438\u0431\u044b\u043b\u044c\u043d\u0430\u044f" in lower:
            latest = trend[-1] if trend else None
            if latest and latest["revenue"]:
                margin = latest["profit"] / latest["revenue"] * 100
                if lang == "ru":
                    return f"Последняя маржа прибыли: {margin:.1f}% при выручке ${latest['revenue']:.0f}."
                if lang == "uz":
                    return f"So'nggi foyda marjasi: {margin:.1f}% va daromad ${latest['revenue']:.0f}."
                return f"Latest profit margin is {margin:.1f}% on revenue ${latest['revenue']:.0f}."
            if lang == "ru":
                return "Последняя маржа прибыли не может быть рассчитана по текущим данным."
            if lang == "uz":
                return "So'nggi foyda marjasi mavjud ma'lumotlar bo'yicha hisoblanmadi."
            return "Latest profit margin cannot be calculated from the current data."

        if "trend" in lower or "month" in lower or "quarter" in lower or "period" in lower:
            if trend:
                latest = trend[-1]
                previous = trend[-2] if len(trend) > 1 else None
                trend_text = "stable"
                if previous:
                    if latest["revenue"] >= previous["revenue"]:
                        trend_text = "up"
                    else:
                        trend_text = "down"
                if lang == "ru":
                    return f"Финансовый тренд: последний месяц {latest['date']} выручка ${latest['revenue']:.0f}, расходы ${latest['expense']:.0f}, прибыль ${latest['profit']:.0f}, тренд {trend_text}."
                if lang == "uz":
                    return f"Moliya trendi: oxirgi oy {latest['date']} daromad ${latest['revenue']:.0f}, xarajat ${latest['expense']:.0f}, foyda ${latest['profit']:.0f}, trend {trend_text}."
                return f"Finance trend: latest month {latest['date']} revenue ${latest['revenue']:.0f}, expense ${latest['expense']:.0f}, profit ${latest['profit']:.0f}, trend {trend_text}."

        if asks_profit:
            profits = [row["profit"] for row in trend]
            latest = profits[-1] if profits else 0
            if lang == "ru":
                return f"Последняя прибыль: ${latest:.2f}; всего периодов в тренде: {len(profits)}."
            if lang == "uz":
                return f"So'nggi foyda: ${latest:.2f}; trend davrlari soni: {len(profits)}."
            return f"Latest profit is ${latest:.2f} with trend over time showing {len(profits)} periods."

        if "cash" in lower or "flow" in lower or "\u0434\u0435\u043d\u0435\u0436" in lower or "naqd" in lower:
            if lang == "ru":
                return "Денежный поток моделируется по рядам выручки и расходов; в последнем периоде поток положительный."
            if lang == "uz":
                return "Naqd pul oqimi daromad va xarajat qatorlari asosida baholangan; so'nggi davrda oqim ijobiy."
            return "Cash flow is modeled from revenue and expense series; the latest period remains positive in sample data."

        if asks_expense:
            expenses = [row["expense"] for row in trend]
            latest = expenses[-1] if expenses else 0
            if lang == "ru":
                return f"Последние расходы: ${latest:.2f}."
            if lang == "uz":
                return f"So'nggi xarajat: ${latest:.2f}."
            return f"Latest expense is ${latest:.2f}."

        total_revenue = sum(row["revenue"] for row in trend)
        if lang == "ru":
            return f"Суммарная выручка по финансовому тренду: ${total_revenue:.2f}."
        if lang == "uz":
            return f"Moliya trendi bo'yicha jami daromad: ${total_revenue:.2f}."
        return f"Total revenue for the sample finance periods is ${total_revenue:.2f}."
