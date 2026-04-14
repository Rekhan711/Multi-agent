from typing import Any, Callable, Dict, List

from ..core.knowledge_index import BusinessKnowledgeIndex
from ..core.llm_client import detect_language, is_smalltalk, smalltalk_response, synthesize_business_answer
from .finance_agent import FinanceAgent
from .hr_agent import HRAgent
from .inventory_agent import InventoryAgent
from .sales_agent import SalesAgent


class Orchestrator:
    def __init__(self, db_session):
        self.db_session = db_session
        self.knowledge_index = BusinessKnowledgeIndex()
        self.sales = SalesAgent(db_session)
        self.inventory = InventoryAgent(db_session)
        self.finance = FinanceAgent(db_session)
        self.hr = HRAgent(db_session)
        self.execution_trace: List[str] = []

    def _record(self, tool_name: str) -> None:
        if tool_name not in self.execution_trace:
            self.execution_trace.append(tool_name)

    def _sales_tool(self, query: str) -> str:
        self._record("sales")
        return self.sales.answer_question(query)

    def _inventory_tool(self, query: str) -> str:
        self._record("inventory")
        return self.inventory.answer_question(query)

    def _finance_tool(self, query: str) -> str:
        self._record("finance")
        return self.finance.answer_question(query)

    def _hr_tool(self, query: str) -> str:
        self._record("hr")
        return self.hr.answer_question(query)

    def _knowledge_tool(self, query: str) -> str:
        self._record("knowledge")
        return self.knowledge_index.query(query)

    def handle(self, question: str) -> Dict[str, Any]:
        question = question.strip()
        if not question:
            return {"answer": "Please provide a business question.", "agents": []}

        self.execution_trace = []
        lang = detect_language(question)
        if is_smalltalk(question):
            return {"answer": smalltalk_response(lang), "agents": []}

        selected_tools = self._route(question)
        tool_map: Dict[str, Callable[[str], str]] = {
            "sales_tool": self._sales_tool,
            "inventory_tool": self._inventory_tool,
            "finance_tool": self._finance_tool,
            "hr_tool": self._hr_tool,
            "knowledge_tool": self._knowledge_tool,
        }

        if not selected_tools:
            selected_tools = ["knowledge_tool"]

        tool_outputs: Dict[str, str] = {}
        for tool_name in selected_tools:
            tool_fn = tool_map.get(tool_name)
            if not tool_fn:
                continue
            try:
                tool_outputs[tool_name] = tool_fn(question)
            except Exception as error:
                tool_outputs[tool_name] = f"{tool_name} failed: {error}"

        answer = synthesize_business_answer(question, tool_outputs, lang)
        return {"answer": answer, "agents": self.execution_trace}

    def _route(self, question: str) -> List[str]:
        low = question.lower()
        tools: List[str] = []

        sales_kw = [
            "sales",
            "revenue",
            "deal",
            "product",
            "region",
            "savdo",
            "daromad",
            "mahsulot",
            "hudud",
            "\u043f\u0440\u043e\u0434\u0430\u0436",
            "\u0432\u044b\u0440\u0443\u0447\u043a",
            "\u0441\u0434\u0435\u043b\u043a",
            "\u043f\u0440\u043e\u0434\u0443\u043a\u0442",
            "\u0440\u0435\u0433\u0438\u043e\u043d",
        ]
        inventory_kw = [
            "inventory",
            "stock",
            "warehouse",
            "supply",
            "sku",
            "ombor",
            "zaxira",
            "qoldiq",
            "\u0441\u043a\u043b\u0430\u0434",
            "\u0437\u0430\u043f\u0430\u0441",
            "\u043e\u0441\u0442\u0430\u0442",
            "\u043f\u043e\u0441\u0442\u0430\u0432",
        ]
        finance_kw = [
            "finance",
            "profit",
            "expense",
            "cash",
            "budget",
            "loss",
            "moliya",
            "foyda",
            "xarajat",
            "byudjet",
            "\u0444\u0438\u043d\u0430\u043d\u0441",
            "\u043f\u0440\u0438\u0431\u044b\u043b",
            "\u0440\u0430\u0441\u0445\u043e\u0434",
            "\u0431\u044e\u0434\u0436\u0435\u0442",
            "\u0443\u0431\u044b\u0442",
        ]
        hr_kw = [
            "hr",
            "employee",
            "headcount",
            "turnover",
            "hiring",
            "attrition",
            "xodim",
            "ishchi",
            "kadr",
            "\u043f\u0435\u0440\u0441\u043e\u043d\u0430\u043b",
            "\u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a",
            "\u0448\u0442\u0430\u0442",
            "\u0442\u0435\u043a\u0443\u0447",
            "\u043d\u0430\u0439\u043c",
        ]
        knowledge_kw = [
            "business",
            "strategy",
            "market",
            "trend",
            "analysis",
            "biznes",
            "strategiya",
            "bozor",
            "tahlil",
            "\u0431\u0438\u0437\u043d\u0435\u0441",
            "\u0441\u0442\u0440\u0430\u0442\u0435\u0433",
            "\u0440\u044b\u043d\u043e\u043a",
            "\u0442\u0440\u0435\u043d\u0434",
            "\u0430\u043d\u0430\u043b\u0438\u0437",
        ]

        if self._contains_any(low, sales_kw):
            tools.append("sales_tool")
        if self._contains_any(low, inventory_kw):
            tools.append("inventory_tool")
        if self._contains_any(low, finance_kw):
            tools.append("finance_tool")
        if self._contains_any(low, hr_kw):
            tools.append("hr_tool")
        if self._contains_any(low, knowledge_kw):
            tools.append("knowledge_tool")
        return tools

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        return any(keyword in text for keyword in keywords)
