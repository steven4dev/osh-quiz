#!/usr/bin/env python3
"""
Extract questions from 4 source files for 缺氧作業主管 quiz.

Sources:
  1. 1090501_缺氧作業主管試題.pdf   → "1090501練習題"   (pdfplumber table)
  2. 222002A13_參考試題.pdf          → "22200乙級"       (plain text)
  3. 參考試題2021.docx               → "2021參考試題"    (python-docx tables)
  4. 複習測驗題.doc                  → "複習測驗題"      (win32com / raw text)

Output: kyso/questions.json
"""

import json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent / "缺氧作業主管題庫"
OUT  = Path(__file__).parent / "questions.json"

# ── Shared helpers ─────────────────────────────────────────────────────────────
_CJK = r'[⺀-鿿＀-￯]'   # CJK + fullwidth chars
_RE_SPACE_AFTER  = re.compile(rf'(?<={_CJK}) ')   # space right after CJK
_RE_SPACE_BEFORE = re.compile(rf' (?={_CJK})')    # space right before CJK

def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    s = _RE_SPACE_AFTER.sub('', s)   # 進入 作業 → 進入作業
    s = _RE_SPACE_BEFORE.sub('', s)  # 18 度     → 18度
    return s

NUMERIC_UNITS = (
    r"年|個月|月(?!薪)|日|天|小時|分鐘|分(?!包)|秒|"
    r"公尺|公分|毫米|公里|㎝|㎞|mm|cm(?![a-z])|(?<!\d)m(?!\w)|"
    r"公斤|噸|kg|"
    r"萬元|萬(?!全)|元|"
    r"人(?=以上|以下|名|員)|名|位|"
    r"倍|次|"
    r"%|％|度(?!假|數)|"
    r"ppm|PPM"
)
RE_ARABIC     = re.compile(r"\d+\.?\d*\s*(" + NUMERIC_UNITS + r")", re.UNICODE)
RE_CHINESE_NUM = re.compile(
    r"[一二三四五六七八九十百千萬]{1,4}\s*(" + NUMERIC_UNITS + r")", re.UNICODE
)
RE_NEGATIVE = re.compile(
    r"何者.{0,10}(?:非(?!常)|為非|不是|不正確|有誤|錯誤|不符合|不屬於|不包括|不適當|不適用|不為(?!了|何))"
    r"|何項.{0,10}(?:不正確|有誤|錯誤|不符合|不為|不適用)"
    r"|何種.{0,10}(?:不正確|有誤|錯誤|不符合|不適用)"
    r"|何者.{0,6}[「\"](?:非|不)[」\"]"
    r"|下列.{0,20}(?:有誤|不正確|錯誤的|不符合|非正確)"
    r"|哪.{0,5}(?:不正確|有誤|錯誤)"
    r"|何者.{0,20}無關"
    r"|何項.{0,20}無關"
    r"|何種.{0,20}無關"
    r"|何不為"
    r"|非屬"
    r"|不當行為"
    r"|不必(?!的)"
    r"|無須(?!知)",
    re.UNICODE
)

def is_numeric(text, options):
    combined = text + " " + " ".join(options)
    if RE_ARABIC.search(combined):
        return True
    if RE_CHINESE_NUM.search(combined):
        return True
    bare = sum(1 for o in options if re.match(r"^\d{1,4}\s*(以上|以下|以內)?$", o.strip()))
    return bare >= 2

