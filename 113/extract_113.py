#!/usr/bin/env python3
"""
Scrape 113年職業安全衛生業務主管 (471題) from yamol.tw
Uses Playwright with existing Chrome profile (already logged in).
"""

import json, re, time
from pathlib import Path
from playwright.sync_api import sync_playwright

# ── Chapter list ──────────────────────────────────────────────────────────────
CHAPTERS = [
    (119816, "第一章 企業經營風險與安全衛生"),
    (119817, "第二章 職業安全衛生相關法規"),
    (119818, "第三章 職業安全衛生概論"),
    (119819, "第四章 職業安全衛生管理系統介紹"),
    (119820, "第五章 風險評估"),
    (119821, "第六章 承攬管理"),
    (119822, "第七章 採購及變更管理"),
    (119823, "第八章 緊急應變管理"),
    (119824, "第九章 墜落危害預防管理實務"),
    (119825, "第十章 機械安全管理實務"),
    (119826, "第十一章 火災爆炸危害預防管理實務"),
    (119827, "第十二章 感電危害預防管理實務"),
    (119828, "第十三章 倒塌崩塌危害預防管理實務"),
    (119829, "第十四章 化學性危害預防管理實務"),
    (119831, "第十五章 物理性危害預防管理實務"),
    (119832, "第十六章 職場健康管理實務"),
    (119833, "第十七章 職業災害調查處理與統計"),
]

# Chrome profile path (already logged in to yamol.tw)
CHROME_PROFILE = r"C:\Users\USER\AppData\Local\Google\Chrome\User Data"

