#!/usr/bin/env python3
"""Build a bilingual one-page expert brief for NeoRepro."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFError, TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/pdf/neorepro_expert_brief_bilingual.pdf"

NAVY = HexColor("#102A43")
TEAL = HexColor("#078B83")
TEAL_LIGHT = HexColor("#E6F5F3")
BLUE = HexColor("#286F9E")
BLUE_LIGHT = HexColor("#EAF2F8")
ORANGE = HexColor("#D97706")
INK = HexColor("#172B4D")
MUTED = HexColor("#5D6B7A")
LINE = HexColor("#D7E0E8")
PAPER = HexColor("#F5F7FA")
CARD = white


def register_fonts() -> tuple[str, str]:
    regular = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    medium = "/System/Library/Fonts/STHeiti Medium.ttc"
    pdfmetrics.registerFont(TTFont("NeoCJK", regular))
    try:
        pdfmetrics.registerFont(TTFont("NeoCJK-Medium", medium, subfontIndex=0))
        return "NeoCJK", "NeoCJK-Medium"
    except TTFError:
        return "NeoCJK", "NeoCJK"


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9@.+%:/=()\[\]-]+|\s+|.", text)


def wrap(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for token in tokens(text):
        candidate = current + token
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    width: float,
    font: str,
    size: float,
    color=INK,
    leading: float | None = None,
    max_lines: int | None = None,
) -> float:
    leading = leading or size * 1.35
    lines = wrap(text, font, size, width)
    if max_lines:
        lines = lines[:max_lines]
    c.setFillColor(color)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def rounded_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, fill=CARD) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 9, fill=1, stroke=1)


def metric_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    number: str,
    cn: str,
    en: str,
    accent,
    regular: str,
    medium: str,
) -> None:
    rounded_card(c, x, y, w, h)
    c.setFillColor(accent)
    c.roundRect(x, y, 6, h, 3, fill=1, stroke=0)
    c.setFont(medium, 22)
    c.setFillColor(accent)
    c.drawString(x + 17, y + h - 30, number)
    c.setFont(medium, 9.4)
    c.setFillColor(INK)
    c.drawString(x + 17, y + h - 49, cn)
    draw_wrapped(c, en, x + 17, y + h - 66, w - 31, regular, 7.2, MUTED, 9.3, 2)


def comparison_bar(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    title: str,
    subtitle: str,
    bigmhc: float,
    prime: float,
    minimum: float,
    maximum: float,
    regular: str,
    medium: str,
) -> None:
    c.setFont(medium, 9.5)
    c.setFillColor(INK)
    c.drawString(x, y, title)
    c.setFont(regular, 7.2)
    c.setFillColor(MUTED)
    c.drawRightString(x + w, y, subtitle)
    track_x = x + 62
    track_w = w - 78
    for index, (name, value, color) in enumerate(
        (("BigMHC", bigmhc, HexColor("#8B9AAA")), ("PRIME", prime, TEAL))
    ):
        row_y = y - 18 - index * 23
        c.setFont(regular, 7.8)
        c.setFillColor(MUTED)
        c.drawString(x, row_y + 2, name)
        c.setFillColor(HexColor("#E7ECF1"))
        c.roundRect(track_x, row_y, track_w, 8, 4, fill=1, stroke=0)
        length = max(0, min(1, (value - minimum) / (maximum - minimum))) * track_w
        c.setFillColor(color)
        c.roundRect(track_x, row_y, length, 8, 4, fill=1, stroke=0)
        c.setFont(medium, 8)
        c.setFillColor(INK)
        c.drawRightString(x + w, row_y + 1, f"{value:.3f}")


def bullet(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    cn: str,
    en: str,
    regular: str,
    medium: str,
) -> float:
    c.setFillColor(TEAL)
    c.circle(x + 3, y + 2, 2.3, fill=1, stroke=0)
    c.setFont(medium, 8.6)
    c.setFillColor(INK)
    c.drawString(x + 13, y, cn)
    y -= 13
    y = draw_wrapped(c, en, x + 13, y, width - 13, regular, 7.1, MUTED, 9.1, 2)
    return y - 7


def build() -> None:
    regular, medium = register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    page_w, page_h = landscape(A4)
    c = canvas.Canvas(str(OUTPUT), pagesize=(page_w, page_h), pageCompression=1)
    c.setTitle("NeoRepro - Bilingual Expert Brief")
    c.setAuthor("NeoRepro")

    c.setFillColor(PAPER)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    # Header
    c.setFillColor(NAVY)
    c.rect(0, page_h - 72, page_w, 72, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, page_h - 75, page_w, 3, fill=1, stroke=0)
    c.setFont(medium, 21)
    c.setFillColor(white)
    c.drawString(38, page_h - 34, "NeoRepro 核心成果 | Expert Brief")
    c.setFont(regular, 9.2)
    c.setFillColor(HexColor("#C9D7E5"))
    c.drawString(
        39,
        page_h - 54,
        "公共 MHC-I 新抗原预测工具的泄漏感知复现与患者级评估  |  Leakage-aware reproduction and patient-level evaluation",
    )

    # Core message, bilingual columns
    top_y = page_h - 94
    c.setFont(medium, 10)
    c.setFillColor(TEAL)
    c.drawString(39, top_y, "一句话结论")
    c.drawString(427, top_y, "BOTTOM LINE")
    draw_wrapped(
        c,
        "最重要的发现不是简单宣布“谁最好”，而是证明：常用外部基准可能已进入模型训练集；严格排除泄漏后，模型差异仍存在，但绝对预测能力有限。",
        39,
        top_y - 17,
        363,
        medium,
        11.3,
        INK,
        16,
        3,
    )
    draw_wrapped(
        c,
        "The key result is not a simplistic winner. A widely used external benchmark had entered training data; after strict leakage exclusion, model differences persisted, but absolute predictive performance remained modest.",
        427,
        top_y - 17,
        374,
        regular,
        9.6,
        INK,
        13.2,
        4,
    )

    # Three evidence cards
    card_y = 337
    gap = 13
    card_w = (page_w - 78 - 2 * gap) / 3
    metric_card(
        c,
        39,
        card_y,
        card_w,
        82,
        "520 / 520",
        "TESLA 记录与 PRIME2 训练集精确重叠",
        "TESLA records exactly overlapped PRIME2 training data; they were withdrawn as external validation evidence.",
        ORANGE,
        regular,
        medium,
    )
    metric_card(
        c,
        39 + card_w + gap,
        card_y,
        card_w,
        82,
        "17,475",
        "泄漏过滤后的 IMPROVE pMHC 记录",
        "Leakage-filtered pMHC records: 465 positives, 70 patients, 3 cohorts, one common evaluation set.",
        BLUE,
        regular,
        medium,
    )
    metric_card(
        c,
        39 + 2 * (card_w + gap),
        card_y,
        card_w,
        82,
        "+0.051",
        "PRIME 相对 BigMHC 的 AUROC 差值",
        "Patient-bootstrap 95% CI: 0.008 to 0.092. Direction robust across all reported sensitivity analyses.",
        TEAL,
        regular,
        medium,
    )

    # Lower left: primary comparisons
    left_x, lower_y, left_w, lower_h = 39, 117, 368, 202
    rounded_card(c, left_x, lower_y, left_w, lower_h)
    c.setFont(medium, 11)
    c.setFillColor(NAVY)
    c.drawString(left_x + 17, lower_y + lower_h - 24, "主要结果 | PRIMARY RESULTS")
    c.setFont(regular, 7.2)
    c.setFillColor(MUTED)
    c.drawRightString(left_x + left_w - 17, lower_y + lower_h - 23, "common support / same task")
    comparison_bar(
        c,
        left_x + 17,
        lower_y + lower_h - 52,
        left_w - 34,
        "总体区分度 | Pooled AUROC",
        "higher is better",
        0.545829,
        0.596909,
        0.50,
        0.65,
        regular,
        medium,
    )
    comparison_bar(
        c,
        left_x + 17,
        lower_y + lower_h - 116,
        left_w - 34,
        "患者级检索 | Mean pMHC Recall@20",
        "60 positive-bearing patients",
        0.145803,
        0.260047,
        0.00,
        0.30,
        regular,
        medium,
    )
    c.setFillColor(TEAL_LIGHT)
    c.roundRect(left_x + 17, lower_y + 13, left_w - 34, 29, 6, fill=1, stroke=0)
    c.setFont(medium, 7.8)
    c.setFillColor(TEAL)
    c.drawString(left_x + 28, lower_y + 30, "稳健性 | Robustness")
    c.setFont(regular, 6.8)
    c.setFillColor(INK)
    c.drawString(
        left_x + 28,
        lower_y + 18,
        "Exact-peptide, Hamming-1, 9-10mer, patient-peptide and within-HLA normalization all preserved the direction.",
    )

    # Lower right: value and boundary
    right_x, right_w = 421, page_w - 421 - 39
    rounded_card(c, right_x, lower_y, right_w, lower_h)
    c.setFont(medium, 11)
    c.setFillColor(NAVY)
    c.drawString(right_x + 17, lower_y + lower_h - 24, "实质价值 | WHY IT MATTERS")
    y = lower_y + lower_h - 49
    y = bullet(
        c,
        right_x + 17,
        y,
        right_w - 34,
        "阻止错误外部验证",
        "Prevents training-overlapped data from being presented as independent evidence.",
        regular,
        medium,
    )
    y = bullet(
        c,
        right_x + 17,
        y,
        right_w - 34,
        "把比较变成可审计流程",
        "Provides pinned tools, common support, provenance, failure evidence and byte-stable reproduction.",
        regular,
        medium,
    )
    y = bullet(
        c,
        right_x + 17,
        y,
        right_w - 34,
        "给出可信而克制的模型差异",
        "PRIME ranked better here, but low AP and patient heterogeneity argue against universal superiority.",
        regular,
        medium,
    )
    c.setFillColor(BLUE_LIGHT)
    c.roundRect(right_x + 17, lower_y + 13, right_w - 34, 43, 6, fill=1, stroke=0)
    c.setFont(medium, 7.8)
    c.setFillColor(BLUE)
    c.drawString(right_x + 27, lower_y + 42, "证据边界 | SCOPE")
    c.setFont(regular, 6.8)
    c.setFillColor(INK)
    c.drawString(
        right_x + 27,
        lower_y + 29,
        "仅评估 presentation 预筛选候选的 pMHC multimer 可检测 T-cell recognition。",
    )
    c.drawString(
        right_x + 27,
        lower_y + 19,
        "Not natural processing, tumor presentation, killing or clinical benefit.",
    )

    # Footer
    c.setStrokeColor(LINE)
    c.line(39, 98, page_w - 39, 98)
    c.setFont(medium, 7.2)
    c.setFillColor(NAVY)
    c.drawString(39, 83, "复现验证 | REPRODUCIBILITY")
    c.setFont(regular, 6.8)
    c.setFillColor(MUTED)
    c.drawString(
        39,
        70,
        "Clean checkout: 27/27 tests passed; 24 independent metric checks; max error 1.1e-16; tracked outputs byte-stable.",
    )
    c.setFont(medium, 7.2)
    c.setFillColor(NAVY)
    c.drawString(485, 83, "主要来源 | KEY SOURCES")
    c.setFont(regular, 6.5)
    c.setFillColor(MUTED)
    c.drawString(485, 70, "IMPROVE (2024) · PRIME2 (2023) · BigMHC (2023) · TESLA (2020)")
    c.setFont(regular, 5.8)
    c.setFillColor(HexColor("#8291A2"))
    c.drawString(39, 46, "NeoRepro · Evidence-first benchmark brief · 2026-08-20")
    c.drawRightString(
        page_w - 39, 46, "Interpretation: dataset- and contract-specific; no clinical-utility claim"
    )

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
