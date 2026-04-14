import os
import re
from typing import Dict, Optional, List

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


_TOOL_ALIASES = {
    "sales_tool": "sales_tool",
    "sales": "sales_tool",
    "revenue": "sales_tool",
    "inventory_tool": "inventory_tool",
    "inventory": "inventory_tool",
    "stock": "inventory_tool",
    "finance_tool": "finance_tool",
    "finance": "finance_tool",
    "profit": "finance_tool",
    "expense": "finance_tool",
    "cash": "finance_tool",
    "hr_tool": "hr_tool",
    "hr": "hr_tool",
    "employee": "hr_tool",
    "employees": "hr_tool",
    "knowledge_tool": "knowledge_tool",
    "knowledge": "knowledge_tool",
    "business": "knowledge_tool",
    "market": "knowledge_tool",
}


def _parse_tool_selection(output: str) -> List[str]:
    if not output:
        return []

    chosen: List[str] = []
    tokens = re.split(r"[\n,;]+", output)
    for token in tokens:
        token = token.strip().lower()
        if not token:
            continue

        if token in _TOOL_ALIASES:
            tool_name = _TOOL_ALIASES[token]
            if tool_name not in chosen:
                chosen.append(tool_name)
            continue

        for alias, tool_name in _TOOL_ALIASES.items():
            if alias in token and tool_name not in chosen:
                chosen.append(tool_name)
    return chosen