# ── Chapter classification (for non-22200乙級 sources) ────────────────────────
# 6 chapters of the 缺氧作業主管 course.
# Rules: ordered by specificity (first match wins).
CHAPTER_RULES = [
    # Ch4: Emergency & First Aid — most distinct keywords
    ("第4章 缺氧事故處理與急救", [
        "急救", "CPR", "心肺復甦", "心外按摩", "人工呼吸",
        "燒燙傷", "沖、脫、泡", "施救者", "傷患", "AED",
        "心臟停止跳動", "生命徵象", "失去意識",
        "人工呼吸法", "復甦術", "昏倒", "昏迷.*救",
        "援救者", "救援者", "搶救.*防護", "中毒.*搶救",
        "缺氧症.*症狀", "缺氧.*症狀", "症狀.*缺氧",
        "意識.*喪失", "呼吸停止",
    ]),
    # Ch5: Environmental Measurement — instrument / sampling / exposure standard
    ("第5章 缺氧危險場所之環境測定", [
        "採樣", "檢知管", "直讀式儀器", "採樣管", "採樣器",
        "採氣管", "吸附劑", "活性碳", "Mesh",
        "流率", "攝氏.*大氣壓",
        "TWA", "STEL", "IDLH",
        "容許暴露標準", "短時間時量", "八小時日時量",
        "採樣後分析", "垂直.*水平.*測定",
        "感知器.*軟泥", "測定點.*垂直",
        "作業環境監測",
        "呼氣閥.*採樣",
    ]),
    # Ch2: Hazard Prevention & PPE — equipment-focused
    ("第2章 缺氧危險場所危害預防及安全衛生防護具", [
        "空氣呼吸器", "輸氣管面罩", "輸氣管面具", "壓縮機式氣",
        "肺力式自攜", "供氣式呼吸防護", "自攜式呼吸",
        "過濾式防毒面罩", "防護衣", "不浸透性防護",
        "防護因數", "PF為",
        "SDS", "安全資料表", "GHS",
        "危害性化學品.*標示", "危害圖示", "化學品.*標示",
        "選購防護具", "個人防護具", "個人防護",
        "防護用品",
    ]),
    # Ch3: Safety Management & Execution — supervisory/procedural keywords
    ("第3章 缺氧危險作業安全衛生管理與執行", [
        "缺氧作業主管", "作業主管.*監督", "監視人員",
        "許可進入", "進入許可", "作業許可",
        "協議組織", "原事業單位.*承攬", "承攬.*原事業單位",
        "自動檢查", "作業檢點",
        "局限空間.*作業", "局限空間.*特徵", "局限空間.*危害預防",
        "缺氧危險作業.*主管",
        "換氣裝置.*確認", "確認.*換氣裝置",
        "進出.*簽名", "點名確認", "進出.*確認",
        "盲板", "關閉.*管閥",
        "作業前.*換氣", "換氣.*作業前",
        "爆炸下限.*換氣",
    ]),
    # Ch6: 缺氧症預防規則 — specific legal requirements & defined places
    ("第6章 缺氧症預防規則", [
        "缺氧症預防規則",
        "氧氣濃度未滿18", "未滿百分之十八", "未滿18%",
        "缺氧危隩作業場所", "缺氧危險場所.*下列",
        "屬缺氧危險", "非屬缺氧危險",
        "乾性油", "保溫棉",
        "連續作業時間.*超過", "不得超過.*小時",
        "5倍.*換氣", "換氣.*5倍",
        "缺氧係指", "純氧.*換氣", "換氣.*純氧",
        "儲槽.*缺氧", "缺氧.*儲槽",
        "缺氧.*何種.*場所", "何種.*場所.*缺氧",
    ]),
    # Ch1: General Laws Overview — fallback for all law/regulation questions
    ("第1章 缺氧危險作業及局限空間作業相關法規概要", [
        ""  # sentinel: always matches (fallback)
    ]),
]

def classify_chapter(text, options_str):
    """Map question to one of 6 course chapters via keyword rules."""
    combined = text + " " + options_str
    for chapter, keywords in CHAPTER_RULES:
        for kw in keywords:
            if kw == "":          # fallback
                return chapter
            if re.search(kw, combined):
                return chapter
    return "第1章 缺氧危險作業及局限空間作業相關法規概要"


