#!/usr/bin/env python3
"""
Extract questions from 營造業丙種職業安全衛生業務主管 PDF and classify by law.
Output: questions.json
"""

import json
import re
import pypdfium2 as pdfium

PDF_PATH = "補充教材-營造業職業安全衛生業務主管參考題型(列印版)1120516.pdf"
OUT_PATH = "questions.json"

# ── Law classification rules (order matters – first match wins) ──────────────
LAW_RULES = [
    ("職業安全衛生法施行細則",    ["施行細則"]),
    ("職業安全衛生管理辦法",      ["管理辦法", "業務主管", "甲種", "乙種", "丙種",
                                    "自動檢查", "管理計畫", "承攬管理"]),
    ("職業安全衛生教育訓練規則",  ["教育訓練", "訓練規則", "受訓", "結訓",
                                    "安全衛生訓練", "三小時", "六小時", "3小時", "6小時"]),
    ("營造安全衛生設施標準",      ["鷹架", "施工架", "開挖", "擋土", "護欄", "安全網",
                                    "模板", "支撐", "墜落", "高處作業", "吊料", "構台",
                                    "開口部", "洞口", "安全母索", "防墜", "露天開挖",
                                    "擋土支撐", "型鋼", "鋼板樁", "斜撐"]),
    ("職業安全衛生設施規則",      ["設施規則", "通道淨", "採光", "照明", "接地",
                                    "漏電斷路器", "個人防護具", "防護具", "安全帽",
                                    "安全帶", "防護面罩", "通風換氣"]),
    ("起重升降機具安全規則",      ["起重機", "吊車", "升降機", "堆高機", "吊掛",
                                    "吊升", "荷重", "吊鉤", "移動式起重", "固定式起重"]),
    ("勞工健康保護規則",          ["健康檢查", "體格檢查", "急救人員", "護理人員", "健康保護"]),
    ("危害性化學品標示及通識規則",["SDS", "安全資料表", "GHS", "危害標示",
                                    "化學品標示", "物質安全", "通識規則", "危害性化學"]),
    ("缺氧症預防規則",            ["缺氧", "局限空間", "人孔", "下水道", "坑道", "缺氧症"]),
    ("高壓氣體勞工安全規則",      ["高壓氣體", "氧氣瓶", "乙炔", "鋼瓶", "高壓氣"]),
    ("鍋爐及壓力容器安全規則",    ["鍋爐", "壓力容器", "蒸氣鍋"]),
    ("勞動檢查法",                ["勞動檢查", "檢查員", "停工", "查察", "勞動檢查法"]),
    ("勞動基準法",                ["勞動基準", "職災補償", "工作時間", "加班費", "勞基法"]),
    ("職業安全衛生法",            ["職業安全衛生法", "雇主應", "罰鍰", "負責人",
                                    "公告", "危險性工作場所", "特別危害",
                                    "作業環境監測", "安全衛生委員會"]),
]

# ── Numeric detection (金庫密碼) ─────────────────────────────────────────────
NUMERIC_UNITS = (
    r"年|個月|月(?!薪)|日|天|小時|分鐘|分(?!包)|秒|"
    r"公尺|公分|毫米|公里|㎝|㎞|mm|cm(?![a-z])|(?<!\d)m(?!\w)|"
    r"公斤|噸|kg|"
    r"萬元|萬(?!全)|元|"
    r"人(?=以上|以下|名|員)|名|位|"
    r"倍|次|"
    r"%|％|度(?!假|數)"
)
RE_ARABIC = re.compile(r"\d+\.?\d*\s*(" + NUMERIC_UNITS + r")", re.UNICODE)
RE_CHINESE_NUM = re.compile(
    r"[一二三四五六七八九十百千萬]{1,4}\s*(" + NUMERIC_UNITS + r")", re.UNICODE
)
# Sequence-order options (efcdab, fecdba, abcde etc.)
RE_SEQ_ALPHA = re.compile(r"^[a-g]{4,7}$")


def is_numeric(text, options):
    combined = text + " " + " ".join(options)
    if RE_ARABIC.search(combined):
        return True
    if RE_CHINESE_NUM.search(combined):
        return True
    # Options that are permutations of letters → sequence question
    seq = sum(1 for o in options if RE_SEQ_ALPHA.match(o.strip().lower()))
    if seq >= 3:
        return True
    return False


def classify_law(text, options):
    combined = text + " " + " ".join(options)
    for law_name, keywords in LAW_RULES:
        for kw in keywords:
            if kw in combined:
                return law_name
    return "職業安全衛生法"


# ── PDF text extraction ──────────────────────────────────────────────────────
def extract_full_text(pdf_path):
    doc = pdfium.PdfDocument(pdf_path)
    pages = []
    for page in doc:
        tp = page.get_textpage()
        pages.append(tp.get_text_range())
    # Join pages; normalize line endings
    text = "\n".join(pages)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


# ── Parsing ──────────────────────────────────────────────────────────────────
# Format: (answer_digit)question_number. question_text (1)opt1 (2)opt2 (3)opt3 (4)opt4
# Answer marker looks like: (1)22. or (4)1.
# Key: the answer digit comes BEFORE the question number; options come AFTER