# ── Text cleaning ─────────────────────────────────────────────────────────────
def clean(s):
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ── Parse chapter page text ───────────────────────────────────────────────────
def parse_chapter(text, chapter_name, start_id):
    """
    Parse innerText of a yamol exam page.
    Format per question:
      第 N 題
      難度
      N.Question text
      (A)Option A
      (B)Option B
      (C)Option C
      (D)Option D
      尚未作答
      答案：
      X         ← answer letter
      查看詳細解析
    """
    questions = []

    # Split by "第 N 題" markers
    blocks = re.split(r"第\s*\d+\s*題", text)
    blocks = [b.strip() for b in blocks if b.strip()]

    # Regex for numeric detection (金庫密碼)
    RE_NUM = re.compile(
        r"\d+[\s]*(年|月|日|小時|分鐘|公尺|公分|毫米|公斤|噸|人|萬|度|倍|%|cm|m|kg|hr|min"
        r"|伏特|安培|瓦特|歐姆|赫茲|毫安|千伏|千瓦|燭光|勒克斯|分貝"
        r"|kV|kW|kA|mA|Hz|Ω|lux|lm|dB|V(?!\w)|W(?!\w)|A(?!\w))"
        r"|[一二三四五六七八九十百千]+[\s]*(年|個月|小時|公尺|公分|人|倍|日)",
        re.IGNORECASE
    )
    # Regex for negative questions (反向題)
    RE_NEGATIVE = re.compile(
        r"何者.{0,10}(?:非(?!常)|為非|不是|不正確|有誤|錯誤|不符合|不屬於|不包括|不適當|不適用|不為(?!了|何))"
        r"|何項.{0,10}(?:不正確|有誤|錯誤|不符合|不為|不適用|不是)"
        r"|何種.{0,10}(?:不正確|有誤|錯誤|不符合|不適用|不是)"
        r"|何者.{0,6}[「\"](?:非|不)[」\"]"
        r"|下列.{0,20}(?:有誤|不正確|錯誤的|不符合|非正確|不是)"
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

    q_id = start_id

    for block in blocks:
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if not lines:
            continue

        # Find question text line. Handles multiple formats:
        #   "31.Question"   "31 .Question"  (dot present, any char after)
        #   "11Question"                    (no dot, directly non-digit/non-space)
        # Does NOT match "1." alone (page header link) or numbers inside sentences.
        q_line_idx = None
        for i, l in enumerate(lines):
            # Case 1: has dot separator (allows digit after dot, e.g. "8.11400伏特...")
            # Case 2: no dot, digit immediately followed by non-digit/non-space (e.g. "11職業...")
            if re.match(r"^\d+\s*[\.。]\s*\S", l) or re.match(r"^\d+[^\d\s\.]", l):
                q_line_idx = i
                break
        if q_line_idx is None:
            continue

        # Check if this is a 複選題 (multiple-answer) block
        is_multiple = any("複選題" in l for l in lines)

        # Question text (may span multiple lines until first option)
        q_text_parts = []
        opt_start = q_line_idx
        for i in range(q_line_idx, len(lines)):
            if re.match(r"^\([ABCD]\)", lines[i]):
                opt_start = i
                break
            q_text_parts.append(lines[i])

        q_text = clean(" ".join(q_text_parts))
        # Remove leading "N.", "N .", or "N" numbering prefix
        q_text = re.sub(r"^\d+\s*[\.。]?\s*", "", q_text)

        if not q_text:
            continue

        # Extract 4 options
        options = []
        for i in range(opt_start, len(lines)):
            m = re.match(r"^\(([ABCD])\)(.*)", lines[i])
            if m:
                opt_text = clean(m.group(2))
                # Merge next line if it doesn't start with option/answer marker
                j = i + 1
                while j < len(lines) and not re.match(r"^\([ABCD]\)|^尚未作答|^答案", lines[j]):
                    opt_text = clean(opt_text + " " + lines[j])
                    j += 1
                options.append(opt_text)
            if len(options) == 4:
                break

        if len(options) < 4:
            # Some questions have fewer visible options - pad
            while len(options) < 4:
                options.append("（詳見原題）")

        # Extract answer: line immediately after "答案："
        # Supports single (A) and multiple (A,B,C) answers
        answer_raw = None
        for i, l in enumerate(lines):
            if l.startswith("答案"):
                for j in range(i + 1, min(i + 4, len(lines))):
                    stripped = lines[j].strip()
                    if re.match(r"^[ABCD](,[ABCD])*$", stripped):
                        answer_raw = stripped
                        break
                break

        if not answer_raw:
            print(f"  WARNING: no answer found in block, skipping")
            continue

        letter_map = {"A": 1, "B": 2, "C": 3, "D": 4}

        if "," in answer_raw:
            # Multiple-answer question: store all answer numbers as list
            answer_nums = [letter_map[c] for c in answer_raw.split(",") if c in letter_map]
            answer_val = answer_nums  # list e.g. [1, 2, 3]
        else:
            answer_val = letter_map[answer_raw]  # int

        # Numeric detection
        all_text = q_text + " " + " ".join(options)
        is_numeric = bool(RE_NUM.search(all_text)) or bool(
            re.search(r"[一二三四五六七八九]、[一二三四五六七八九]、", all_text)
        )
        # Also flag when options are bare numbers (unit is implied in question text)
        # e.g. options "1", "3", "6", "12" where question asks "幾個月"
        if not is_numeric:
            # Bare numbers with ≤4 digits: "7", "30", "3000" = quantity questions
            # Excludes 5-digit sequences like "24153" (排列順序題)
            bare = sum(1 for opt in options if re.match(r"^\d{1,4}\s*(以上|以下|以內)?$", opt.strip()))
            is_numeric = bare >= 2

        questions.append({
            "id": q_id,
            "text": q_text,
            "options": options,
            "answer": answer_val,
            "chapter": chapter_name,
            "isNumeric": is_numeric,
            "isMultiple": is_multiple,
            "isNegative": bool(RE_NEGATIVE.search(q_text)),
        })
        q_id += 1

    return questions, q_id


# ── Main scraper ──────────────────────────────────────────────────────────────
def main():
    all_questions = []
    q_id = 1

    with sync_playwright() as p:
        print("Launching headless browser (no login required)...")
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = ctx.new_page()

        for exam_id, chapter_name in CHAPTERS:
            url = f"https://yamol.tw/exam/{exam_id}"
            print(f"\n[{chapter_name}] {url}")

            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for questions to render (look for "第 1 題" text)
            try:
                page.wait_for_selector("text=第 1 題", timeout=15000)
            except Exception:
                print("  WARNING: timed out waiting for questions, trying anyway...")
            time.sleep(2)  # extra settle time

            # Scroll to bottom to ensure all questions are loaded
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(0.5)

            # Extract full page text
            text = page.inner_text("body")

            # Check if answer is visible
            if "答案：" not in text:
                print("  ERROR: answers not visible (login required?)")
                continue

            qs, q_id = parse_chapter(text, chapter_name, q_id)
            print(f"  Parsed {len(qs)} questions")
            all_questions.extend(qs)

        ctx.close()
        browser.close()

    # Save
    out = Path(__file__).parent / "questions.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Total: {len(all_questions)} questions saved to {out}")

    # Stats
    from collections import Counter
    counts = Counter(q["chapter"] for q in all_questions)
    for ch, cnt in sorted(counts.items()):
        ch_safe = ch.encode('ascii', errors='replace').decode('ascii')
        print(f"  {ch_safe}: {cnt}")
    print(f"  [numeric] {sum(1 for q in all_questions if q['isNumeric'])} questions")


if __name__ == "__main__":
    main()
