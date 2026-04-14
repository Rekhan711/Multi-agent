from typing import List

try:
    from llama_index import Document, GPTSimpleVectorIndex
except ImportError:
    try:
        from llama_index.core import Document, VectorStoreIndex
    except ImportError:
        Document = None
        GPTSimpleVectorIndex = None
        VectorStoreIndex = None
    else:
        GPTSimpleVectorIndex = VectorStoreIndex


class BusinessKnowledgeIndex:
    """Lightweight LlamaIndex-based knowledge layer for business context."""

    def __init__(self):
        self.fallback_docs = [
            "Sales data includes revenue, product, region, quantities and deal status.",
            "Inventory data tracks stock levels, categories, valuation, and low-stock alerts.",
            "Finance data contains revenue, expense, profit, cash flow and budget performance.",
            "HR analytics includes headcount, turnover, hiring trends and department distribution.",
        ]
        self.index = self._build_index()

    def _build_index(self):
        if GPTSimpleVectorIndex is None or Document is None:
            return None

        documents = [Document(text=text) for text in self.fallback_docs]
        try:
            return GPTSimpleVectorIndex(documents)
        except Exception:
            return None

    def query(self, prompt: str) -> str:
        if not self.index:
            prompt_lower = prompt.lower()
            if any(token in prompt_lower for token in ["sale", "revenue", "deal", "product", "region"]):
                return self.fallback_docs[0]
            if any(token in prompt_lower for token in ["inventory", "stock", "warehouse", "supply", "category"]):
                return self.fallback_docs[1]
            if any(token in prompt_lower for token in ["finance", "profit", "expense", "cash", "budget"]):
                return self.fallback_docs[2]
            if any(token in prompt_lower for token in ["hr", "employee", "headcount", "turnover", "hiring"]):
                return self.fallback_docs[3]
            return "Business knowledge is available for sales, inventory, finance, and HR topics."
        response = self.index.query(prompt)
        return str(response)
