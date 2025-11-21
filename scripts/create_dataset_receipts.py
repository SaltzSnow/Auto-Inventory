"""Generate receipt manifest with ground-truth labels using dataset.csv."""

from __future__ import annotations

import csv
import json
import random
import sys
from dataclasses import dataclass
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "dataset.csv"
OUTPUT_DIR = ROOT / "test_data" / "dataset_receipts_v2"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"
GROUND_TRUTH_PATH = OUTPUT_DIR / "ground_truth.jsonl"

# Settings
DEFAULT_NUM_RECEIPTS = 30
MIN_ITEMS = 4
MAX_ITEMS = 10


@dataclass
class ProductEntry:
    name: str
    unit: str
    price: float

STORES = [
    "ร้านโชคดีมาร์ท",
    "บจก.ไทยซุปเปอร์",
    "ฟู้ดดี้สโตร์",
    "เชียงใหม่มินิมาร์ท",
    "ภูเก็ตเดลี่",
    "บางกอกออร์แกนิก",
    "ดอนเมืองซัพพลาย",
    "อีสานทรูมาร์ท",
    "สุขใจซูเปอร์",
    "สยามโฮลเซล",
]

BRANCHES = [
    "สาขาสยาม",
    "สาขาลาดพร้าว",
    "สาขาหัวหิน",
    "สาขาภูเก็ต",
    "สาขาขอนแก่น",
    "สาขานครปฐม",
    "สาขาเชียงใหม่",
    "สาขาบางแค",
]

ADDRESSES = [
    "123 ถนนสุขุมวิท เขตวัฒนา กรุงเทพฯ 10110",
    "55/8 ถ.ห้วยแก้ว ต.ช้างเผือก อ.เมืองเชียงใหม่",
    "78/4 ถ.เยาวราช อ.เมือง จ.ภูเก็ต",
    "21/9 ถ.ศรีนครินทร์ ต.ในเมือง อ.เมืองขอนแก่น",
    "459 ม.5 ต.คลองหนึ่ง อ.คลองหลวง จ.ปทุมธานี",
    "99 หมู่บ้านริมทะเล ต.หัวหิน อ.หัวหิน จ.ประจวบฯ",
]

PAYMENT_METHODS = [
    "เงินสด",
    "พร้อมเพย์",
    "บัตรเครดิต",
    "โอนผ่านโมบายแบงก์",
]

CASHIERS = ["Nicha", "Somchai", "Apin", "May", "Beam", "Nam"]


def load_products() -> List[ProductEntry]:
    entries: List[ProductEntry] = []
    with open(DATASET_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("ชื่อสินค้า") or "").strip()
            if not name:
                continue
            try:
                price = float(row.get("ราคาขาย 1", "0") or 0)
            except ValueError:
                price = 0.0
            if price <= 0:
                price = round(random.uniform(10.0, 250.0), 2)
            unit = (row.get("หน่วยเล็กที่สุด") or "ชิ้น").strip() or "ชิ้น"
            entries.append(ProductEntry(name=name, unit=unit, price=price))
    return entries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic receipt datasets")
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_NUM_RECEIPTS,
        help=f"Number of receipts to generate (default: {DEFAULT_NUM_RECEIPTS})",
    )
    return parser.parse_args()


def main(num_receipts: int):
    print("=" * 70)
    print("DATASET RECEIPT MANIFEST GENERATOR (GROUND TRUTH)")
    print("=" * 70)

    if not DATASET_PATH.exists():
        print(f"[ERROR] dataset.csv not found at {DATASET_PATH}")
        return

    products = load_products()
    if len(products) < 20:
        print("[ERROR] Need at least 20 products to generate receipts")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = []
    ground_truth_lines = []

    print(f"Generating {num_receipts} receipts using {len(products)} product entries...")

    for idx in range(1, num_receipts + 1):
        store = random.choice(STORES)
        branch = random.choice(BRANCHES)
        address = random.choice(ADDRESSES)
        cashier = random.choice(CASHIERS)
        issued_at = datetime.now() - timedelta(days=random.randint(0, 120), hours=random.randint(0, 23))
        invoice_no = f"EV{issued_at.strftime('%y%m%d')}-{random.randint(1000, 9999)}"
        vat_rate = random.choice([0.0, 0.07])
        payment_method = random.choice(PAYMENT_METHODS)

        num_items = random.randint(MIN_ITEMS, MAX_ITEMS)
        selected = random.sample(products, num_items)

        items = []
        subtotal = 0.0
        for prod in selected:
            qty = random.randint(1, 5)
            unit_price = round(prod.price * random.uniform(0.9, 1.15), 2)
            line_total = round(qty * unit_price, 2)
            subtotal += line_total
            items.append({
                "name": prod.name,
                "unit": prod.unit,
                "qty": qty,
                "unit_price": unit_price,
                "total": line_total,
            })

        subtotal = round(subtotal, 2)
        discount = round(random.choice([0.0, 0.0, 5.0, 10.0, round(random.uniform(1.0, 20.0), 2)]), 2)
        taxable_amount = max(subtotal - discount, 0.0)
        vat_base = taxable_amount / (1 + vat_rate) if vat_rate else taxable_amount
        vat_amount = round(taxable_amount - vat_base, 2)
        grand_total = round(taxable_amount, 2)

        payment_received = grand_total
        change_due = 0.0
        if payment_method == "เงินสด":
            payment_received = round(grand_total + random.uniform(1.0, 50.0), 2)
            change_due = round(payment_received - grand_total, 2)

        receipt_file = f"dataset_receipt_v2_{idx:03d}.png"

        totals = {
            "subtotal": subtotal,
            "discount": discount,
            "taxable_amount": taxable_amount,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "grand_total": grand_total,
            "payment_received": payment_received,
            "change_due": change_due,
        }

        manifest_entry = {
            "file": receipt_file,
            "store_name": store,
            "branch": branch,
            "address": address,
            "cashier": cashier,
            "issued_at": issued_at.isoformat(),
            "invoice_no": invoice_no,
            "payment_method": payment_method,
            "items": items,
            "totals": totals,
        }
        manifest.append(manifest_entry)

        ground_truth_lines.append({
            "file": receipt_file,
            "invoice_no": invoice_no,
            "issued_at": issued_at.isoformat(),
            "store_name": store,
            "branch": branch,
            "payment_method": payment_method,
            "items": items,
            "totals": totals,
        })

        if idx % 10 == 0 or idx == num_receipts:
            print(f"  Prepared {idx}/{num_receipts} receipts")

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with open(GROUND_TRUTH_PATH, "w", encoding="utf-8") as f:
        for line in ground_truth_lines:
            f.write(json.dumps(line, ensure_ascii=False))
            f.write("\n")

    print(f"\n[OK] Manifest saved to {MANIFEST_PATH}")
    print(f"[OK] Ground truth (JSONL) saved to {GROUND_TRUTH_PATH}")
    print(f"Total receipts: {len(manifest)}")


if __name__ == "__main__":
    args = parse_args()
    if args.count < 1:
        print("[ERROR] --count must be at least 1")
        sys.exit(1)
    main(args.count)
