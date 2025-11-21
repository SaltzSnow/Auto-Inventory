"""Evaluate receipt processing accuracy using dataset_receipts_v2 via API."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple

import httpx
from httpx import ASGITransport

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_PATH))

# Ensure UTF-8 logs for Thai text
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

try:
    from main import app  # type: ignore
except Exception:
    app = None

DATASET_DIR = PROJECT_ROOT / "test_data" / "dataset_receipts_v2"
GROUND_TRUTH_PATH = DATASET_DIR / "ground_truth.jsonl"
REPORT_PATH = DATASET_DIR / "evaluation_report.json"


@dataclass
class ReceiptAnalysis:
    expected_items: int
    name_matches: int
    quantity_matches: int
    quantity_accuracy: float
    quantity_mismatches: List[Dict[str, List[int]]]
    missing_items: Dict[str, int]
    extra_items: Dict[str, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate OCR pipeline against dataset_receipts_v2")
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Send requests through a running backend API instead of the in-process app",
    )
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("BACKEND_API_BASE_URL", "http://127.0.0.1:8000"),
        help="Base URL when --use-api is enabled (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=float(os.getenv("BACKEND_API_TIMEOUT", "90")),
        help="HTTP timeout (seconds) for API requests (default: 90)",
    )
    parser.add_argument(
        "--min-quantity-accuracy",
        type=float,
        default=0.90,
        help="Stop looping once quantity accuracy meets or exceeds this threshold (default: 0.90)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum evaluation loops before giving up (default: 3)",
    )
    parser.add_argument(
        "--post-regenerate-evals",
        type=int,
        default=2,
        help="Additional evaluations to run after regenerating receipts (default: 2)",
    )
    parser.add_argument(
        "--regen-count",
        type=int,
        default=30,
        help="Number of receipts to regenerate when refreshing the dataset (default: 30)",
    )
    parser.add_argument(
        "--auto-regenerate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Automatically run create/render scripts once the target accuracy is met (default: True)",
    )
    parser.add_argument(
        "--skip-loop",
        action="store_true",
        help="Run evaluation once regardless of accuracy thresholds",
    )
    return parser.parse_args()


def load_ground_truth() -> List[Dict]:
    entries: List[Dict] = []
    with GROUND_TRUTH_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


_NON_WORD_PATTERN = re.compile(r"[^\wก-ฮ๐-๙]+", flags=re.UNICODE)


def normalize_name(name: str) -> str:
    cleaned = (name or "").strip().lower()
    cleaned = _NON_WORD_PATTERN.sub("", cleaned)
    return cleaned


def _safe_int(value) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return 0


def _build_pred_pool(predicted_items: List[Dict]) -> List[Dict]:
    pool = []
    for idx, item in enumerate(predicted_items):
        name = item.get("product_name") or item.get("name") or ""
        pool.append(
            {
                "index": idx,
                "name": name.strip(),
                "normalized": normalize_name(name),
                "quantity": _safe_int(item.get("quantity", 0)),
                "raw": item,
                "used": False,
            }
        )
    return pool


def _match_item(gt_name: str, pred_pool: List[Dict], threshold: float = 0.82):
    normalized_gt = normalize_name(gt_name)
    best = None
    best_score = 0.0
    for candidate in pred_pool:
        if candidate["used"]:
            continue
        score = SequenceMatcher(None, normalized_gt, candidate["normalized"]).ratio()
        if score > best_score:
            best = candidate
            best_score = score
    if best and best_score >= threshold:
        best["used"] = True
        return best, best_score
    return None, best_score


def analyze_items(gt_items: List[Dict], predicted_items: List[Dict]) -> ReceiptAnalysis:
    pred_pool = _build_pred_pool(predicted_items)
    expected_items = len(gt_items)
    name_matches = 0
    quantity_matches = 0
    quantity_mismatches: List[Dict[str, List[int]]] = []
    missing_items: Dict[str, int] = {}

    for item in gt_items:
        gt_name = item.get("name") or ""
        gt_qty = _safe_int(item.get("qty", 0))
        match, score = _match_item(gt_name, pred_pool)
        if match:
            name_matches += 1
            pred_qty = match["quantity"]
            if pred_qty == gt_qty:
                quantity_matches += 1
            else:
                quantity_mismatches.append(
                    {
                        "name": gt_name,
                        "expected_qty": [gt_qty],
                        "predicted_qty": [pred_qty],
                        "match_score": round(score, 3),
                    }
                )
        else:
            missing_items[gt_name] = gt_qty

    extra_items = {
        candidate["name"]: candidate["quantity"]
        for candidate in pred_pool
        if not candidate["used"]
    }

    quantity_accuracy = (quantity_matches / expected_items) if expected_items else 0.0

    return ReceiptAnalysis(
        expected_items=expected_items,
        name_matches=name_matches,
        quantity_matches=quantity_matches,
        quantity_accuracy=quantity_accuracy,
        quantity_mismatches=quantity_mismatches,
        missing_items=missing_items,
        extra_items=extra_items,
    )


async def evaluate_receipts(use_api: bool, base_url: str, timeout: float) -> Tuple[Dict, List[Dict]]:
    entries = load_ground_truth()
    total_expected = 0
    total_name_matches = 0
    total_quantity_matches = 0
    results: List[Dict] = []

    client_kwargs = {"timeout": timeout}
    if use_api:
        client_kwargs["base_url"] = base_url
    else:
        if app is None:
            raise RuntimeError("FastAPI app not available. Run with --use-api instead.")
        client_kwargs["transport"] = ASGITransport(app=app)
        client_kwargs["base_url"] = "http://testserver"

    async with httpx.AsyncClient(**client_kwargs) as client:
        for entry in entries:
            file_name = entry["file"]
            image_path = DATASET_DIR / file_name
            if not image_path.exists():
                results.append({
                    "file": file_name,
                    "status": "error",
                    "error": "Image not found",
                })
                continue

            with image_path.open("rb") as f:
                file_bytes = f.read()

            response = await client.post(
                "/api/receipts/upload",
                params={"sync": "true"},
                files={"file": (file_name, file_bytes, "image/png")},
            )

            if response.status_code != 200:
                results.append({
                    "file": file_name,
                    "status": "error",
                    "error": f"HTTP {response.status_code}: {response.text}",
                })
                continue

            payload = response.json()
            result = payload.get("result") or {}
            predicted_items = result.get("items", [])

            analysis = analyze_items(entry["items"], predicted_items)

            total_expected += analysis.expected_items
            total_name_matches += analysis.name_matches
            total_quantity_matches += analysis.quantity_matches

            results.append({
                "file": file_name,
                "receipt_id": result.get("receipt_id"),
                "image_url": result.get("image_url"),
                "status": "ok" if analysis.name_matches == analysis.expected_items else "partial",
                "items_expected": analysis.expected_items,
                "name_matches": analysis.name_matches,
                "quantity_matches": analysis.quantity_matches,
                "quantity_accuracy": analysis.quantity_accuracy,
                "quantity_mismatches": analysis.quantity_mismatches,
                "missing_items": analysis.missing_items,
                "extra_items": analysis.extra_items,
            })

    name_accuracy = (total_name_matches / total_expected) if total_expected else 0.0
    quantity_accuracy = (total_quantity_matches / total_expected) if total_expected else 0.0

    summary = {
        "receipts": len(entries),
        "items_expected": total_expected,
        "items_matched": total_name_matches,
        "name_matches": total_name_matches,
        "quantity_matches": total_quantity_matches,
        "accuracy": name_accuracy,
        "name_accuracy": name_accuracy,
        "quantity_accuracy": quantity_accuracy,
    }

    return summary, results


def write_report(summary: Dict, results: List[Dict], history: List[Dict], label: str) -> None:
    report = {
        **summary,
        "run_label": label,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results,
    }
    if history:
        report["history"] = history
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def print_summary(label: str, summary: Dict) -> None:
    print(f"\n=== Receipt Evaluation Summary ({label}) ===")
    print(f"Receipts evaluated : {summary['receipts']}")
    print(f"Total items (GT)   : {summary['items_expected']}")
    print(
        f"Name accuracy      : {summary['name_accuracy'] * 100:.2f}% "
        f"({summary['name_matches']}/{summary['items_expected']})"
    )
    print(
        f"Quantity accuracy  : {summary['quantity_accuracy'] * 100:.2f}% "
        f"({summary['quantity_matches']}/{summary['items_expected']})"
    )


def record_history_entry(label: str, summary: Dict) -> Dict:
    return {
        "label": label,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "name_accuracy": summary["name_accuracy"],
        "quantity_accuracy": summary["quantity_accuracy"],
        "items_expected": summary["items_expected"],
        "name_matches": summary["name_matches"],
        "quantity_matches": summary["quantity_matches"],
    }


def run_subprocess(command: List[str]) -> None:
    subprocess.run(command, cwd=str(PROJECT_ROOT), check=True)


def regenerate_dataset(count: int) -> None:
    print("\n[INFO] Regenerating receipt dataset ...")
    create_cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "create_dataset_receipts.py")]
    if count and count > 0:
        create_cmd.extend(["--count", str(count)])
    run_subprocess(create_cmd)
    run_subprocess([sys.executable, str(PROJECT_ROOT / "scripts" / "render_dataset_receipts.py")])


def run_iteration(label: str, history: List[Dict], use_api: bool, base_url: str, timeout: float) -> Dict:
    summary, results = asyncio.run(evaluate_receipts(use_api, base_url, timeout))
    history.append(record_history_entry(label, summary))
    write_report(summary, results, history, label)
    print_summary(label, summary)
    return summary


def main():
    args = parse_args()
    history: List[Dict] = []
    success_summary: Dict | None = None

    iterations = max(args.max_iterations, 1)
    for iteration in range(1, iterations + 1):
        label = f"run-{iteration}"
        summary = run_iteration(label, history, args.use_api, args.api_base_url, args.api_timeout)

        if args.skip_loop:
            success_summary = summary
            break

        if summary["quantity_accuracy"] >= args.min_quantity_accuracy:
            success_summary = summary
            break

    if success_summary is None:
        print(
            f"\n[ERROR] Quantity accuracy did not reach {args.min_quantity_accuracy * 100:.2f}% "
            f"after {iterations} iteration(s)."
        )
        sys.exit(1)

    if args.auto_regenerate:
        regenerate_dataset(args.regen_count)
        for idx in range(1, max(args.post_regenerate_evals, 0) + 1):
            label = f"post-regenerate-{idx}"
            run_iteration(label, history, args.use_api, args.api_base_url, args.api_timeout)

    print("\n[OK] Evaluation workflow completed.")


if __name__ == "__main__":
    main()
