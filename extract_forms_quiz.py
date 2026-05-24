#!/usr/bin/env python3
"""
Extract questions from 營造業丙種初訓_測驗.pdf (Google Forms quiz result PDF).

The PDF contains one student's test result (50 questions, score 72/100).
Format per page section:
  - Score blocks: N/2 → 4 option lines → optional (正確答案 → correct answer text)
  - Question texts: "N. question text" → terminated by * (may be on same line)

Output: forms_questions.json
"""

import json
import re
import difflib
import sys

import pypdfium2 as pdfium

PDF_PATH = "營造業丙種初訓_測驗.pdf"
BANK_PATH = "questions.json"
OUT_PATH  = "forms_questions.json"

# ── Text cleanup ─────────────────────────────────────────────────────────────
# Map half-width CJK radicals to full-width equivalents
_HALFWIDTH = {
    "⼝": "口", "⼊": "入", "⽅": "方", "⾼": "高", "⼯": "工",
    "⼤": "大", "⾯": "面", "⼀": "一", "⼩": "小", "⽔": "水",
    "⽕": "火", "⼟": "土", "⽊": "木", "⾦": "金", "⼈": "人",
    "⼒": "力", "⼿": "手", "⼼": "心", "⽬": "目", "⽿": "耳",
    "⾜": "足", "⾞": "車", "⾔": "言", "⾏": "行", "⾐": "衣",
    "⿂": "魚", "⿃": "鳥", "⼭": "山", "⽥": "田", "⾬": "雨",
    "⽇": "日", "⽉": "月", "⽣": "生", "⾁": "肉", "⾻": "骨",
    "⽪": "皮", "⾊": "色", "⽵": "竹", "⽶": "米", "⿆": "麥",
    "⿈": "黃", "⿊": "黑", "⽩": "白", "⽯": "石", "⽟": "玉",
    "⽡": "瓦", "⾍": "虫", "⽻": "羽", "⾃": "自", "⾄": "至",
    "⿐": "鼻", "⿏": "鼠", "⼆": "二", "⼋": "八", "⼗": "十",
    "⼜": "又", "⼦": "子", "⼥": "女", "⼰": "己", "⼸": "弓",
    "⽓": "气", "⽂": "文", "⽃": "斗", "⽄": "斤", "⽅": "方",
    "⽆": "无", "⽇": "日", "⽉": "月", "⽊": "木", "⽋": "欠",
    "⽌": "止", "⽍": "歹", "⽏": "毋", "⽐": "比", "⽑": "毛",
    "⽒": "氏", "⽓": "气", "⽔": "水", "⽕": "火", "⾘": "爪",
    "⽗": "父", "⽖": "爻", "⽙": "片", "⽛": "牙", "⽜": "牛",
    "⽝": "犬", "⽞": "玄", "⽠": "瓜", "⿇": "麻", "⿅": "鹿",
    "⽤": "用",
}
_HALFWIDTH_TABLE = str.maketrans(_HALFWIDTH)


