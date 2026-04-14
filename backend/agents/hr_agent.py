from sqlalchemy.orm import Session

from ..core.llm_client import detect_language
from ..core.metrics import gather_hr_metrics
from ..db.warehouse import WarehouseClient


class HRAgent:
    def __init__(self, db: Session):
        self.db = db
        self.warehouse = WarehouseClient(db)

    def summary(self) -> str:
        metrics = gather_hr_metrics(self.db)
        return f"HR analytics covers {metrics['headcount']} employees and a turnover count of {metrics['turnover']}."

    def answer_question(self, question: str) -> str:
        lower = question.lower()
        lang = detect_language(question)
        metrics = gather_hr_metrics(self.db)

        if (
            ("sales" in lower or "\u043f\u0440\u043e\u0434\u0430\u0436" in lower or "savdo" in lower)
            and (
                "employee" in lower
                or "headcount" in lower
                or "hr" in lower
                or "\u0441\u043e\u0442\u0440\u0443\u0434" in lower
                or "\u043f\u0435\u0440\u0441\u043e\u043d" in lower
                or "xodim" in lower
            )
        ):
            if lang == "ru":
                return (
                    f"Текущая HR-база: headcount = {metrics['headcount']}, turnover = {metrics['turnover']}. "
                    "При росте продаж обычно первой растет нагрузка на Sales, Customer Success и Operations. "
                    "Рекомендуется ежемесячно отслеживать скорость найма, нагрузку на сотрудника и текучесть."
                )
            if lang == "uz":
                return (
                    f"Hozirgi HR holati: headcount = {metrics['headcount']}, turnover = {metrics['turnover']}. "
                    "Savdo o'sganda odatda Sales, Customer Success va Operations jamoalarida yuklama tez ortadi. "
                    "Har oy yollash tezligi, bir xodimga yuklama va turnover ni kuzating."
                )
            return (
                f"Current HR baseline: headcount is {metrics['headcount']} and turnover is {metrics['turnover']}. "
                "If sales grow, workload usually rises first in Sales, Customer Success, and Operations. "
                "Track hiring lead time, capacity per employee, and turnover monthly."
            )

        if "headcount" in lower or "employees" in lower or "\u0441\u043e\u0442\u0440\u0443\u0434" in lower or "xodim" in lower:
            if lang == "ru":
                return f"Текущий headcount: {metrics['headcount']}."
            if lang == "uz":
                return f"Joriy headcount: {metrics['headcount']}."
            return f"Current headcount is {metrics['headcount']}."

        if "turnover" in lower or "attrition" in lower or "\u0442\u0435\u043a\u0443\u0447" in lower:
            if lang == "ru":
                return f"Текучесть (кол-во увольнений): {metrics['turnover']}."
            if lang == "uz":
                return f"Turnover (ketganlar soni): {metrics['turnover']}."
            return f"Turnover count in the sample dataset is {metrics['turnover']}."

        if "department" in lower or "\u043e\u0442\u0434\u0435\u043b" in lower:
            breakdown = ", ".join([f"{row['department']} ({row['count']})" for row in metrics["department_distribution"]])
            if lang == "ru":
                return f"Распределение по отделам: {breakdown}."
            if lang == "uz":
                return f"Bo'limlar kesimidagi taqsimot: {breakdown}."
            return f"Employee distribution by department: {breakdown}."

        if lang == "ru":
            return "HR-аналитика доступна по headcount, текучести, найму и распределению по отделам."
        if lang == "uz":
            return "HR analitika headcount, turnover, yollash va bo'limlar kesimi bo'yicha mavjud."
        return "HR analytics can report on headcount, turnover, hiring trends, and department distribution."
