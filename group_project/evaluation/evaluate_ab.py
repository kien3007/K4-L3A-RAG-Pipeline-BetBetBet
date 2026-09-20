"""
Evaluation Script for A/B Comparison:
Config A (Dense-only) vs Config B (Hybrid + RRF)
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.task9_retrieval_pipeline import retrieve
from src.task10_generation import (
    SAFE_REFUSAL,
    SYSTEM_PROMPT,
    call_llm,
    format_context,
    reorder_for_llm,
)


def compute_context_recall(expected_context: str, retrieved_chunks: list[dict]) -> float:
    """Tỷ lệ các từ khóa/cụm từ quan trọng của expected_context xuất hiện trong retrieved chunks."""
    if not retrieved_chunks or not expected_context.strip():
        return 0.0

    retrieved_text = " ".join([c["content"].lower() for c in retrieved_chunks])
    # Tách các từ quan trọng (bỏ các từ nối ngắn)
    words = [w.strip(".,;:\"'()[]") for w in expected_context.lower().split() if len(w) > 2]
    if not words:
        return 0.0
    matched = sum(1 for w in words if w in retrieved_text)
    return min(1.0, matched / len(words))


def compute_context_precision(question: str, retrieved_chunks: list[dict]) -> float:
    """Độ tập trung và thứ hạng của các chunk liên quan đến câu hỏi."""
    if not retrieved_chunks:
        return 0.0

    q_words = set(w.strip(".,;:\"'()[]") for w in question.lower().split() if len(w) > 2)
    if not q_words:
        return 0.5

    precisions = []
    relevant_count = 0
    for rank, chunk in enumerate(retrieved_chunks, 1):
        chunk_words = set(chunk["content"].lower().split())
        overlap = len(q_words & chunk_words)
        is_relevant = (overlap / len(q_words)) >= 0.25
        if is_relevant:
            relevant_count += 1
            precisions.append(relevant_count / rank)

    if not precisions:
        return 0.2
    return min(1.0, sum(precisions) / len(precisions))


def compute_faithfulness(answer: str, retrieved_chunks: list[dict]) -> float:
    """Độ trung thực của câu trả lời so với context (không bịa thông tin)."""
    if answer.strip() == SAFE_REFUSAL:
        return 0.85
    if not retrieved_chunks:
        return 0.0

    retrieved_text = " ".join([c["content"].lower() for c in retrieved_chunks])
    ans_words = [w.strip(".,;:\"'()[]") for w in answer.lower().split() if len(w) > 2]
    if not ans_words:
        return 0.5
    matched = sum(1 for w in ans_words if w in retrieved_text)
    return min(1.0, max(0.4, (matched / len(ans_words)) * 1.15))


def compute_answer_relevance(question: str, answer: str) -> float:
    """Độ phù hợp của câu trả lời với câu hỏi."""
    if answer.strip() == SAFE_REFUSAL:
        return 0.4
    q_words = set(w.strip(".,;:\"'()[]") for w in question.lower().split() if len(w) > 2)
    ans_words = set(w.strip(".,;:\"'()[]") for w in answer.lower().split() if len(w) > 2)
    if not q_words or not ans_words:
        return 0.5
    overlap = len(q_words & ans_words)
    ratio = overlap / len(q_words)
    return min(1.0, max(0.5, 0.4 + ratio * 0.7))


def evaluate_config(cases: list[dict], use_reranking: bool) -> tuple[dict, list[dict]]:
    """Chạy đánh giá toàn bộ cases theo một config."""
    config_name = "Config B (Hybrid + RRF)" if use_reranking else "Config A (Dense-only)"
    print(f"\n--- Đang đánh giá {config_name} ---")

    case_scores = []
    total_metrics = {
        "faithfulness": 0.0,
        "answer_relevance": 0.0,
        "context_recall": 0.0,
        "context_precision": 0.0,
    }

    start_time = time.time()
    for idx, case in enumerate(cases, 1):
        q = case["question"]
        expected_ctx = case["expected_context"]

        chunks = retrieve(q, top_k=5, use_reranking=use_reranking)

        if chunks:
            reordered = reorder_for_llm(chunks)
            ctx = format_context(reordered)
            user_msg = (
                f"Context:\n{ctx}\n\n"
                f"Question: {q}\n\n"
                f"Hãy trả lời câu hỏi dựa vào Context và trích dẫn nguồn."
            )
            try:
                answer = call_llm(SYSTEM_PROMPT, user_msg)
            except Exception:
                answer = SAFE_REFUSAL
        else:
            answer = SAFE_REFUSAL

        f_score = compute_faithfulness(answer, chunks)
        r_score = compute_answer_relevance(q, answer)
        rec_score = compute_context_recall(expected_ctx, chunks)
        prec_score = compute_context_precision(q, chunks)

        total_metrics["faithfulness"] += f_score
        total_metrics["answer_relevance"] += r_score
        total_metrics["context_recall"] += rec_score
        total_metrics["context_precision"] += prec_score

        avg = (f_score + r_score + rec_score + prec_score) / 4.0
        case_scores.append({
            "index": idx,
            "question": q,
            "config": "Config B" if use_reranking else "Config A",
            "faithfulness": round(f_score, 4),
            "relevance": round(r_score, 4),
            "recall": round(rec_score, 4),
            "precision": round(prec_score, 4),
            "average": round(avg, 4),
            "answer": answer,
        })
        print(f"[{idx}/{len(cases)}] Avg: {avg:.4f} | Rec: {rec_score:.3f} | Prec: {prec_score:.3f}")

    elapsed = time.time() - start_time
    n = len(cases)
    avg_metrics = {k: round(v / n, 4) for k, v in total_metrics.items()}
    avg_metrics["average"] = round(sum(avg_metrics.values()) / 4.0, 4)
    avg_metrics["latency_seconds"] = round(elapsed, 2)
    return avg_metrics, case_scores


def main():
    dataset_path = Path(__file__).parent / "golden_dataset.json"
    cases = json.loads(dataset_path.read_text(encoding="utf-8"))
    print(f"Loaded {len(cases)} golden cases from {dataset_path.name}")

    metrics_a, details_a = evaluate_config(cases, use_reranking=False)
    metrics_b, details_b = evaluate_config(cases, use_reranking=True)

    print("\n" + "=" * 60)
    print("KẾT QUẢ ĐÁNH GIÁ TỔNG HỢP A/B")
    print("=" * 60)
    print(f"{'Metric':<20} | {'Config A (Dense)':<18} | {'Config B (Hybrid+RRF)':<22} | {'Delta (B-A)':<10}")
    print("-" * 75)
    for m in ["faithfulness", "answer_relevance", "context_recall", "context_precision", "average"]:
        score_a = metrics_a[m]
        score_b = metrics_b[m]
        delta = round(score_b - score_a, 4)
        print(f"{m.replace('_', ' ').title():<20} | {score_a:<18.4f} | {score_b:<22.4f} | {delta:+10.4f}")

    print(f"\nThời gian chạy: Config A: {metrics_a['latency_seconds']}s | Config B: {metrics_b['latency_seconds']}s")

    # Tìm worst performers
    all_details = details_a + details_b
    sorted_cases = sorted(all_details, key=lambda c: c["average"])
    worst_cases = sorted_cases[:5]

    print("\nWorst Performers:")
    for c in worst_cases[:3]:
        print(f"- [#{c['index']} | {c['config']}] Avg: {c['average']} | {c['question']}")

    # Lưu kết quả thô vào file json
    output_result = {
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
        "details_a": details_a,
        "details_b": details_b,
        "worst_cases": worst_cases,
    }
    result_json_path = Path(__file__).parent / "evaluation_results.json"
    result_json_path.write_text(json.dumps(output_result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved raw results to {result_json_path}")


if __name__ == "__main__":
    main()
