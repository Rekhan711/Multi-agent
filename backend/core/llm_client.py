import os
from typing import Dict, Optional

from openai import OpenAI


def detect_language(text: str) -> str:
    low = text.lower()
    uz_keywords = [
        "savdo",
        "daromad",
        "ombor",
        "moliya",
        "xodim",
        "foyda",
        "xarajat",
        "bozor",
        "qanday",
    ]
    if any(token in low for token in uz_keywords):
        return "uz"

    if any("\u0400" <= ch <= "\u04FF" for ch in low):
        return "ru"

    return "en"


def is_smalltalk(text: str) -> bool:
    low = text.strip().lower()
    tokens = {
        "hi",
        "hello",
        "hey",
        "alo",
        "алло",
        "ало",
        "привет",
        "здравствуйте",
        "salom",
        "assalomu alaykum",
    }
    return low in tokens


def smalltalk_response(lang: str) -> str:
    if lang == "ru":
        return "На связи. Задайте бизнес-вопрос по продажам, финансам, складу или HR, и я дам конкретный ответ по данным."
    if lang == "uz":
        return "Aloqadaman. Savdo, moliya, ombor yoki HR bo'yicha aniq savol bering, men ma'lumotlarga tayangan javob beraman."
    return "I'm here. Ask a specific business question about sales, finance, inventory, or HR and I'll answer from available data."


def get_openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def _normalize_tool_output(tool_name: str, text: str, lang: str) -> str:
    value = (text or "").strip()
    if not value:
        return ""

    if "Business knowledge is available for sales, inventory, finance, and HR topics." in value:
        if lang == "ru":
            return "Общие справочные знания доступны, но конкретных метрик по запросу пока нет."
        if lang == "uz":
            return "Umumiy bilimlar mavjud, lekin bu savol uchun aniq metrikalar hozircha topilmadi."
        return "General business knowledge is available, but no specific metric was found for this question."

    if lang == "ru":
        label_map = {
            "sales_tool": "Продажи",
            "finance_tool": "Финансы",
            "inventory_tool": "Склад",
            "hr_tool": "HR",
            "knowledge_tool": "Знания",
        }
    elif lang == "uz":
        label_map = {
            "sales_tool": "Savdo",
            "finance_tool": "Moliya",
            "inventory_tool": "Ombor",
            "hr_tool": "HR",
            "knowledge_tool": "Bilim bazasi",
        }
    else:
        label_map = {
            "sales_tool": "Sales",
            "finance_tool": "Finance",
            "inventory_tool": "Inventory",
            "hr_tool": "HR",
            "knowledge_tool": "Knowledge",
        }

    label = label_map.get(tool_name, tool_name)
    return f"{label}: {value}"


def _fallback_summary(question: str, tool_outputs: Dict[str, str], lang: str) -> str:
    if is_smalltalk(question):
        return smalltalk_response(lang)

    normalized = []
    for name, text in tool_outputs.items():
        cleaned = _normalize_tool_output(name, text, lang)
        if cleaned:
            normalized.append(cleaned)

    q = question.lower()
    asks_people_impact = any(
        token in q
        for token in ["сотруд", "персон", "employee", "xodim", "штат", "headcount", "hr"]
    ) and any(token in q for token in ["продаж", "sales", "savdo", "рост", "oshir", "increase"])

    if not normalized:
        if lang == "ru":
            return "Не вижу достаточных данных по этому вопросу. Уточните метрику или период (например: «продажи по регионам за месяц»)."
        if lang == "uz":
            return "Bu savol uchun yetarli ma'lumot topilmadi. Iltimos, metrika yoki davrni aniqlashtiring."
        return "I don't have enough data for this question yet. Please specify metric and period."

    if lang == "ru":
        parts = ["Короткий ответ по данным:"]
        parts.extend([f"- {line}" for line in normalized])
        if asks_people_impact:
            parts.append(
                "- Влияние на сотрудников: рост продаж обычно увеличивает нагрузку на Sales, Customer Success и Operations; стоит заранее отслеживать headcount и текучесть."
            )
        parts.append("Следующий шаг: выберите 1 KPI и целевой период, чтобы оценить эффект решений.")
        return "\n".join(parts)

    if lang == "uz":
        parts = ["Ma'lumotlarga tayangan qisqa javob:"]
        parts.extend([f"- {line}" for line in normalized])
        if asks_people_impact:
            parts.append(
                "- Xodimlarga ta'siri: savdo o'ssa Sales, Customer Success va Operations jamoalarida yuklama ortadi; headcount va turnover ko'rsatkichlarini oldindan kuzatish kerak."
            )
        parts.append("Keyingi qadam: bitta asosiy KPI va davrni tanlab, ta'sirni o'lchang.")
        return "\n".join(parts)

    parts = ["Data-based short answer:"]
    parts.extend([f"- {line}" for line in normalized])
    if asks_people_impact:
        parts.append(
            "- People impact: sales growth usually increases workload in Sales, Customer Success, and Operations; track headcount and attrition early."
        )
    parts.append("Next step: pick one KPI and a period to measure impact.")
    return "\n".join(parts)


def synthesize_business_answer(question: str, tool_outputs: Dict[str, str], lang: str) -> str:
    if is_smalltalk(question):
        return smalltalk_response(lang)

    client = get_openai_client()
    if client is None:
        return _fallback_summary(question, tool_outputs, lang)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    lang_instruction = {"ru": "Russian", "uz": "Uzbek", "en": "English"}.get(lang, "English")
    tools_block = "\n".join([f"{name}: {value}" for name, value in tool_outputs.items() if value])

    prompt = (
        f"User question:\n{question}\n\n"
        f"Tool outputs:\n{tools_block or 'No tool outputs'}\n\n"
        "Rules:\n"
        "- Use only facts from tool outputs.\n"
        "- If data is insufficient, explicitly say so.\n"
        "- Do not invent metrics, dates, or causes.\n"
        "- Keep answer concise and practical.\n"
        f"Respond only in {lang_instruction}."
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": "You are a BI analyst. Be accurate, grounded, and never hallucinate.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        answer = (response.output_text or "").strip()
        if answer:
            return answer
    except Exception:
        pass

    return _fallback_summary(question, tool_outputs, lang)