def make_q(qid, qtype, text, options, answer, source, section=""):
    # Chapter field: 22200乙級 uses its 工作項目 section; others get keyword-classified
    if source == "22200乙級":
        chapter = section or "22200乙級"
    else:
        chapter = classify_chapter(text, " ".join(options))

    return {
        "id": qid,
        "type": qtype,          # "single" | "truefalse"
        "text": text,
        "options": options,
        "answer": answer,       # 1-based int
        "source": source,
        "section": section,
        "chapter": chapter,
        "isNumeric": is_numeric(text, options) if qtype == "single" else False,
        "isNegative": bool(RE_NEGATIVE.search(text)),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 1: PDF1 — 1090501_缺氧作業主管試題.pdf
# pdfplumber extract_tables() → 3-col rows: [num, answer, question+options]
# ══════════════════════════════════════════════════════════════════════════════
def parse_pdf1():
    import pdfplumber

    pdf_path = BASE / "1090501_缺氧作業主管試題.pdf"
    print(f"[PDF1] {pdf_path.name}")
    questions = []

    RE_OPTS = re.compile(r"[（(]([1-4])[)）]")  # matches （1） or (1)


    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    num_cell   = clean(str(row[0] or ""))
                    ans_cell   = clean(str(row[1] or ""))
                    q_cell     = clean(str(row[2] or "")).replace("", "(1)").replace("", "(2)").replace("", "(3)").replace("", "(4)")

                    # Skip header rows
                    if not re.match(r"^\d+$", num_cell):
                        continue
                    if not re.match(r"^[1-4]$", ans_cell):
                        continue

                    answer = int(ans_cell)

                    # Split question text from options
                    parts = RE_OPTS.split(q_cell)
                    # parts[0] = question text, parts[1]=opt_num, parts[2]=opt_text, ...
                    if len(parts) < 9:
                        # Some rows wrap; try to identify options via (1)...(2)...(3)...(4)
                        pass

                    q_text = clean(parts[0]) if parts else q_cell
                    # Remove trailing question number artifacts
                    q_text = re.sub(r"^\d+\s*", "", q_text)

                    options = []
                    i = 1
                    while i < len(parts) - 1:
                        try:
                            int(parts[i])  # option number
                        except ValueError:
                            i += 1
                            continue
                        opt_text = clean(parts[i + 1])
                        # Remove trailing 。or punctuation
                        opt_text = re.sub(r"[。．\.\s]+$", "", opt_text)
                        options.append(opt_text)
                        i += 2

                    if len(options) < 4:
                        while len(options) < 4:
                            options.append("")

                    if not q_text:
                        continue

                    questions.append((int(num_cell), q_text, options, answer))

    # Sort and deduplicate by num
    seen = set()
    result = []
    for num, text, options, answer in sorted(questions):
        if num not in seen:
            seen.add(num)
            result.append((num, text, options, answer))

    print(f"  Parsed {len(result)} questions")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 2: PDF2 — 222002A13_參考試題.pdf
# Plain text: "N. (answer) question ①opt ②opt ③opt ④opt 。"
# Sections: 工作項目 NN：header
# ══════════════════════════════════════════════════════════════════════════════
def parse_pdf2():
    import pdfplumber

    pdf_path = BASE / "222002A13_參考試題(專業科目193-216題).pdf"
    print(f"[PDF2] {pdf_path.name}")

    # Extract full text
    pages_text = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pages_text.append(t)
    full = "\n".join(pages_text)

    # Remove page markers like "Page N of 68"
    full = re.sub(r"Page \d+ of \d+", "", full)

    # Detect section headers: 工作項目 NN：
    # Hardcode correct names (PDF encoding unreliable)
    SECTION_NAMES = {
        "01": "工作項目01：職業安全衛生相關法規",
        "02": "工作項目02：職業安全衛生計畫與管理",
        "03": "工作項目03：專業科目",
    }
    RE_SECTION = re.compile(r"工作項目\s*(\d+)[：:]")
    section_map = {}   # start_pos → section name
    for m in RE_SECTION.finditer(full):
        num = m.group(1).zfill(2)
        section_map[m.start()] = SECTION_NAMES.get(num, f"工作項目{num}")

    section_starts = sorted(section_map.keys())

    def get_section(pos):
        sec = ""
        for s in section_starts:
            if s <= pos:
                sec = section_map[s]
            else:
                break
        return sec

    # Match question anchors: "N. (answer) text"
    # Answer can be 1-4 digits: "(3)" for single, "(23)" "(124)" for multiple
    RE_Q = re.compile(
        r"^(\d{1,4})\.\s*"           # question number + dot
        r"\(([1-4]{1,4})\)\s*"       # answer in parens (1–4 digits for multi-select)
        r"(.+?)$",                   # question text start
        re.MULTILINE
    )

    # Circle option markers: ① ② ③ ④
    CIRCLE = ["①", "②", "③", "④"]
    RE_CIRCLE = re.compile(r"[①②③④]")

    questions = []
    matches = list(RE_Q.finditer(full))

    for idx, m in enumerate(matches):
        qnum      = int(m.group(1))
        ans_raw   = m.group(2)
        # Single-select: one digit; Multiple-select: 2-4 digits
        if len(ans_raw) == 1:
            answer = int(ans_raw)
            qtype  = "single"
        else:
            answer = sorted([int(c) for c in ans_raw])
            qtype  = "multiple"
        pos     = m.start()
        section = get_section(pos)

        # Collect text from after this match to start of next match
        start = m.end()
        end   = matches[idx + 1].start() if idx + 1 < len(matches) else len(full)
        block = full[start:end].strip()

        # Combine first line + block for full question+options text
        q_first_line = m.group(3).strip()
        full_q = q_first_line + " " + block

        # Find first circle marker anywhere in combined text
        first_circle = RE_CIRCLE.search(full_q)
        if first_circle:
            q_text   = clean(full_q[:first_circle.start()])
            opts_block = full_q[first_circle.start():]
        else:
            q_text   = clean(full_q)
            opts_block = ""

        # Parse circle options: split on ① ② ③ ④
        options = []
        if opts_block:
            parts = RE_CIRCLE.split(opts_block)
            # parts[0] = text before first circle (should be empty), parts[1..4] = option texts
            for p in parts[1:5]:
                opt = clean(p)
                opt = re.sub(r"[。．\s]+$", "", opt)
                opt = re.sub(r"\s*\d+\.\s*$", "", opt)
                options.append(opt)

        if len(options) < 4:
            # Try (1)(2)(3)(4) format
            RE_NUM_OPT = re.compile(r"[（(]([1-4])[)）](.*?)(?=[（(][1-4][)）]|$)", re.DOTALL)
            full_block = q_first_line + " " + block
            num_parts = RE_NUM_OPT.findall(full_block)
            if len(num_parts) >= 4:
                by_num = {}
                for num, txt in num_parts:
                    by_num[int(num)] = clean(re.sub(r"[。．\s]+$", "", txt))
                options = [by_num.get(i, "") for i in range(1, 5)]

        if len(options) < 4:
            while len(options) < 4:
                options.append("")

        # Clean question text
        q_text = re.sub(r"[。．\s]+$", "", q_text)

        if not q_text:
            continue

        questions.append((qnum, q_text, options, answer, section, qtype))

    # Deduplicate by (section, qnum) — each section restarts from Q1
    seen = set()
    result = []
    for row in sorted(questions, key=lambda x: (x[4], x[0])):
        key = (row[4], row[0])
        if key not in seen:
            seen.add(key)
            result.append(row)

    print(f"  Parsed {len(result)} questions")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 3: DOCX — 參考試題2021.docx
# 33 two-column tables: col0 = "N、（answer）", col1 = question + ○1○2○3○4
# ══════════════════════════════════════════════════════════════════════════════
def parse_docx():
    from docx import Document

    docx_path = BASE / "參考試題－缺氧作業主管（2021.06.22）陳建仁 黃榮鴻.docx"
    print(f"[DOCX] {docx_path.name}")

    doc = Document(str(docx_path))

    # Circle option markers ○1 ○2 ○3 ○4 (full-width and half-width)
    RE_CIRCLE_OPT = re.compile(r"[○◯]\s*([1-4])")

    questions = []
    q_counter = 0

    for table in doc.tables:
        for row in table.rows:
            cells = row.cells
            if len(cells) < 2:
                continue
            col0 = clean(cells[0].text)
            col1 = clean(cells[1].text)

            if not col0 or not col1:
                continue

            # col0: "N、（answer）" or "N.（answer）"
            m = re.match(r"(\d+)[、．.]\s*[（(]([1-4])[)）]", col0)
            if not m:
                continue

            qnum   = int(m.group(1))
            answer = int(m.group(2))

            # col1: question text + options separated by ○1 ○2 ○3 ○4
            parts = RE_CIRCLE_OPT.split(col1)
            # parts[0] = question text, parts[1]=opt_num, parts[2]=opt_text, ...
            q_text = clean(parts[0])
            options = []
            i = 1
            while i < len(parts) - 1:
                try:
                    opt_num = int(parts[i])
                except ValueError:
                    i += 1
                    continue
                opt_text = clean(parts[i + 1])
                opt_text = re.sub(r"[。．\s]+$", "", opt_text)
                options.append(opt_text)
                i += 2

            if len(options) < 4:
                # Try alternate: options with （1）（2）（3）（4）
                RE_FULL_OPT = re.compile(r"[（(]([1-4])[)）](.*?)(?=[（(][1-4][)）]|$)", re.DOTALL)
                full_parts = RE_FULL_OPT.findall(col1)
                if len(full_parts) >= 4:
                    by_num = {}
                    for num, txt in full_parts:
                        by_num[int(num)] = clean(re.sub(r"[。．\s]+$", "", txt))
                    # Re-extract question text as text before first option
                    first_m = RE_FULL_OPT.search(col1)
                    if first_m:
                        q_text = clean(col1[:first_m.start()])
                    options = [by_num.get(i, "") for i in range(1, 5)]

            if len(options) < 4:
                while len(options) < 4:
                    options.append("")

            if not q_text:
                continue

            questions.append((qnum, q_text, options, answer))

    # Sort and deduplicate
    seen = set()
    result = []
    for row in sorted(questions):
        if row[0] not in seen:
            seen.add(row[0])
            result.append(row)

    print(f"  Parsed {len(result)} questions")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE 4: DOC — 複習測驗題.doc
# Parse from existing doc_content.txt (raw text dump via win32com)
#
# Structure (split by \x07):
#   Parts 0-99   → T/F section 1  (25 questions × 4 parts each)
#   Parts 100-199 → MC section 1  (25 questions × 4 parts each)
#   Part 200      → remaining text: T/F section 2 + MC section 2 + MC section 3
#
# T/F part pattern: [answer_marker]\n, [NN]\n, [question text]\n, [empty]\n
# MC part pattern:  [answer_marker]\n, [NN]\n, [question+options text]\n, [empty]\n
# ══════════════════════════════════════════════════════════════════════════════
def _parse_mc_options(text):
    """Extract question text and 4 options from a raw text block.
    Handles two formats:
      Format B: question(1)opt1(2)opt2(3)opt3(4)opt4
      Format A: question(opt1(opt2(opt3(opt4
    Returns (q_text, [opt1, opt2, opt3, opt4])
    """
    # Try Format B: numbered options (1)(2)(3)(4) or （1）（2）（3）（4）
    RE_B = re.compile(r"[（(]\s*([1-4])\s*[)）](.*?)(?=[（(]\s*[1-4]\s*[)）]|$)", re.DOTALL)
    b_parts = RE_B.findall(text)
    if len(b_parts) >= 4:
        by_num = {}
        for n, t in b_parts:
            if int(n) not in by_num:
                by_num[int(n)] = clean(re.sub(r"[。．\s]+$", "", t))
        first_opt = RE_B.search(text)
        q_text = clean(text[:first_opt.start()]) if first_opt else ""
        options = [by_num.get(i, "") for i in range(1, 5)]
        while len(options) < 4:
            options.append("")
        return q_text, options

    # Format A: split on bare ( characters
    # Question text is before the first ( that's not part of question punctuation
    # Find where options start: look for the last stretch of (text( patterns
    paren_positions = [i for i, c in enumerate(text) if c == "("]
    if len(paren_positions) >= 4:
        # Options start at the 4th-from-last paren
        opt_start = paren_positions[-4]
        q_text = clean(text[:opt_start])
        opts_raw = text[opt_start:]
        # Split on ( and take first 4 non-empty parts
        opt_parts = [p.strip() for p in opts_raw.split("(") if p.strip()]
        options = []
        for p in opt_parts[:8]:  # take up to 8, pick valid ones
            opt = clean(re.sub(r"[。．\s]+$", "", p))
            if opt:
                options.append(opt)
            if len(options) == 4:
                break
        while len(options) < 4:
            options.append("")
        return q_text, options

    # Fallback: whole text is question, no options
    return clean(text), ["", "", "", ""]


def parse_doc():
    doc_txt = BASE / "doc_content.txt"
    print(f"[DOC] {doc_txt.name}")

    text = doc_txt.read_text(encoding="utf-8")
    parts = text.split("\x07")

    questions = []

    # ── T/F SECTION 1 (parts 0-99): groups of 4 ───────────────────────────
    # Pattern per group: marker_part, number_part, text_part, empty_part
    TF_MARKERS = {
        "(()": 1, "(○)": 1, "( O )": 1,
        "(Χ)": 2, "(×)": 2, "( X )": 2,
    }
    RE_TF_MARKER = re.compile(r"\(+([()○Χ×OXox]+)\)+")

    tf1_count = 0
    i = 0
    while i < min(100, len(parts)):
        part = parts[i].strip()
        # Skip non-answer-marker parts
        # Answer markers look like: "(()  " or "(Χ)" possibly prefixed by section titles
        m = re.search(r"\(\s*([()○Χ×OXox]+)\s*\)\s*$", part)
        if not m:
            i += 1
            continue
        marker = m.group(1).strip()
        # Determine answer
        if marker in ("(", "○", "O", "o"):
            answer = 1
        elif marker in ("Χ", "X", "×", "χ", "x"):
            answer = 2
        else:
            i += 1
            continue
        # Next part is question number, then question text
        if i + 2 >= len(parts):
            break
        qnum_raw = parts[i + 1].strip()
        qtext_raw = parts[i + 2].strip()
        try:
            qnum = int(re.sub(r"\D", "", qnum_raw))
        except ValueError:
            i += 1
            continue
        qtext = clean(qtext_raw).rstrip("。")
        if qtext and qnum and qnum <= 30:
            questions.append(("truefalse", qtext, ["○正確", "✕錯誤"], answer, "是非題一"))
            tf1_count += 1
        i += 4  # skip the 4 parts of this question

    print(f"  T/F section 1: {tf1_count} questions")

    # ── MC SECTION 1 (parts ~100-199): same 4-part structure ──────────────
    # Answer markers: (N) or (N）
    RE_MC_MARKER = re.compile(r"^\s*\(?([1-4])[)）]\s*$")

    mc1_count = 0
    i = 100
    while i < min(200, len(parts)):
        part = parts[i].strip()
        # Extract answer from last line if part has header like "二、選擇題\n(3)"
        lines = [l.strip() for l in part.split("\n") if l.strip()]
        marker_line = lines[-1] if lines else ""
        m = re.match(r"^\(?([1-4])[)）]\s*$", marker_line)
        if not m:
            i += 1
            continue
        answer = int(m.group(1))
        if i + 2 >= len(parts):
            break
        qnum_raw = parts[i + 1].strip()
        qblock   = parts[i + 2].strip()
        try:
            qnum = int(re.sub(r"\D", "", qnum_raw))
        except ValueError:
            i += 1
            continue
        if not qblock or qnum > 30:
            i += 4
            continue

        q_text, options = _parse_mc_options(qblock)
        if q_text:
            questions.append(("single", q_text, options, answer, "選擇題一"))
            mc1_count += 1
        i += 4

    print(f"  MC section 1: {mc1_count} questions")

    # ── REMAINING TEXT (part 200): T/F section 2 + MC sections 2 & 3 ──────
    tail = parts[200] if len(parts) > 200 else ""

    # Find the boundaries
    tf2_marker = "一、是非題"
    mc2_marker  = "二、選擇題"  # may not exist; use heuristic instead

    tf2_start = tail.find(tf2_marker)
    if tf2_start == -1:
        tf2_start = tail.find("( O )")
    # MC section 2 starts after T/F block 2
    # Find "( 1 )缺氧是指" as first MC2 question
    mc2_start = tail.find("( 1 )缺氧是指")
    if mc2_start == -1:
        mc2_start = tail.find("( 1 )")
    # MC section 3 starts with numbered format (N)N.
    mc3_start = tail.find("(1)1.")
    if mc3_start == -1:
        mc3_start = len(tail)

    # T/F Section 2
    tf2_block = tail[tf2_start:mc2_start] if 0 <= tf2_start < mc2_start else ""
    RE_TF2 = re.compile(r"\(\s*([OX○×Χ])\s*\)(.*?)(?=\(\s*[OX○×Χ]\s*\)|$)", re.DOTALL)
    tf2_count = 0
    for m in RE_TF2.finditer(tf2_block):
        marker = m.group(1).strip()
        qtext  = clean(m.group(2)).rstrip("。。.\n")
        if not qtext or len(qtext) < 3:
            continue
        answer = 1 if marker in ("O", "○") else 2
        questions.append(("truefalse", qtext, ["○正確", "✕錯誤"], answer, "是非題二"))
        tf2_count += 1
    print(f"  T/F section 2: {tf2_count} questions")

    # MC Section 2: ( N ) format, each question ends with 。 then next ( N )
    mc2_block = tail[mc2_start:mc3_start] if 0 <= mc2_start < mc3_start else ""

    # Split on sentence boundary + answer marker
    # Strategy: split on 。 and reattach if next chunk starts with ( N )
    RE_MC2_Q = re.compile(
        r"\(\s*([1-4])\s*\)"          # answer marker (with spaces)
        r"(.*?)"                       # question text
        r"\(1\)(.*?)\(2\)(.*?)\(3\)(.*?)\(4\)(.*?)"  # 4 options
        r"(?=[。。]|\Z)",              # ends with period
        re.DOTALL
    )
    mc2_count = 0
    for m in RE_MC2_Q.finditer(mc2_block):
        answer  = int(m.group(1))
        q_text  = clean(m.group(2))
        options = [
            clean(re.sub(r"[。。\s]+$", "", m.group(3))),
            clean(re.sub(r"[。。\s]+$", "", m.group(4))),
            clean(re.sub(r"[。。\s]+$", "", m.group(5))),
            clean(re.sub(r"[。。\s]+$", "", m.group(6))),
        ]
        if not q_text:
            continue
        questions.append(("single", q_text, options, answer, "選擇題二"))
        mc2_count += 1

    # Also try bare-( format for MC2 questions that don't have (1)(2)(3)(4)
    # (questions like "( 4 )缺氧作業主管(1)每班次...(4)以上皆是")
    # The above regex should catch numbered ones; for bare-( try separately
    RE_MC2_BARE = re.compile(
        r"\(\s*([1-4])\s*\)"   # answer marker with spaces
        r"([^(]{5,}?)"         # question text (at least 5 chars, no parens)
        r"((?:\([^(]{1,50}\)){4,})"  # 4+ options as (text)
        r"[。。]?",
        re.DOTALL
    )
    # Skip for now - numbered format covers most cases
    print(f"  MC section 2: {mc2_count} questions")

    # MC Section 3: (N)N. numbered questions
    mc3_block = tail[mc3_start:] if mc3_start < len(tail) else ""
    RE_MC3 = re.compile(r"\(([1-4])\)(\d{1,2})\.(.*?)(?=\([1-4]\)\d{1,2}\.|\Z)", re.DOTALL)
    mc3_count = 0
    seen_mc3 = set()
    for m in RE_MC3.finditer(mc3_block):
        answer = int(m.group(1))
        qnum   = int(m.group(2))
        block  = m.group(3).strip()
        if qnum in seen_mc3:
            continue
        q_text, options = _parse_mc_options(block)
        if not q_text or len(q_text) < 3:
            continue
        seen_mc3.add(qnum)
        questions.append(("single", q_text, options, answer, "選擇題三"))
        mc3_count += 1
    print(f"  MC section 3: {mc3_count} questions")

    return questions


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    all_questions = []
    qid = 1

    # --- SOURCE 1: PDF1 ---
    try:
        pdf1 = parse_pdf1()
        for num, text, options, answer in pdf1:
            all_questions.append(make_q(
                qid, "single", text, options, answer,
                source="1090501練習題", section=""
            ))
            qid += 1
    except Exception as e:
        print(f"  ERROR in PDF1: {e}")

    # --- SOURCE 2: PDF2 ---
    try:
        pdf2 = parse_pdf2()
        for row in pdf2:
            qnum, text, options, answer, section, qtype = row
            all_questions.append(make_q(
                qid, qtype, text, options, answer,
                source="22200乙級", section=section
            ))
            qid += 1
    except Exception as e:
        print(f"  ERROR in PDF2: {e}")
        import traceback; traceback.print_exc()

    # --- SOURCE 3: DOCX ---
    try:
        docx = parse_docx()
        for num, text, options, answer in docx:
            all_questions.append(make_q(
                qid, "single", text, options, answer,
                source="2021參考試題", section=""
            ))
            qid += 1
    except Exception as e:
        print(f"  ERROR in DOCX: {e}")
        import traceback; traceback.print_exc()

    # --- SOURCE 4: DOC ---
    try:
        doc = parse_doc()
        for qtype, text, options, answer, section in doc:
            all_questions.append(make_q(
                qid, qtype, text, options, answer,
                source="複習測驗題", section=section
            ))
            qid += 1
    except Exception as e:
        print(f"  ERROR in DOC: {e}")
        import traceback; traceback.print_exc()

    # Filter out incomplete single questions (fewer than 2 non-empty options)
    before = len(all_questions)
    all_questions = [
        q for q in all_questions
        if q["type"] == "truefalse"
        or sum(1 for o in q["options"] if o.strip()) >= 2
    ]
    dropped = before - len(all_questions)
    if dropped:
        print(f"  Dropped {dropped} incomplete questions")

    # Save
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Total: {len(all_questions)} questions saved to {OUT}")

    # Stats
    from collections import Counter
    src_counts = Counter(q["source"] for q in all_questions)
    type_counts = Counter(q["type"] for q in all_questions)
    for src, cnt in sorted(src_counts.items()):
        print(f"  {src}: {cnt}")
    print(f"  single: {type_counts['single']}, truefalse: {type_counts['truefalse']}")
    print(f"  numeric: {sum(1 for q in all_questions if q.get('isNumeric'))}")
    print(f"  negative: {sum(1 for q in all_questions if q.get('isNegative'))}")


if __name__ == "__main__":
    main()
