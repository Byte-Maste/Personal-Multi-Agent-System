from langchain_groq import ChatGroq
from app.config import settings

_llm: ChatGroq | None = None


def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=4096,
        )
    return _llm


async def llm_invoke(prompt: str, system_prompt: str | None = None) -> str:
    llm = get_llm()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    response = await llm.ainvoke(messages)
    return str(response.content)


async def llm_invoke_structured(prompt: str, system_prompt: str, output_schema: dict) -> dict:
    llm = get_llm().with_structured_output(schema=output_schema)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    response = await llm.ainvoke(messages)
    return response