RE_Q_ANCHOR = re.compile(
    r"\(([1-4])\)"           # answer digit in parens
    r"(\d{1,3})\."           # question number (1-402) + dot
    r"(.+?)"                 # question text (non-greedy)
    r"(?=\([1-4]\)\d{1,3}\.\s|\Z)",  # lookahead: next question or end
    re.DOTALL
)

RE_OPT_SPLIT = re.compile(r"[(（]([1-4])[)）]")


def clean(s):
    """Collapse whitespace; remove spaces between CJK characters (PDF line-break artifacts)."""
    s = re.sub(r"[ \t\n\u3000]+", " ", s).strip()
    # Remove space between two CJK characters (line-break artifact)
    s = re.sub(r"([\u4e00-\u9fff\uff00-\uffef\u3000-\u303f，。！？、；：「」『』【】〔〕…—])\s+([\u4e00-\u9fff\uff00-\uffef\u3000-\u303f，。！？、；：「」『』【】〔〕…—ㄧ])", r"\1\2", s)
    # Also remove space between CJK and punctuation
    s = re.sub(r"([\u4e00-\u9fff])\s+([，。！？、；：\(\)（）])", r"\1\2", s)
    s = re.sub(r"([，。！？、；：\(\)（）])\s+([\u4e00-\u9fff])", r"\1\2", s)
    return s


def parse_options(raw_after_text):
    """
    Given text like 「(1)foo (2)bar (3)baz (4)qux」
    return a list of 4 option strings.
    """
    parts = RE_OPT_SPLIT.split(raw_after_text)
    # parts: [pre, '1', opt1_text, '2', opt2_text, ...]
    options = {}
    i = 1
    while i < len(parts) - 1:
        try:
            num = int(parts[i])
        except ValueError:
            i += 1
            continue
        val = clean(parts[i + 1])
        # Strip trailing next-question marker if present
        val = re.sub(r"\s*\([1-4]\)\d{1,3}\.\s*$", "", val).strip()
        options[num] = val
        i += 2
    return [options.get(k, "") for k in [1, 2, 3, 4]]


def parse_questions(full_text):
    questions = []

    # Step 1: find all question anchors
    # We look for patterns like (N)DDD. where N is 1-4, DDD is 1-3 digits
    # We need to avoid false positives from option markers like (1) inside text
    # Strategy: collect all candidate positions, then for each verify the number is sequential

    # Collect all (N)NNN. positions
    RE_CANDIDATE = re.compile(r"\(([1-4])\)(\d{1,3})\.")
    candidates = list(RE_CANDIDATE.finditer(full_text))

    # Filter: question numbers should be 1-402 and mostly sequential
    # We validate by checking number is in [1..402]
    valid = [(m, int(m.group(1)), int(m.group(2)))
             for m in candidates if 1 <= int(m.group(2)) <= 402]

    # For each valid anchor, extract content until next question anchor
    for idx, (m, answer, qnum) in enumerate(valid):
        start = m.end()
        # Find end: start of next question
        if idx + 1 < len(valid):
            end = valid[idx + 1][0].start()
        else:
            end = len(full_text)

        block = full_text[start:end]

        # Split block into question text + options
        # First (1) marker separates question text from options
        first_opt = RE_OPT_SPLIT.search(block)
        if not first_opt:
            # No options found – skip
            continue

        q_text = clean(block[:first_opt.start()])
        opts_raw = block[first_opt.start():]
        options = parse_options(opts_raw)

        if len([o for o in options if o]) < 4:
            continue

        law = classify_law(q_text, options)
        numeric = is_numeric(q_text, options)

        questions.append({
            "id": qnum,
            "text": q_text,
            "options": options,
            "answer": answer,
            "law": law,
            "isNumeric": numeric,
        })

    # Deduplicate (keep first occurrence of each id)
    seen = set()
    unique = []
    for q in questions:
        if q["id"] not in seen:
            seen.add(q["id"])
            unique.append(q)

    unique.sort(key=lambda q: q["id"])
    return unique


def main():
    print(f"Reading {PDF_PATH} ...")
    full_text = extract_full_text(PDF_PATH)

    print("Parsing questions ...")
    questions = parse_questions(full_text)
    print(f"Parsed {len(questions)} questions.")

    ids = set(q["id"] for q in questions)
    missing = [i for i in range(1, 403) if i not in ids]
    if missing:
        print(f"Missing IDs: {missing}")

    from collections import Counter
    law_counts = Counter(q["law"] for q in questions)
    numeric_count = sum(1 for q in questions if q["isNumeric"])

    with open("stats.txt", "w", encoding="utf-8") as f:
        f.write(f"Total: {len(questions)}\n")
        f.write(f"Missing: {missing}\n")
        f.write(f"Numeric (金庫密碼): {numeric_count}\n\n")
        f.write("Law distribution:\n")
        for law, cnt in law_counts.most_common():
            f.write(f"  {law}: {cnt}\n")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"Saved to {OUT_PATH}")
    print(f"Numeric: {numeric_count}")
    print("Stats written to stats.txt")


if __name__ == "__main__":
    main()
