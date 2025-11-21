"""Render receipt images from dataset manifest."""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps
import numpy as np

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = r"C:\Windows\Fonts\leelawad.ttf"

FOOTERS = [
    "ขอบคุณที่อุดหนุน",
    "สะสมแต้มวันนี้ 2 เท่า",
    "สแกนไลน์เพื่อติดตามโปรโมชั่น",
    "รับคืนสินค้าได้ภายใน 7 วันพร้อมใบเสร็จ",
]


def pick_text_color(is_header: bool) -> tuple[int, int, int]:
    base = random.randint(15, 30) if is_header else random.randint(40, 90)
    fade = random.uniform(0.3, 0.5)
    jitter = random.randint(-8, 12)
    intensity = max(0, min(255, int((base + jitter) * fade)))
    return (intensity, intensity, intensity)


def apply_lighting_effect(image):
    width, height = image.size
    gradient = Image.linear_gradient("L").resize(image.size)
    gradient = gradient.rotate(random.uniform(-45, 45), resample=Image.BICUBIC)
    gradient = gradient.filter(ImageFilter.GaussianBlur(random.uniform(2, 5)))
    gradient = ImageOps.autocontrast(gradient)

    highlight = Image.new("L", image.size, 0)
    highlight_draw = ImageDraw.Draw(highlight)
    hx = random.randint(int(width * 0.1), int(width * 0.9))
    hy = random.randint(int(height * 0.1), int(height * 0.9))
    hr = random.randint(int(min(width, height) * 0.3), int(min(width, height) * 0.6))
    highlight_draw.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=random.randint(140, 220))
    highlight = highlight.filter(ImageFilter.GaussianBlur(random.uniform(50, 90)))
    gradient = ImageChops.add(gradient, highlight)

    gradient_rgb = Image.merge("RGB", (gradient, gradient, gradient))
    toned = ImageChops.multiply(image, gradient_rgb)
    toned = ImageChops.screen(toned, gradient_rgb)

    vignette = Image.new("L", (width, height), 0)
    vignette_draw = ImageDraw.Draw(vignette)
    pad = int(min(width, height) * random.uniform(0.05, 0.15))
    vignette_draw.ellipse((-pad, -pad, width + pad, height + pad), fill=random.randint(150, 210))
    vignette = vignette.filter(ImageFilter.GaussianBlur(random.uniform(60, 120)))
    vignette = ImageOps.invert(vignette).point(lambda v: int(v * random.uniform(0.5, 0.8)))
    vignette_rgb = Image.merge("RGB", (vignette, vignette, vignette))
    toned = ImageChops.multiply(toned, vignette_rgb)

    mix = random.uniform(0.45, 0.7)
    return Image.blend(image, toned, mix)


