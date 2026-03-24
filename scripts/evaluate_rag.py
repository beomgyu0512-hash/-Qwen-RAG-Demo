from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rag_demo.rag_service import ManufacturingRAGService, RetrievedChunk


def normalize_text(text: str) -> str:
    compact = text.strip().lower()
    for token in [" ", "\n", "\t", "。", "，", "；", "：", "、", ",", ".", ":", ";", "（", "）", "(", ")"]:
        compact = compact.replace(token, "")
    return compact


def split_expected_points(text: str) -> list[str]:
    points = []
    for item in text.replace("；", ";").split(";"):
        cleaned = item.strip()
        if cleaned:
            points.append(cleaned)
    return points


def points_hit(answer: str, expected_points: Iterable[str]) -> tuple[int, int, list[str]]:
    normalized_answer = normalize_text(answer)
    matched: list[str] = []
    total = 0
    for point in expected_points:
        total += 1
        if normalize_text(point) in normalized_answer:
            matched.append(point)
    return len(matched), total, matched


@dataclass
class EvalItem:
    id: str
    question: str
    expected_answer_points: str
    source: str


def load_eval_items(csv_path: Path) -> list[EvalItem]:
    with csv_path.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            EvalItem(
                id=row["id"],
                question=row["question"],
                expected_answer_points=row["expected_answer_points"],
                source=row["source"],
            )
            for row in reader
        ]


def snippets_to_text(snippets: list[RetrievedChunk]) -> str:
    return " | ".join(f"{snippet.source}#chunk{snippet.chunk_id}" for snippet in snippets)


def build_markdown_summary(result_rows: list[dict[str, str]], top_k: int) -> str:
    total = len(result_rows)
    fully_passed = sum(1 for row in result_rows if row["heuristic_status"] == "pass")
    avg_coverage = (
        sum(float(row["coverage_ratio_value"]) for row in result_rows) / total if total else 0.0
    )

    lines = [
        "# RAG Eval Report",
        "",
        f"- Sample count: `{total}`",
        f"- Top-K: `{top_k}`",
        f"- Heuristic pass count: `{fully_passed}`",
        f"- Heuristic pass rate: `{fully_passed / total:.2%}`" if total else "- Heuristic pass rate: `0.00%`",
        f"- Average coverage ratio: `{avg_coverage:.2%}`",
        "",
        "> 说明：当前为基于标准答案要点的字符串覆盖率启发式评测，适合快速批量筛查，最终仍建议结合人工复核。",
        "",
        "## Detailed Results",
        "",
        "| ID | Status | Coverage | Question | Sources |",
        "|---|---|---:|---|---|",
    ]

    for row in result_rows:
        lines.append(
            f"| {row['id']} | {row['heuristic_status']} | {row['coverage_ratio']} | "
            f"{row['question']} | {row['retrieved_sources']} |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch evaluate the Qwen RAG demo.")
    parser.add_argument(
        "--input",
        default="data/eval/test_qa.csv",
        help="Path to the evaluation CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/eval/results",
        help="Directory for generated evaluation reports.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of retrieved chunks used for each question.",
    )
    args = parser.parse_args()

    csv_path = Path(args.input).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    service = ManufacturingRAGService()
    if not service.is_ready():
        print("Knowledge base not found. Building index from local documents...")
        service.build_index()

    items = load_eval_items(csv_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_output_path = output_dir / f"eval_result_{timestamp}.csv"
    md_output_path = output_dir / f"eval_report_{timestamp}.md"

    result_rows: list[dict[str, str]] = []
    for item in items:
        print(f"[{item.id}/{len(items)}] Evaluating: {item.question}")
        answer, snippets = service.answer_question(item.question, top_k=args.top_k)
        expected_points = split_expected_points(item.expected_answer_points)
        matched_count, total_count, matched_points = points_hit(answer, expected_points)
        coverage = matched_count / total_count if total_count else 0.0
        result_rows.append(
            {
                "id": item.id,
                "question": item.question,
                "expected_answer_points": item.expected_answer_points,
                "matched_points": "；".join(matched_points),
                "matched_count": str(matched_count),
                "total_count": str(total_count),
                "coverage_ratio_value": f"{coverage:.4f}",
                "coverage_ratio": f"{coverage:.2%}",
                "heuristic_status": "pass" if matched_count == total_count else "review",
                "source": item.source,
                "retrieved_sources": snippets_to_text(snippets),
                "answer": answer,
            }
        )

    with csv_output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "id",
                "question",
                "expected_answer_points",
                "matched_points",
                "matched_count",
                "total_count",
                "coverage_ratio_value",
                "coverage_ratio",
                "heuristic_status",
                "source",
                "retrieved_sources",
                "answer",
            ],
        )
        writer.writeheader()
        writer.writerows(result_rows)

    md_output_path.write_text(
        build_markdown_summary(result_rows, top_k=args.top_k),
        encoding="utf-8",
    )

    print(f"CSV result saved to: {csv_output_path}")
    print(f"Markdown report saved to: {md_output_path}")


if __name__ == "__main__":
    main()