def choose_tools_for_question(question: str, page: Optional[str] = None, messages: Optional[list[dict]] = None) -> List[str]:
    client = get_openai_client()
    if client is None:
        return []

    page_hint = page or "No page hint"
    history_text = ""
    if messages:
        history = [msg.get("content", "") for msg in messages if isinstance(msg, dict) and msg.get("role") == "user"]
        if history:
            history_text = "\nConversation history:\n" + "\n".join(history[-3:])
    prompt = (
        "You are a strict business routing assistant. Choose the most relevant tools for the user's question. "
        "Available tools: sales_tool, inventory_tool, finance_tool, hr_tool, knowledge_tool. "
        "Use page context if it is helpful. Return only a comma-separated list of tool names, no explanation. "
        f"Current page: {page_hint}.\n"
        f"User question: {question}\n"
        f"{history_text}\n"
        "If the question mentions multiple domains, include multiple tool names. "
        "If the question is general and not tied to a specific domain, include knowledge_tool. "
        "If you are unsure, respond with knowledge_tool."
    )

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=[
                {"role": "system", "content": "You are a tool router for a business intelligence system."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        tool_output = getattr(response, "output_text", None)
        if tool_output is None:
            tool_output = "".join(
                str(item) for item in getattr(response, "output", [])
            )
        return _parse_tool_selection(str(tool_output))
    except Exception:
        return []


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

    label_map = {
        "sales_tool": {"ru": "Продажи", "uz": "Savdo", "en": "Sales"},
        "finance_tool": {"ru": "Финансы", "uz": "Moliya", "en": "Finance"},
        "inventory_tool": {"ru": "Склад", "uz": "Ombor", "en": "Inventory"},
        "hr_tool": {"ru": "HR", "uz": "HR", "en": "HR"},
        "knowledge_tool": {"ru": "Знания", "uz": "Bilim bazasi", "en": "Knowledge"},
    }
    label = label_map.get(tool_name, {"ru": tool_name, "uz": tool_name, "en": tool_name}).get(lang, tool_name)
    return f"{label}: {value}"


SECTION_TEMPLATES = {
    "ru": {
        "short": "Короткий ответ",
        "facts": "Что подтверждено данными",
        "unknowns": "Что пока не видно в данных",
        "actions": "Следующие шаги",
        "no_data": "Сейчас данных недостаточно для точного ответа. Уточните метрику и период.",
    },
    "uz": {
        "short": "Qisqa javob",
        "facts": "Ma'lumotlar bilan tasdiqlangan",
        "unknowns": "Ma'lumotlarda ko'rinmayotgani",
        "actions": "Keyingi qadamlar",
        "no_data": "Hozircha aniq javob uchun yetarli ma'lumot yo'q. Iltimos, metrika va davrni aniqlang.",
    },
    "en": {
        "short": "Short answer",
        "facts": "What is supported by data",
        "unknowns": "What is not visible in data",
        "actions": "Next steps",
        "no_data": "There is not enough data to answer precisely. Please clarify metric and period.",
    },
}


def _local_label(section: str, lang: str) -> str:
    return SECTION_TEMPLATES.get(lang, SECTION_TEMPLATES["en"]).get(section, section)


def _build_structured_facts(tool_outputs: Dict[str, str], lang: str) -> list[str]:
    lines: list[str] = []
    for tool_name, text in tool_outputs.items():
        if not text or not text.strip():
            continue
        normalized = _normalize_tool_output(tool_name, text, lang)
        if normalized:
            lines.append(normalized)
    return lines


def _build_recommendations(used_agents: list[str] | None, lang: str) -> list[str]:
    if not used_agents:
        return [
            {
                "ru": "Уточните область (sales, inventory, finance, HR) и период для точного ответа.",
                "uz": "Aniq javob uchun soha (savdo, ombor, moliya, HR) va davrni aniqlang.",
                "en": "Clarify the area (sales, inventory, finance, HR) and period for a precise answer.",
            }[lang]
        ]

    recs: list[str] = []
    if "sales_tool" in used_agents:
        recs.append(
            {
                "ru": "Посмотрите основную метрику продаж и сравните периоды.",
                "uz": "Asosiy savdo metrikasini ko'rib chiqing va davrlarni solishtiring.",
                "en": "Review the main sales metric and compare periods.",
            }[lang]
        )
    if "inventory_tool" in used_agents:
        recs.append(
            {
                "ru": "Выберите KPI для склада: (1) единицы на складе (сумма остатков), (2) SKU/позиций, (3) низкий остаток, (4) стоимость (общая/по категориям).",
                "uz": "Ombor KPI ni tanlang: (1) birliklar (qoldiq summasi), (2) SKU/pozitsiyalar, (3) past zaxira, (4) qiymat (umumiy/kategoriya bo'yicha).",
                "en": "Pick an inventory KPI: (1) total units (sum of quantities), (2) SKUs/positions, (3) low-stock count, (4) value (total/by category).",
            }[lang]
        )
    if "finance_tool" in used_agents:
        recs.append(
            {
                "ru": "Сравните прибыль и расходы за последние периоды, чтобы увидеть тренд.",
                "uz": "So'nggi davrlarda foyda va xarajatlarni solishtiring, trendni aniqlang.",
                "en": "Compare profit and expenses across recent periods to identify the trend.",
            }[lang]
        )
    if "hr_tool" in used_agents:
        recs.append(
            {
                "ru": "Отслеживайте headcount и текучесть, если вопрос связан с персоналом.",
                "uz": "Savol xodimlar bilan bog'liq bo'lsa, headcount va turnover ni kuzating.",
                "en": "Track headcount and turnover when the question involves personnel.",
            }[lang]
        )
    if not recs:
        recs.append(
            {
                "ru": "Назовите 1 KPI, который хотите увидеть, и (если применимо) период — я отвечу строго по данным.",
                "uz": "Ko'rmoqchi bo'lgan 1 KPI ni va (kerak bo'lsa) davrni ayting — men faqat ma'lumotlarga tayanib javob beraman.",
                "en": "Name 1 KPI you want and (if applicable) a period — I’ll answer strictly from the data.",
            }[lang]
        )
    return recs


def _compose_structured_answer(
    question: str,
    tool_outputs: Dict[str, str],
    used_agents: list[str] | None,
    lang: str,
) -> str:
    facts = _build_structured_facts(tool_outputs, lang)
    has_data = bool(facts)
    unknowns: list[str] = []
    if not has_data:
        unknowns = [SECTION_TEMPLATES[lang]["no_data"]]
    else:
        unknowns = [
            {
                "ru": "Не видно точного периода, если он не указан в запросе.",
                "uz": "Agar davr ko'rsatilmagan bo'lsa, aniq davr ko'rinmaydi.",
                "en": "The exact period is not visible if it is not specified in the request.",
            }[lang]
        ]
    actions = _build_recommendations(used_agents, lang)

    short_answer = facts[0] if facts else SECTION_TEMPLATES[lang]["no_data"]
    return "\n\n".join(
        [
            f"{_local_label('short', lang)}:\n- {short_answer}",
            f"{_local_label('facts', lang)}:\n" + ("\n".join(f"- {line}" for line in facts) if facts else "-"),
            f"{_local_label('unknowns', lang)}:\n" + ("\n".join(f"- {line}" for line in unknowns) if unknowns else "-"),
            f"{_local_label('actions', lang)}:\n" + ("\n".join(f"- {line}" for line in actions) if actions else "-"),
        ]
    )


def synthesize_business_answer(
    question: str,
    tool_outputs: Dict[str, str],
    lang: str,
    used_agents: list[str] | None = None,
    strict: bool = True,
) -> str:
    if is_smalltalk(question):
        return smalltalk_response(lang)

    has_tool_data = any(text and text.strip() for text in tool_outputs.values())
    if not has_tool_data:
        return _compose_structured_answer(question, tool_outputs, used_agents, lang)

    client = get_openai_client()
    if client is None:
        return _compose_structured_answer(question, tool_outputs, used_agents, lang)

    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    lang_instruction = {"ru": "Russian", "uz": "Uzbek", "en": "English"}.get(lang, "English")
    tools_block = "\n".join([f"{name}: {value.strip()}" for name, value in tool_outputs.items() if value and value.strip()])
    agents_block = ", ".join(used_agents or []) or "none"

    prompt = (
        f"User question:\n{question}\n\n"
        f"Used agents:\n{agents_block}\n\n"
        f"Tool outputs:\n{tools_block}\n\n"
        "Instructions:\n"
        "- Answer only from the tool outputs.\n"
        "- Use only the facts that are present.\n"
        "- Do not invent metrics, dates, or causes.\n"
        "- Do not repeat raw tool text verbatim.\n"
        "- If the data is incomplete, say so explicitly.\n"
        "- Keep the answer concise and structured.\n"
        "- Output exactly four sections with headings.\n"
        f"- Respond in {lang_instruction}.\n"
        f"{_local_label('short', lang)}:\n"
        f"{_local_label('facts', lang)}:\n"
        f"{_local_label('unknowns', lang)}:\n"
        f"{_local_label('actions', lang)}:\n"
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": "You are a strict BI assistant. Base the answer only on provided tool outputs."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        answer = (response.output_text or "").strip()
        if answer:
            return answer
    except Exception:
        pass

    return _compose_structured_answer(question, tool_outputs, used_agents, lang)
