"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os
from dotenv import load_dotenv

from src.contracts import validate_generation_result
from .task9_retrieval_pipeline import retrieve

load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "")

SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

SYSTEM_PROMPT = """Bạn là trợ lý AI chuyên nghiệp trả lời các câu hỏi về pháp luật và tin tức dựa trên tài liệu được cung cấp.
Nguyên tắc bắt buộc:
1. Trả lời chỉ từ context được cung cấp dưới đây.
2. Mỗi khẳng định phải có citation rõ ràng trích dẫn nguồn (ví dụ: [Document 1], [Document 2]).
3. Nếu context không có thông tin hoặc không đủ bằng chứng để trả lời chính xác, hãy trả lời đúng nguyên văn: "Tôi không thể xác minh thông tin này từ nguồn hiện có."
4. Không suy diễn hoặc tự ý bổ sung kiến thức bên ngoài context."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context (giảm lost-in-the-middle)."""
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label rõ ràng cho từng chunk."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        title = metadata.get("title", "Unknown Title")
        source = metadata.get("source", "Unknown Source")
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source}]\n{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình trong .env."""
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()

    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")
        model = os.getenv("LLM_MODEL") or LLM_MODEL or "gpt-4o-mini"
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        return response.choices[0].message.content or ""

    elif provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        model = os.getenv("LLM_MODEL") or LLM_MODEL or "gemini-2.0-flash"
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=user_message,
            config={
                "system_instruction": system_prompt,
                "temperature": TEMPERATURE,
                "top_p": TOP_P,
            },
        )
        return response.text or ""

    elif provider == "anthropic":
        import anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
        model = os.getenv("LLM_MODEL") or LLM_MODEL or "claude-3-5-haiku-20241022"
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1024,
            temperature=TEMPERATURE,
        )
        return response.content[0].text

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult có citation và nguồn tham chiếu."""
    if not query.strip():
        return {
            "answer": SAFE_REFUSAL,
            "sources": [],
            "retrieval_source": "none",
        }

    try:
        chunks = retrieve(query, top_k=top_k)
    except Exception:
        chunks = []

    if not chunks:
        result = {
            "answer": SAFE_REFUSAL,
            "sources": [],
            "retrieval_source": "none",
        }
        validate_generation_result(result)
        return result

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    user_message = (
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Hãy trả lời câu hỏi bằng tiếng Việt dựa vào Context và trích dẫn [Document X] tương ứng."
    )

    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        if not answer or not answer.strip():
            answer = SAFE_REFUSAL
    except Exception:
        answer = SAFE_REFUSAL

    retrieval_source = chunks[0]["retrieval_method"]
    if retrieval_source not in ("hybrid", "pageindex", "none"):
        retrieval_source = "hybrid"

    result = {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }
    validate_generation_result(result)
    return result


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    sample_q = "Quy định về bảo đảm an toàn giao thông đường bộ gồm những gì?"
    print(f"Testing generation for: '{sample_q}'")
    gen_res = generate_with_citation(sample_q, top_k=3)
    print("Answer:\n", gen_res["answer"])
    print("\nRetrieval Source:", gen_res["retrieval_source"])
    print(f"Sources count: {len(gen_res['sources'])}")
