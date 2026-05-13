from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from app.application.services.evaluation import RagEvaluator, load_rag_eval_dataset
from app.application.services.knowledge_service import KnowledgeService
from app.infra.db.session import SessionLocal, init_db


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate SAGAI RAG retrieval quality.")
    parser.add_argument("--dataset", required=True, help="Path to the RAG evaluation dataset JSON.")
    parser.add_argument("--output", help="Markdown report output path. Defaults to reports/rag_eval_*.md.")
    parser.add_argument("--top-k", type=int, help="Override dataset top_k.")
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Reindex knowledge before running the evaluation.",
    )
    return parser.parse_args()


async def run() -> int:
    args = parse_args()
    init_db()
    dataset = load_rag_eval_dataset(args.dataset)
    output = Path(args.output) if args.output else _default_output_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        if args.reindex:
            await KnowledgeService(session).reindex()

        evaluator = RagEvaluator.from_session(session)
        report = await evaluator.evaluate_dataset(dataset, top_k=args.top_k)

    output.write_text(report.to_markdown(), encoding="utf-8")
    metrics = report.metrics
    print(f"RAG evaluation report written to {output}")
    print(
        "Summary: "
        f"questions={metrics['total_questions']} "
        f"precision@1={metrics['precision_at_1']:.4f} "
        f"precision@3={metrics['precision_at_3']:.4f} "
        f"recall@5={metrics['recall_at_5']:.4f} "
        f"mrr={metrics['mean_reciprocal_rank']:.4f}"
    )
    return 0


def _default_output_path() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return Path("reports") / f"rag_eval_{stamp}.md"


def main() -> None:
    raise SystemExit(asyncio.run(run()))


if __name__ == "__main__":
    main()
