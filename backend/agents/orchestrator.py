from typing import Any, Callable, Dict, List, Optional

from ..core.knowledge_index import BusinessKnowledgeIndex
from ..core.llm_client import (
    choose_tools_for_question,
    detect_language,
    is_smalltalk,
    smalltalk_response,
    synthesize_business_answer,
)
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

    def handle(self, question: str, page: Optional[str] = None, messages: Optional[list[dict]] = None) -> Dict[str, Any]:
        question = question.strip()
        if not question:
            return {"answer": "Please provide a business question.", "agents": []}

        self.execution_trace = []
        lang = detect_language(question)
        if is_smalltalk(question):
            return {"answer": smalltalk_response(lang), "agents": []}

        selected_tools = self._route(question, page=page, messages=messages)
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

        answer = synthesize_business_answer(
            question,
            tool_outputs,
            lang,
            used_agents=self.execution_trace,
            strict=True,
        )
        return {"answer": answer, "agents": self.execution_trace}

    def _route(self, question: str, page: Optional[str] = None, messages: Optional[list[dict]] = None) -> List[str]:
        low = question.lower()
        page_hint = (page or "").strip().lower()
        page_tools = {
            "dashboard": "knowledge_tool",
            "sales": "sales_tool",
            "inventory": "inventory_tool",
            "finance": "finance_tool",
            "hr": "hr_tool",
        }

        # If the user message is contextual/short ("выбрал KPI", "а потом что?"),
        # infer the domain from the recent conversation so we don't fall back to knowledge.
        inferred = self._infer_domain_from_history(messages)
        if inferred and self._looks_like_contextual_followup(low):
            return [f"{inferred}_tool"]

        # Use the page context as a strong hint for routing.
        if page_hint and page_hint in page_tools:
            page_tool = page_tools[page_hint]
        else:
            page_tool = None

        selected_tools = choose_tools_for_question(question, page=page_hint, messages=messages)
        if selected_tools:
            if page_tool and page_tool not in selected_tools:
                selected_tools.append(page_tool)
            return selected_tools

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
            if not any(tool in tools for tool in ["sales_tool", "inventory_tool", "finance_tool", "hr_tool"]):
                tools.append("knowledge_tool")

        if tools:
            return tools
        if page_tool:
            return [page_tool]
        return ["knowledge_tool"]

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _infer_domain_from_history(self, messages: Optional[list[dict]]) -> Optional[str]:
        if not messages:
            return None

        # Scan backwards for the most recent user message that clearly belongs to a domain.
        # We intentionally ignore assistant messages so the user's own intent drives routing.
        for msg in reversed(messages):
            if not isinstance(msg, dict):
                continue
            if msg.get("role") != "user":
                continue
            content = (msg.get("content") or "").strip()
            if not content:
                continue
            routed = self._route(content, messages=None)
            for tool in routed:
                if tool in ("sales_tool", "inventory_tool", "finance_tool", "hr_tool"):
                    return tool.replace("_tool", "")
        return None

    def _looks_like_contextual_followup(self, low_question: str) -> bool:
        # Keep this conservative: only short, conversational follow-ups that otherwise route nowhere.
        followup_markers = [
            "а потом",
            "и что теперь",
            "что дальше",
            "дальше что",
            "потом что",
            "теперь что",
            "выбрал",
            "выбрала",
            "kpi",
            "кпи",
            "ок",
            "хорошо",
        ]
        if len(low_question) <= 40 and any(token in low_question for token in followup_markers):
            return True
        return False
