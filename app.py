import html
import re
import time
import streamlit as st
from dotenv import load_dotenv

from src.task5_semantic_search import semantic_search
from src.task6_lexical_search import lexical_search
from src.task7_reranking import rerank_rrf
from src.task10_generation import (
    SAFE_REFUSAL,
    call_llm,
    format_context,
    reorder_for_llm,
)

load_dotenv(override=True)

st.set_page_config(
    page_title="RAG Chatbot — Pháp luật & Tin tức",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Áp dụng giao diện ChatGPT / Gemini Pro với CSS High-End Visual Design & Micro-animations
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0f172a;
    }

    /* Nền ứng dụng có dải gradient ánh sáng nhẹ ở trên */
    .stApp {
        background: radial-gradient(circle at 50% -80px, rgba(59, 130, 246, 0.08) 0%, rgba(248, 250, 252, 0.5) 45%, #f8fafc 100%);
    }

    /* Khung hội thoại rộng rãi thoáng đãng để thấy rõ Agent bên trái - User bên phải */
    .block-container {
        max-width: 1180px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 6rem !important;
    }

    /* Sidebar tinh giản với hiệu ứng kính mờ nhẹ */
    [data-testid="stSidebar"] {
        background-color: rgba(248, 250, 252, 0.85) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(226, 232, 240, 0.8);
    }

    /* ========================================================
       BỐ CỤC TUYỆT ĐỐI: USER BÊN PHẢI — AGENT BÊN TRÁI
       ======================================================== */

    /* 1. Tin nhắn của User (HOÀN TOÀN Ở GÓC PHẢI) */
    .user-bubble-container {
        display: flex;
        justify-content: flex-end;
        align-items: flex-start;
        gap: 12px;
        margin-top: 12px;
        margin-bottom: 24px;
        width: 100%;
    }
    .user-bubble {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
        color: #ffffff;
        border-radius: 20px 20px 4px 20px;
        padding: 14px 22px;
        max-width: 85%;
        box-shadow: 0 4px 18px rgba(37, 99, 235, 0.28), inset 0 1px 1px rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.15);
        font-size: 0.95rem;
        line-height: 1.55;
        word-break: break-word;
    }
    .user-avatar-badge {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563eb, #1e40af);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 1.1rem;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.35);
        flex-shrink: 0;
    }

    /* 2. Tin nhắn của Agent (HOÀN TOÀN Ở GÓC TRÁI) */
    .agent-bubble-container {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 14px;
        margin-top: 12px;
        margin-bottom: 24px;
        width: 100%;
    }
    .agent-avatar-badge {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0ea5e9, #6366f1);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: bold;
        box-shadow: 0 3px 12px rgba(99, 102, 241, 0.3);
        flex-shrink: 0;
    }
    .agent-bubble {
        background: #ffffff;
        border: 1px solid rgba(226, 232, 240, 0.9);
        border-radius: 4px 20px 20px 20px;
        padding: 20px 26px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
        color: #0f172a;
        width: 100%;
        word-break: break-word;
    }
    .agent-badge-tag {
        font-size: 0.72rem;
        font-weight: 700;
        color: #4f46e5;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 10px;
        display: inline-block;
    }
    .agent-content {
        font-size: 0.95rem;
        line-height: 1.7;
        color: #1e293b;
    }
    .agent-content p {
        margin-bottom: 0.75rem;
    }
    .agent-content ul, .agent-content ol {
        padding-left: 1.3rem;
        margin-bottom: 0.75rem;
    }

    /* Thinking indicator với 3 chấm chuyển động như đang chat */
    .thinking-status {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 7px 16px;
        font-size: 0.85rem;
        color: #334155;
        font-weight: 500;
        margin-top: 8px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .dots-wave {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        margin-left: 2px;
    }
    .dots-wave span {
        width: 4px;
        height: 4px;
        background-color: #3b82f6;
        border-radius: 50%;
        display: inline-block;
        animation: dotWave 1.2s infinite ease-in-out;
    }
    .dots-wave span:nth-child(1) { animation-delay: 0s; }
    .dots-wave span:nth-child(2) { animation-delay: 0.2s; }
    .dots-wave span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes dotWave {
        0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
        30% { transform: translateY(-4px); opacity: 1; }
    }

    /* Hero Greeting Header */
    .hero-container {
        text-align: center;
        margin-top: 36px;
        margin-bottom: 32px;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        color: #4f46e5;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 5px 14px;
        border-radius: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08);
    }

    @keyframes textStream {
        from { clip-path: inset(0 100% 0 0); }
        to { clip-path: inset(0 0 0 0); }
    }
    @keyframes subFade {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .hero-title {
        font-family: 'Outfit', sans-serif;
        font-size: 32px;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #0f172a 20%, #2563eb 65%, #7c3aed 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        display: inline-block;
        white-space: nowrap;
        animation: textStream 0.9s cubic-bezier(0.1, 0, 0.2, 1) forwards;
    }
    .hero-subtitle {
        font-size: 15px;
        color: #64748b;
        text-align: center;
        max-width: 580px;
        margin: 0 auto;
        line-height: 1.55;
        animation: subFade 0.7s ease 0.4s forwards;
    }

    /* Thẻ gợi ý câu hỏi mẫu kiểu Double-Bezel */
    .suggestion-btn button {
        text-align: left !important;
        padding: 16px 20px !important;
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        font-size: 0.88rem !important;
        line-height: 1.45 !important;
        color: #334155 !important;
        transition: all 0.25s cubic-bezier(0.32, 0.72, 0, 1) !important;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03) !important;
        height: 100% !important;
    }
    .suggestion-btn button:hover {
        border-color: #60a5fa !important;
        background: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12) !important;
    }
    .suggestion-btn button:active {
        transform: scale(0.99) !important;
    }

    /* Note cảnh báo khi độ tin cậy thấp */
    .confidence-note-warning {
        display: flex;
        align-items: center;
        gap: 8px;
        background: #fffbeb;
        border: 1px solid #fef3c7;
        border-left: 4px solid #f59e0b;
        color: #92400e;
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 0.84rem;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    /* Citation links dạng inline trong văn bản [1], [2] */
    .citation-link {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #eff6ff;
        color: #2563eb !important;
        border: 1px solid #bfdbfe;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 1px 6px;
        margin: 0 2px;
        text-decoration: none !important;
        vertical-align: baseline;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.06);
        transition: all 0.2s cubic-bezier(0.32, 0.72, 0, 1);
    }
    .citation-link:hover {
        background: #2563eb;
        color: #ffffff !important;
        border-color: #1d4ed8;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.35);
        transform: translateY(-1.5px);
    }

    /* Dòng chip nguồn tham khảo có link bấm trực tiếp */
    .source-pills-row {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
        margin-top: 14px;
        margin-bottom: 8px;
        padding-top: 12px;
        border-top: 1px dashed rgba(226, 232, 240, 0.9);
    }
    .source-pill-label {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .source-chip-btn {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #f8fafc;
        color: #334155 !important;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 500;
        text-decoration: none !important;
        transition: all 0.25s cubic-bezier(0.32, 0.72, 0, 1);
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    .source-chip-btn:hover {
        background: #ffffff;
        border-color: #3b82f6;
        color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
        transform: translateY(-1.5px);
    }

    /* Card chi tiết nguồn kiểm chứng */
    .grounding-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }

    /* Chat input bo tròn lớn chuẩn hiện đại */
    [data-testid="stChatInput"] {
        border-radius: 28px !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        box-shadow: 0 8px 25px rgba(15, 23, 42, 0.07) !important;
        transition: all 0.25s cubic-bezier(0.32, 0.72, 0, 1) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #3b82f6 !important;
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.18), 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.markdown("### ✦ Trợ lý RAG")
    if st.button("＋ Đoạn chat mới", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("##### Cấu hình")
    top_k = st.slider("Số nguồn tham chiếu (top-k)", min_value=3, max_value=10, value=5)


LEGAL_URL_MAP = {
    "89-vbhn": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/89-vbhn-vpqh.pdf",
    "55-vbhn": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/55-vbhn-vpqh.pdf",
    "72-vbhn": "https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/3/72-vbhn-vpqh.pdf",
}

CHAT_SYSTEM_PROMPT = """Bạn là trợ lý hỏi đáp thông tin chính xác, khách quan và đáng tin cậy dựa trên tài liệu được cung cấp.
Quy tắc trả lời:
1. Chỉ trả lời dựa vào thông tin có trong Context. Không suy diễn hoặc bịa đặt thông tin ngoài Context.
2. Mỗi khẳng định, số liệu hoặc sự kiện phải kèm theo trích dẫn nguồn tương ứng dạng [1], [2], [3] (tương ứng với số thứ tự [Document 1], [Document 2] trong Context).
3. Trình bày mạch lạc, rõ ràng, gãy gọn, ưu tiên bullet points nếu có nhiều ý.
4. Nếu Context không chứa đủ bằng chứng để trả lời hoặc thông tin chưa rõ ràng, hãy từ chối một cách lịch sự: "Tôi không thể xác minh thông tin này từ nguồn hiện có."
"""


def resolve_source_url(meta: dict) -> str | None:
    """Xác định URL công khai cho tài liệu (Web URL hoặc link văn bản pháp luật chính phủ)."""
    url = meta.get("url")
    if url and isinstance(url, str) and (url.startswith("http://") or url.startswith("https://")):
        return url
    source = str(meta.get("source", ""))
    for key, mapped_url in LEGAL_URL_MAP.items():
        if key in source:
            return mapped_url
    return url if url else None


def linkify_citations(text: str, chunks: list[dict]) -> str:
    """Chuyển đổi các trích dẫn [1], [2], [Document 1] trong câu trả lời thành link bấm trực tiếp."""
    if not chunks:
        return text

    # Đồng bộ hóa [Document X] hoặc [Tài liệu X] về [X]
    text = re.sub(r"\[(?:Document|Tài liệu)\s*(\d+)\]", r"[\1]", text, flags=re.IGNORECASE)

    def replace_bracket(match):
        inner = match.group(1).strip()
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        if parts and all(p.isdigit() for p in parts):
            rendered = []
            for p in parts:
                idx = int(p)
                if 1 <= idx <= len(chunks):
                    chunk = chunks[idx - 1]
                    meta = chunk.get("metadata", {})
                    url = resolve_source_url(meta)
                    title = html.escape(meta.get("title", f"Nguồn {idx}"))
                    if url:
                        rendered.append(
                            f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" class="citation-link" title="{title}">[{idx}]</a>'
                        )
                    else:
                        rendered.append(f'<span class="citation-link">[{idx}]</span>')
                else:
                    rendered.append(f"[{p}]")
            return "".join(rendered)
        return match.group(0)

    return re.sub(r"\[([0-9\s,]+)\]", replace_bracket, text)


def calculate_confidence(answer: str, chunks: list[dict], best_dense_score: float) -> tuple[bool, str, str, str]:
    """Tính toán độ tin cậy dựa trên score và nội dung câu trả lời.
    Trả về: (is_low_confidence, label, css_class, icon)
    """
    if not chunks or answer.strip() == SAFE_REFUSAL or best_dense_score < 0.35:
        return True, "Thấp", "confidence-low", "⚠️"

    if best_dense_score >= 0.70:
        return False, "Độ tin cậy cao", "confidence-high", "🟢"
    elif best_dense_score >= 0.50:
        return False, "Độ tin cậy tốt", "confidence-high", "🟢"
    else:
        return False, "Độ tin cậy tương đối", "confidence-medium", "🟡"


def render_sources_and_confidence(
    sources: list[dict],
    is_low_confidence: bool,
    confidence_label: str,
    confidence_class: str,
    confidence_icon: str,
    retrieval_source: str,
) -> None:
    """Hiển thị các chip nguồn tham khảo có link bấm được, ghi chú độ tin cậy và chi tiết kiểm chứng."""
    if not sources:
        if is_low_confidence:
            st.markdown(
                '<div class="confidence-note-warning">⚠️ <b>Lưu ý:</b> Câu trả lời có thể chưa chính xác do không tìm thấy tài liệu phù hợp.</div>',
                unsafe_allow_html=True,
            )
        return

    # 1. Hàng chip nguồn tham khảo click vào mở link ngay
    chips_html_list = []
    for idx, s in enumerate(sources, 1):
        meta = s.get("metadata", {})
        title = meta.get("title", f"Tài liệu {idx}")
        url = resolve_source_url(meta)
        short_title = title if len(title) <= 35 else title[:33] + "..."
        if url:
            chips_html_list.append(
                f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer" class="source-chip-btn" title="{html.escape(title)}">[{idx}] {html.escape(short_title)} ↗</a>'
            )
        else:
            chips_html_list.append(
                f'<span class="source-chip-btn">[{idx}] {html.escape(short_title)}</span>'
            )

    chips_html = "".join(chips_html_list)
    st.markdown(
        f"""
        <div class="source-pills-row">
            <span class="source-pill-label">📎 Nguồn tham khảo:</span>
            {chips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Xử lý độ tin cậy:
    # Nếu độ tin cậy thấp: Hiển thị note cảnh báo tinh tế
    # Nếu độ tin cậy bình thường/cao: Ẩn các badge kỹ thuật phức tạp theo yêu cầu người dùng
    if is_low_confidence:
        st.markdown(
            '<div class="confidence-note-warning">⚠️ <b>Lưu ý:</b> Câu trả lời có thể chưa chính xác do nguồn thông tin chưa đủ đối chiếu.</div>',
            unsafe_allow_html=True,
        )

    # 3. Chi tiết tài liệu mở rộng
    with st.expander(f"🔍 Xem chi tiết {len(sources)} tài liệu nguồn kiểm chứng", expanded=False):
        for idx, s in enumerate(sources, 1):
            meta = s.get("metadata", {})
            title = meta.get("title", f"Tài liệu {idx}")
            source_file = meta.get("source", "")
            url = resolve_source_url(meta)
            score = s.get("score", 0.0)
            method = s.get("retrieval_method", "hybrid").upper()
            content = s.get("content", "").strip()

            preview = content[:280] + ("..." if len(content) > 280 else "")
            link_html = f" &bull; <a href='{html.escape(url)}' target='_blank' style='color:#1a73e8; text-decoration:none;'>Mở văn bản gốc ↗</a>" if url else ""

            st.markdown(
                f"""
                <div class="grounding-box">
                    <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">
                        [{idx}] {html.escape(title)}
                    </div>
                    <div style="font-size: 0.78rem; color: #666; margin-bottom: 8px; font-family: 'JetBrains Mono', monospace;">
                        Tệp: {html.escape(source_file)} &bull; Điểm: {score:.4f} &bull; {method}{link_html}
                    </div>
                    <div style="font-size: 0.85rem; line-height: 1.5; color: #333; background: #f3f4f6; padding: 8px 12px; border-radius: 6px;">
                        {html.escape(preview)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# -------------------------------------------------------------
# PHẦN ĐẦU TRANG: Luôn hiển thị tiêu đề và 4 thẻ gợi ý câu hỏi mẫu
# -------------------------------------------------------------
selected_query = None

st.markdown(
    """
    <div class="hero-container">
        <div class="hero-badge">✦ RAG INTELLIGENCE ENGINE</div>
        <div><span class="hero-title">Tôi có thể giúp gì cho bạn hôm nay?</span></div>
        <div class="hero-subtitle">Tra cứu thông tin chính xác, kiểm chứng đối chiếu trực tiếp từ văn bản pháp luật và tin tức thời sự</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4 thẻ gợi ý hiển thị cố định ở đầu trang để người dùng kéo lên xem và bấm bất kỳ lúc nào
col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    if st.button("📘 **Mục tiêu giáo dục**\n\nQuy định về đào tạo con người theo Luật Giáo dục", key="btn_1", use_container_width=True):
        selected_query = "Mục tiêu của giáo dục theo Luật Giáo dục là gì?"
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    if st.button("🚗 **An toàn giao thông đường bộ**\n\nQuy định thiết bị kiểm tra tải trọng và giám sát", key="btn_2", use_container_width=True):
        selected_query = "Quy định về thiết bị kỹ thuật nghiệp vụ kiểm tra tải trọng và trật tự an toàn giao thông?"
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    if st.button("💰 **Dự toán ngân sách nhà nước**\n\nQuy định và thời hạn lập dự toán theo Luật Ngân sách", key="btn_3", use_container_width=True):
        selected_query = "Quy định về lập dự toán ngân sách nhà nước theo Luật Ngân sách?"
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
    if st.button("📰 **Chuyến công tác của Tổng Bí thư**\n\nHoạt động tại Mỹ và Canada mới nhất", key="btn_4", use_container_width=True):
        selected_query = "Chuyến công tác của Tổng Bí thư, Chủ tịch nước Tô Lâm tại Mỹ và Canada có hoạt động gì?"
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)


def render_user_message_ui(text: str):
    """Hiển thị tin nhắn người dùng hoàn toàn lệch sang GÓC PHẢI."""
    col_space, col_user = st.columns([0.25, 0.75])
    with col_user:
        st.markdown(
            f"""
            <div class="user-bubble-container">
                <div class="user-bubble">
                    {html.escape(text)}
                </div>
                <div class="user-avatar-badge">👤</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_assistant_message_ui(content: str, sources: list[dict], is_low_conf: bool):
    """Hiển thị tin nhắn Agent hoàn toàn lệch sang GÓC TRÁI."""
    col_agent, col_space = st.columns([0.88, 0.12])
    with col_agent:
        st.markdown(
            f"""
            <div class="agent-bubble-container">
                <div class="agent-avatar-badge">✦</div>
                <div class="agent-bubble">
                    <div class="agent-badge-tag">✦ TRỢ LÝ RAG</div>
                    <div class="agent-content">{content}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if sources:
            render_sources_and_confidence(
                sources=sources,
                is_low_confidence=is_low_conf,
                confidence_label="",
                confidence_class="",
                confidence_icon="",
                retrieval_source="",
            )


# Hiển thị lịch sử chat: Agent bên TRÁI — User bên PHẢI
for message in st.session_state.messages:
    if message["role"] == "user":
        render_user_message_ui(message["content"])
    elif message["role"] == "assistant":
        render_assistant_message_ui(
            content=message["content"],
            sources=message.get("sources", []),
            is_low_conf=message.get("is_low_confidence", False),
        )


# Khung chat input luôn sẵn sàng
user_typed = st.chat_input("Hỏi bất kỳ điều gì về quy định, pháp luật hoặc tin tức...")
prompt = selected_query or user_typed

if prompt:
    # 1. Hiển thị câu hỏi của User hoàn toàn ở góc PHẢI
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_user_message_ui(prompt)

    # 2. Xử lý câu trả lời của Agent hoàn toàn ở góc TRÁI
    col_agent, col_space = st.columns([0.88, 0.12])
    with col_agent:
        thinking_box = st.empty()

        # Trạng thái 1: Đang tìm kiếm tài liệu
        thinking_box.markdown(
            """
            <div class="thinking-status">
                <span>✦ Đang tìm kiếm tài liệu</span>
                <span class="dots-wave"><span></span><span></span><span></span></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        dense_results = semantic_search(prompt, top_k=top_k * 2)
        best_dense = dense_results[0]["score"] if dense_results else 0.0
        sparse_results = lexical_search(prompt, top_k=top_k * 2)

        # Trạng thái 2: Đang đối chiếu thông tin
        thinking_box.markdown(
            """
            <div class="thinking-status">
                <span>✦ Đang đối chiếu thông tin</span>
                <span class="dots-wave"><span></span><span></span><span></span></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fused_chunks = rerank_rrf([dense_results, sparse_results], top_k=top_k)
        reordered = reorder_for_llm(fused_chunks)
        context = format_context(reordered)
        user_msg = f"Dưới đây là tài liệu liên quan:\n\n{context}\n\nCâu hỏi: {prompt}\n\nHãy trả lời câu hỏi dựa trên tài liệu trên:"

        # Trạng thái 3: Đang tổng hợp câu trả lời
        thinking_box.markdown(
            """
            <div class="thinking-status">
                <span>✦ Đang tổng hợp câu trả lời</span>
                <span class="dots-wave"><span></span><span></span><span></span></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            answer = call_llm(CHAT_SYSTEM_PROMPT, user_msg)
            if not answer or not answer.strip():
                answer = SAFE_REFUSAL
        except Exception as e:
            print(f"Error in call_llm: {e}")
            answer = SAFE_REFUSAL

        # Xóa khung trạng thái đang làm để chuyển sang hiển thị câu trả lời mượt mà
        thinking_box.empty()

        # Hiệu ứng streaming câu trả lời theo từ trong bubble bên TRÁI
        answer_placeholder = st.empty()
        streamed_text = ""
        for word in answer.split(" "):
            streamed_text += word + " "
            answer_placeholder.markdown(
                f"""
                <div class="agent-bubble-container">
                    <div class="agent-avatar-badge">✦</div>
                    <div class="agent-bubble">
                        <div class="agent-badge-tag">✦ TRỢ LÝ RAG</div>
                        <div class="agent-content">{html.escape(streamed_text)}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            time.sleep(0.01)

        # Gắn link bấm trực tiếp [1], [2], [3] mở nguồn tham khảo
        formatted_answer = linkify_citations(answer, fused_chunks)
        answer_placeholder.markdown(
            f"""
            <div class="agent-bubble-container">
                <div class="agent-avatar-badge">✦</div>
                <div class="agent-bubble">
                    <div class="agent-badge-tag">✦ TRỢ LÝ RAG</div>
                    <div class="agent-content">{formatted_answer}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Tính toán độ tin cậy và hiển thị nguồn
        is_low_conf, _, _, _ = calculate_confidence(answer, fused_chunks, best_dense)
        retrieval_source = fused_chunks[0]["retrieval_method"] if fused_chunks else "none"

        render_sources_and_confidence(
            sources=fused_chunks,
            is_low_confidence=is_low_conf,
            confidence_label="",
            confidence_class="",
            confidence_icon="",
            retrieval_source=retrieval_source,
        )

    # 3. Lưu vào session state
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": formatted_answer,
            "sources": fused_chunks,
            "is_low_confidence": is_low_conf,
            "retrieval_source": retrieval_source,
        }
    )
