import re
from typing import List

from langchain.agents import AgentExecutor, AgentType, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI


class ReActOrchestrator:
    def __init__(self, llm: ChatOpenAI, tool_functions: List[Tool]):
        self.llm = llm
        self.tools = tool_functions
        self.execution_trace = []
        self.agent_executor = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
        )

    def run(self, prompt: str) -> str:
        self.execution_trace = []
        response = self.agent_executor.run(prompt)
        return response

    @staticmethod
    def select_tools_by_keyword(question: str, tool_names: List[str]) -> List[str]:
        lower = question.lower()
        selected = []
        mapping = {
            "sales": ["sales", "revenue", "deals", "region", "product"],
            "inventory": ["inventory", "stock", "warehouse", "supply"],
            "finance": ["finance", "profit", "loss", "expense", "cash"],
            "hr": ["hr", "employee", "headcount", "turnover", "hiring"],
        }
        for tool_name, keywords in mapping.items():
            if any(term in lower for term in keywords):
                if tool_name in tool_names:
                    selected.append(tool_name)
        return selected

    @staticmethod
    def should_use_knowledge_tool(question: str) -> bool:
        lower = question.lower()
        return any(word in lower for word in ["business", "strategy", "market", "trends", "policy"])