def clean(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.translate(_HALFWIDTH_TABLE)
    # Collapse whitespace
    s = re.sub(r"[ \t　]+", " ", s)
    # Remove space between two CJK characters (line-break artifact)
    s = re.sub(
        r"([一-鿿，。！？、；：「」…—])\s+([一-鿿，。！？、；：「」…—])",
        r"\1\2", s
    )
    return s.strip()


# ── Extract raw text from PDF ─────────────────────────────────────────────────
def load_pdf_text(path: str) -> str:
    doc = pdfium.PdfDocument(path)
    pages = []
    for page in doc:
        tp = page.get_textpage()
        pages.append(tp.get_text_range())
    return "\n".join(pages)


# ── Split into page sections ──────────────────────────────────────────────────
def split_sections(full_text: str) -> list[str]:
    return re.split(r"https://docs\.google\.com[^\n]+\n網頁\d+/26\n?", full_text)


# ── Parse question texts ──────────────────────────────────────────────────────
# Key: look for "N." at start of line where the character after "." is NOT a digit
# (?!\d\D) rejects single-digit decimals like "1.5公尺" (digit then non-digit)
# but allows "12.11400伏特" where after "." comes two digits "11".
_RE_QNUM = re.compile(r"(?:^|\n)(\d{1,2})[.\．](?!\d\D)\s*", re.MULTILINE)

def parse_question_texts(section: str) -> list[tuple[int, str]]:
    text = section.replace("\r\n", "\n").replace("\r", "\n")
    positions = [
        (m.start(1), m.end(), int(m.group(1)))
        for m in _RE_QNUM.finditer(text)
        if 1 <= int(m.group(1)) <= 50
    ]
    results = []
    for i, (_, end, qnum) in enumerate(positions):
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        raw = text[end:next_start]
        # Strip trailing asterisk markers (both "…text *\n" and "…text\n*")
        raw = re.sub(r"[ ]*\*[ ]*$", "", raw.strip())
        raw = re.sub(r"\n\*\s*$", "", raw)
        raw = re.sub(r"[ ]*\*\s*\n", "\n", raw)
        results.append((qnum, clean(raw)))
    return results


# ── Parse score blocks ────────────────────────────────────────────────────────
_RE_SCORE = re.compile(r"(?:^|\n)([02])/2\n", re.MULTILINE)
_RE_CORRECT_HEADER = re.compile(r"\n正確答案\n")


def parse_score_blocks(section: str, q_start_pos: int) -> list[dict]:
    """
    q_start_pos: character position of the first question text in the section
                 (score blocks appear before questions).
    """
    text = section.replace("\r\n", "\n").replace("\r", "\n")
    # Only look for score blocks in the part before question texts
    pre = text[:q_start_pos] if q_start_pos < len(text) else text

    score_matches = list(_RE_SCORE.finditer(pre))
    blocks = []

    for j, sm in enumerate(score_matches):
        score_val = int(sm.group(1)) * 2  # 0 or 2
        seg_start = sm.end()
        seg_end = score_matches[j + 1].start() if j + 1 < len(score_matches) else len(pre)
        seg = pre[seg_start:seg_end]

        # Split on 正確答案
        ca_match = _RE_CORRECT_HEADER.search(seg)
        if ca_match:
            opt_raw = seg[:ca_match.start()]
            ca_raw = seg[ca_match.end():]
            # Take only the first non-empty line (avoid bleeding into page headers)
            first_line = next(
                (l.strip() for l in ca_raw.replace("\r\n", "\n").split("\n") if l.strip()),
                ""
            )
            correct_answer = clean(first_line)
        else:
            opt_raw = seg
            correct_answer = None

        options = parse_4_options(opt_raw)
        blocks.append({
            "score": score_val,
            "options": options,
            "correct_answer": correct_answer,
        })

    return blocks


def parse_4_options(raw: str) -> list[str]:
    """
    Given raw text containing 4 option lines (possibly with line-wrapped options),
    return a list of up to 4 clean option strings.
    """
    lines = [l.strip() for l in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n") if l.strip()]
    # Filter out known non-option lines
    lines = [l for l in lines if not re.match(r"^[02]/2$", l) and l != "正確答案"]

    if len(lines) <= 4:
        return [clean(l) for l in lines]

    # Merge continuation lines.
    # A line is a continuation if the previous line ends with '，' or '、'
    # OR the previous line is long (>18 chars) and this line starts lowercase or is short.
    merged = []
    for line in lines:
        if merged and (
            merged[-1].endswith("，") or
            merged[-1].endswith("、") or
            (len(merged[-1]) > 18 and not re.match(r"^[一-鿿\d（(A-Z]", line))
        ):
            merged[-1] = merged[-1] + line
        else:
            merged.append(line)

    return [clean(l) for l in merged[:4]]


# ── Match against existing bank ───────────────────────────────────────────────
def load_bank(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_in_bank(qtext: str, bank: list[dict]) -> dict | None:
    """Return bank question with highest text similarity (>= 0.65)."""
    best_ratio = 0.0
    best_q = None
    for bq in bank:
        r = difflib.SequenceMatcher(None, qtext, bq["text"]).ratio()
        if r > best_ratio:
            best_ratio = r
            best_q = bq
    return best_q if best_ratio >= 0.65 else None


def answer_index_from_text(correct_text: str, options: list[str]) -> int | None:
    """Find which option (1-based) best matches the correct answer text."""
    best_ratio = 0.0
    best_idx = 0
    for i, opt in enumerate(options):
        r = difflib.SequenceMatcher(None, correct_text, opt).ratio()
        if r > best_ratio:
            best_ratio = r
            best_idx = i
    return (best_idx + 1) if best_ratio >= 0.40 else None


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print(f"Reading {PDF_PATH} …")
    full_text = load_pdf_text(PDF_PATH)
    sections = split_sections(full_text)

    bank = load_bank(BANK_PATH)
    print(f"Loaded {len(bank)} bank questions.")

    all_q: dict[int, dict] = {}

    for sec_idx, section in enumerate(sections):
        # Find question texts and their positions in the raw section
        text = section.replace("\r\n", "\n").replace("\r", "\n")

        q_texts = parse_question_texts(section)
        if not q_texts:
            continue

        # Find position of first question number in text
        first_q_match = _RE_QNUM.search(text)
        q_start_pos = first_q_match.start(1) if first_q_match else len(text)

        score_blocks = parse_score_blocks(section, q_start_pos)

        for i, (qnum, qtext) in enumerate(q_texts):
            if qnum in all_q:
                continue  # already processed (earlier section had false-positive)

            sb = score_blocks[i] if i < len(score_blocks) else None
            options = sb["options"] if sb else []
            correct_text = sb["correct_answer"] if sb else None

            bank_q = find_in_bank(qtext, bank)
            bank_matches = False  # True if bank options agree with PDF data

            if bank_q and correct_text:
                # Student got wrong → explicit correct answer available.
                # Check if bank's answer matches our explicit answer.
                bank_correct = bank_q["options"][bank_q["answer"] - 1]
                ratio = difflib.SequenceMatcher(None, correct_text, bank_correct).ratio()
                if ratio >= 0.45:
                    # Bank and explicit agree → use bank (clean options)
                    options = bank_q["options"]
                    answer = bank_q["answer"]
                    answer_source = "bank_full"
                    bank_matches = True
                else:
                    # Bank disagrees → PDF has a different variant; use PDF options
                    print(f"  NOTE Q{qnum}: PDF variant differs from bank (using PDF options+explicit)")
                    answer = answer_index_from_text(correct_text, options)
                    answer_source = "explicit"

            elif bank_q and not correct_text:
                # Student got right → no explicit answer; use bank answer mapped to PDF options
                bank_correct = bank_q["options"][bank_q["answer"] - 1]
                if options:
                    a = answer_index_from_text(bank_correct, options)
                    if a:
                        answer = a
                        answer_source = "bank"
                        bank_matches = True
                # If options failed/empty, fall back to bank data fully
                if not bank_matches:
                    options = bank_q["options"]
                    answer = bank_q["answer"]
                    answer_source = "bank_full"
                    bank_matches = True

            else:
                # No bank match → use PDF-extracted data only
                answer = None
                answer_source = "unknown"
                if correct_text and options:
                    answer = answer_index_from_text(correct_text, options)
                    answer_source = "explicit"

            all_q[qnum] = {
                "id": qnum,
                "text": qtext,
                "options": options,
                "answer": answer,
                "answer_source": answer_source,
                "bank_id": bank_q["id"] if bank_q else None,
            }

    # Sort and report
    questions = sorted(all_q.values(), key=lambda q: q["id"])
    found = len(questions)
    missing_ids = [i for i in range(1, 51) if i not in all_q]
    with_answer = sum(1 for q in questions if q["answer"] is not None)
    by_source: dict[str, int] = {}
    for q in questions:
        src = q.get("answer_source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    print(f"\nExtracted: {found}/50 questions")
    print(f"  With answer: {with_answer}")
    for src, cnt in sorted(by_source.items()):
        print(f"    {src}: {cnt}")
    if missing_ids:
        print(f"  Missing IDs: {missing_ids}")

    print("\nFirst 5 questions:")
    for q in questions[:5]:
        print(f"  Q{q['id']} [bank={q['bank_id']}, ans={q['answer']} ({q['answer_source']})]: {q['text'][:55]}…")
        for i, opt in enumerate(q["options"], 1):
            marker = "✓" if i == q["answer"] else " "
            print(f"    {marker}({i}) {opt[:60]}")
        print()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