def add_paper_wear(image):
    width, height = image.size
    fiber_noise = Image.effect_noise((width, height), random.uniform(20, 55)).convert("L")
    fiber_noise = fiber_noise.filter(ImageFilter.GaussianBlur(random.uniform(0.6, 1.4)))
    fiber_noise = ImageOps.autocontrast(fiber_noise)
    fiber_rgb = ImageOps.colorize(fiber_noise, (225, 224, 215), (255, 255, 255))
    paper = Image.blend(image, fiber_rgb, random.uniform(0.05, 0.15))
    
    if random.random() < 0.7:
        crease_mask = Image.new("L", (width, height), 0)
        crease_draw = ImageDraw.Draw(crease_mask)
        for _ in range(random.randint(1, 2)):
            y = random.randint(height // 6, height - height // 6)
            offset = random.randint(-80, 80)
            shade = random.randint(60, 120)
            crease_draw.line((0, y, width, y + offset), fill=shade, width=random.randint(3, 6))
        crease_mask = crease_mask.filter(ImageFilter.GaussianBlur(random.uniform(2.5, 4.5)))
        crease_overlay = ImageOps.colorize(crease_mask, (250, 250, 250), (190, 190, 190))
        paper = Image.blend(paper, crease_overlay, 0.3)
    
    return paper


def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    a = np.array(matrix, dtype=float)
    b = np.array(pb).reshape(8)
    res = np.linalg.solve(a, b)
    return res.tolist()


def apply_perspective_warp(image):
    width, height = image.size
    canvas_w = int(width * 1.5)
    canvas_h = int(height * 1.5)
    margin_x = (canvas_w - width) / 2
    margin_y = (canvas_h - height) / 2
    
    jitter_x = width * random.uniform(0.05, 0.18)
    jitter_y = height * random.uniform(0.05, 0.18)
    
    base_quad = [
        (margin_x, margin_y),
        (margin_x + width, margin_y),
        (margin_x + width, margin_y + height),
        (margin_x, margin_y + height),
    ]
    perturbed_quad = [
        (x + random.uniform(-jitter_x, jitter_x), y + random.uniform(-jitter_y, jitter_y))
        for x, y in base_quad
    ]
    
    coeffs = find_coeffs(perturbed_quad, [(0, 0), (width, 0), (width, height), (0, height)])
    
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer.paste(image, (0, 0), image if image.mode == "RGBA" else None)
    
    warped = layer.transform((canvas_w, canvas_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    warped = warped.rotate(random.uniform(-8, 8), resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))
    return warped


def build_surface(size):
    base_color = tuple(random.randint(170, 230) for _ in range(3))
    surface = Image.new("RGB", size, base_color)
    noise = Image.effect_noise(size, random.uniform(20, 60)).convert("RGB")
    surface = Image.blend(surface, noise, 0.12)
    
    gradient = Image.linear_gradient("L").resize(size)
    gradient = gradient.rotate(random.uniform(0, 360), resample=Image.BICUBIC)
    gradient_rgb = Image.merge("RGB", (gradient, gradient, gradient))
    surface = Image.blend(surface, gradient_rgb, 0.07)
    return surface


def compose_scene(receipt_rgba):
    padding = 140
    bg_size = (receipt_rgba.width + padding * 2, receipt_rgba.height + padding * 2)
    background = build_surface(bg_size).convert("RGBA")
    
    alpha = receipt_rgba.split()[-1]
    blur_radius = random.uniform(8, 16)
    shadow_mask = alpha.filter(ImageFilter.GaussianBlur(blur_radius))
    shadow_color = (0, 0, 0, int(random.uniform(60, 120)))
    shadow_layer = Image.new("RGBA", bg_size, (0, 0, 0, 0))
    shadow_offset = (padding + random.randint(10, 30), padding + random.randint(18, 34))
    tinted_shadow = Image.new("RGBA", receipt_rgba.size, shadow_color)
    shadow_layer.paste(tinted_shadow, shadow_offset, shadow_mask)
    
    background = Image.alpha_composite(background, shadow_layer)
    
    receipt_offset = (shadow_offset[0] - random.randint(6, 16), shadow_offset[1] - random.randint(6, 18))
    background.paste(receipt_rgba, receipt_offset, receipt_rgba)
    
    return background.convert("RGB")


def render_receipt(receipt_data, output_path):
    """Render a single receipt image."""
    
    # Load font
    main_font = ImageFont.truetype(FONT_PATH, size=random.randint(26, 32))
    secondary_font = ImageFont.truetype(FONT_PATH, size=max(main_font.size - 4, 18))
    
    # Build lines
    lines = []
    lines.append(receipt_data['store_name'])
    lines.append(receipt_data['branch'])
    lines.append(receipt_data['address'])
    cashier = receipt_data.get("cashier", "Cashier")
    lines.append(f"โทร 02-345-6789 / แคชเชียร์: {cashier}")
    lines.append("----------------------------------------")
    
    issue_date = datetime.fromisoformat(receipt_data['issued_at'])
    lines.append(f"วันที่ {issue_date.strftime('%d/%m/%Y %H:%M')} หมายเลข {receipt_data['invoice_no']}")
    lines.append("----------------------------------------")
    lines.append("รายการ           จำนวน   ราคา   รวม")
    
    total = 0.0
    for item in receipt_data['items']:
        total += item['total']
        name = item['name'][:20]
        lines.append(
            f"{name:<20} {item['qty']:>2} x {item['unit_price']:>6.2f} {item['total']:>7.2f}"
        )
    
    lines.append("----------------------------------------")
    totals = receipt_data.get("totals", {})
    vat_rate = totals.get("vat_rate", receipt_data.get("vat_rate", 0.0))
    vat_base = totals.get("taxable_amount", total) - totals.get("vat_amount", 0.0)
    vat = totals.get("vat_amount", max(total - vat_base, 0.0))
    subtotal = totals.get("subtotal", total)
    discount = totals.get("discount", 0.0)
    grand_total = totals.get("grand_total", total)
    payment_received = totals.get("payment_received", grand_total)
    change_due = totals.get("change_due", 0.0)

    lines.append(f"ยอดรวมสินค้า {subtotal:>11.2f}")
    if discount:
        lines.append(f"ส่วนลดสมาชิก {discount:>9.2f}")
    lines.append(f"ยอดก่อนภาษี {vat_base:>10.2f}")
    lines.append(f"VAT {vat_rate*100:.0f}% {vat:>16.2f}")
    lines.append(f"รวมทั้งสิ้น {grand_total:>12.2f}")
    lines.append(f"ชำระโดย {receipt_data['payment_method']}")
    if receipt_data['payment_method'] == "เงินสด":
        lines.append(f"รับเงินมา {payment_received:>15.2f}")
        lines.append(f"เงินทอน {change_due:>18.2f}")
    lines.append("----------------------------------------")
    lines.append(random.choice(FOOTERS))
    lines.append("โปรดเก็บใบเสร็จนี้ไว้เป็นหลักฐาน")
    
    # Create image
    margin = 60
    line_spacing = main_font.size + 14
    width = random.choice([780, 820, 860])
    height = margin * 2 + line_spacing * len(lines) + 120
    
    base_color = random.randint(235, 250)
    bg = Image.new("RGB", (width, height), (base_color, base_color, base_color))
    texture = Image.effect_noise((width, height), random.uniform(35, 90)).convert("RGB")
    bg = Image.blend(bg, texture, 0.08)
    draw = ImageDraw.Draw(bg)
    
    y = margin
    for i, line in enumerate(lines):
        font = main_font if i < 4 else secondary_font
        jitter_x = margin + random.randint(-3, 3)
        draw.text((jitter_x, y), line, fill=pick_text_color(i < 4), font=font)
        y += line_spacing + random.randint(-1, 1)
    
    # Add PAID stamp
    stamp_color = (180, 50, 50)
    draw.rectangle([
        width - 300, height - 220,
        width - 60, height - 120
    ], outline=stamp_color, width=4)
    draw.text((width - 280, height - 205), "PAID", fill=stamp_color, font=secondary_font)
    
    # Apply effects
    bg = add_paper_wear(bg)
    bg = apply_lighting_effect(bg)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=0.4))
    
    receipt_rgba = bg.convert("RGBA")
    warped = apply_perspective_warp(receipt_rgba)
    final_image = compose_scene(warped)
    
    final_image.save(output_path, format="PNG")


def parse_args():
    parser = argparse.ArgumentParser(description="Render dataset receipts")
    parser.add_argument(
        "--manifest",
        default=ROOT / "test_data" / "dataset_receipts_v2" / "manifest.json",
        type=Path,
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--output",
        default=ROOT / "test_data" / "dataset_receipts_v2",
        type=Path,
        help="Directory for rendered receipts",
    )
    return parser.parse_args()


def main():
    print("="*60)
    print("RECEIPT IMAGE RENDERER")
    print("="*60)
    args = parse_args()

    manifest_path = args.manifest
    output_dir = args.output

    # Read manifest
    print(f"\nReading manifest from {manifest_path}...")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    print(f"[OK] Found {len(manifest)} receipts to render")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Render receipts
    print(f"\nRendering {len(manifest)} receipt images...")
    print("This may take a few minutes...\n")
    
    for i, receipt_data in enumerate(manifest, 1):
        output_path = output_dir / receipt_data['file']
        render_receipt(receipt_data, output_path)
        
        if i % 5 == 0:
            print(f"  Rendered {i}/{len(manifest)} receipts")
    
    print(f"\n[OK] All receipts rendered successfully!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
