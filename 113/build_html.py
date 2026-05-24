#!/usr/bin/env python3
"""Build 113/index.html from 113/questions.json."""

import json
from collections import Counter

with open("questions.json", encoding="utf-8") as f:
    questions = json.load(f)

js_data = json.dumps(questions, ensure_ascii=False, separators=(",", ":"))

chapter_counts = Counter(q["chapter"] for q in questions)
numeric_count = sum(1 for q in questions if q["isNumeric"])
multiple_count = sum(1 for q in questions if q.get("isMultiple"))
total = len(questions)

# Chapters in order (matching CHAPTERS list)
CHAPTERS_ORDER = [
    "第一章 企業經營風險與安全衛生",
    "第二章 職業安全衛生相關法規",
    "第三章 職業安全衛生概論",
    "第四章 職業安全衛生管理系統介紹",
    "第五章 風險評估",
    "第六章 承攬管理",
    "第七章 採購及變更管理",
    "第八章 緊急應變管理",
    "第九章 墜落危害預防管理實務",
    "第十章 機械安全管理實務",
    "第十一章 火災爆炸危害預防管理實務",
    "第十二章 感電危害預防管理實務",
    "第十三章 倒塌崩塌危害預防管理實務",
    "第十四章 化學性危害預防管理實務",
    "第十五章 物理性危害預防管理實務",
    "第十六章 職場健康管理實務",
    "第十七章 職業災害調查處理與統計",
]

# Build dropdown options
def make_options_html():
    lines = []
    lines.append(f'<option value="全部">全部（{total} 題）</option>\n')
    lines.append('<option value="未完成" id="opt-incomplete">📝 未完成</option>\n')
    lines.append('<option value="錯題本" id="opt-wrong">⭐ 我的錯題本</option>\n')
    lines.append(f'<option value="金庫密碼">🔢 金庫密碼（{numeric_count} 題）</option>\n')
    lines.append(f'<option value="複選題">☑ 複選題（{multiple_count} 題）</option>\n')
    lines.append('<optgroup label="── 依章節 ──">\n')
    for ch in CHAPTERS_ORDER:
        cnt = chapter_counts.get(ch, 0)
        # Short label: strip prefix number
        short = ch
        lines.append(f'<option value="{ch}">{short}（{cnt} 題）</option>\n')
    lines.append('</optgroup>\n')
    return "".join(lines)

options_html = make_options_html()

HTML = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>營造業丙種職業安全衛生業務主管題庫【113年版精選471題】</title>
<style>
/* ── Reset & Base ─────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 16px; scroll-behavior: smooth; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Noto Sans TC", "PingFang TC",
    "Microsoft JhengHei", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  transition: background .25s, color .25s;
}}

/* ── Color tokens ─────────────────────────────────── */
:root {{
  --bg: #f4f6f9;
  --surface: #ffffff;
  --surface2: #f0f2f5;
  --border: #dde1e7;
  --text: #1a1a2e;
  --text2: #5a6272;
  --primary: #2e7d32;
  --primary-dark: #1b5e20;
  --correct: #0f7a42;
  --correct-bg: #d4edda;
  --wrong: #c0392b;
  --wrong-bg: #fde8e6;
  --wrong-border: #e74c3c;
  --tag-bg: #e8f5e9;
  --tag-color: #2e7d32;
  --progress-track: #e0e5ec;
  --progress-fill: #2e7d32;
  --progress-done: #0f7a42;
  --shadow: 0 2px 8px rgba(0,0,0,.08);
  --radius: 12px;
}}
[data-theme="dark"] {{
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #22263a;
  --border: #2e3347;
  --text: #e8eaf0;
  --text2: #8a91a8;
  --primary: #66bb6a;
  --primary-dark: #4caf50;
  --correct: #2ecc71;
  --correct-bg: #0d3320;
  --wrong: #e74c3c;
  --wrong-bg: #3d1212;
  --wrong-border: #e74c3c;
  --tag-bg: #1a2d1e;
  --tag-color: #66bb6a;
  --progress-track: #22263a;
  --progress-fill: #66bb6a;
  --progress-done: #2ecc71;
  --shadow: 0 2px 8px rgba(0,0,0,.35);
}}

/* ── Site nav ─────────────────────────────────────── */
.site-nav {{
  background: var(--primary-dark);
  padding: 4px 16px;
  display: flex; gap: 4px; align-items: center;
  font-size: .76rem;
}}
.site-nav a, .site-nav .cur {{
  color: rgba(255,255,255,.75);
  text-decoration: none;
  padding: 2px 8px; border-radius: 4px;
  white-space: nowrap;
}}
.site-nav a:hover {{ color: #fff; background: rgba(255,255,255,.15); }}
.site-nav .cur {{ color: #fff; font-weight: 700; background: rgba(255,255,255,.2); }}
.site-nav .sep {{ color: rgba(255,255,255,.3); }}

/* ── Sticky top wrapper ───────────────────────────── */
.sticky-top {{
  position: sticky; top: 0; z-index: 100;
}}

/* ── Header ───────────────────────────────────────── */
header {{
  background: var(--primary);
  color: #fff;
  padding: 12px 16px;
  display: flex; align-items: center; gap: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,.2);
}}
header h1 {{
  font-size: 1rem; font-weight: 700; flex: 1;
  line-height: 1.3;
}}
header h1 small {{
  font-size: .72rem; font-weight: 400; opacity: .8;
  white-space: nowrap;
}}
#theme-btn {{
  background: rgba(255,255,255,.2); border: none;
  border-radius: 8px; padding: 6px 10px;
  cursor: pointer; color: #fff; font-size: 1.1rem;
  transition: background .2s;
}}
#theme-btn:hover {{ background: rgba(255,255,255,.35); }}

/* ── Progress bar ─────────────────────────────────── */
.progress-section {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 8px 16px 10px;
  box-shadow: 0 2px 6px rgba(0,0,0,.08);
}}
.progress-meta {{
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 5px;
}}
.progress-label {{
  font-size: .82rem; font-weight: 600; color: var(--text2);
}}
.accuracy-label {{
  font-size: .82rem; font-weight: 700; color: var(--correct);
}}
.progress-pct {{
  font-size: .82rem; font-weight: 700; color: var(--primary);
  transition: color .4s;
}}
.progress-pct.done {{ color: var(--correct); }}
.progress-track {{
  height: 8px; border-radius: 99px;
  background: var(--progress-track);
  overflow: hidden;
}}
.progress-fill {{
  height: 100%; border-radius: 99px;
  background: var(--progress-fill);
  width: 0%;
  transition: width .4s ease, background .4s;
}}
.progress-fill.done {{ background: var(--progress-done); }}

/* ── Controls ─────────────────────────────────────── */
.controls {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 10px 16px;
  display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
}}
.controls select, .controls input {{
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: .95rem;
  background: var(--surface2);
  color: var(--text);
  outline: none;
  transition: border-color .2s;
}}
.controls select:focus, .controls input:focus {{ border-color: var(--primary); }}
#ch-select {{ flex: 0 0 auto; max-width: 100%; }}
#search-input {{ flex: 1; min-width: 160px; }}
#stats {{
  font-size: .82rem; color: var(--text2);
  white-space: nowrap;
}}
#clear-wrong-btn {{
  font-size: .8rem; padding: 6px 10px;
  background: var(--wrong-bg); color: var(--wrong);
  border: 1px solid var(--wrong-border); border-radius: 8px;
  cursor: pointer; display: none;
}}
#clear-wrong-btn:hover {{ opacity: .85; }}
#reset-progress-btn {{
  font-size: .8rem; padding: 6px 10px;
  background: var(--surface2); color: var(--text2);
  border: 1px solid var(--border); border-radius: 8px;
  cursor: pointer;
}}
#reset-progress-btn:hover {{ border-color: var(--primary); color: var(--primary); }}
#export-btn, #import-btn {{
  font-size: .8rem; padding: 6px 10px;
  background: var(--surface2); color: var(--text2);
  border: 1px solid var(--border); border-radius: 8px;
  cursor: pointer;
}}
#export-btn:hover {{ border-color: #0f7a42; color: #0f7a42; }}
#import-btn:hover {{ border-color: var(--primary); color: var(--primary); }}

/* ── Main grid ────────────────────────────────────── */
main {{
  max-width: 1300px; margin: 0 auto;
  padding: 16px 16px 60px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}}
@media (min-width: 1024px) {{
  main {{ grid-template-columns: 1fr 1fr; }}
}}

/* ── Question card ────────────────────────────────── */
.card {{
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1.5px solid var(--border);
  border-left: 4px solid var(--border);
  padding: 16px;
  display: flex; flex-direction: column; gap: 10px;
  transition: border-color .2s, box-shadow .2s;
  position: relative;
}}
.card.was-wrong {{ border-left-color: var(--wrong-border); }}
.card.answered-ok {{ border-left-color: var(--correct); }}
.card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.12); }}

.card-header {{
  display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;
}}
.q-num {{
  font-weight: 700; color: var(--primary); font-size: .9rem;
  white-space: nowrap; margin-top: 2px;
}}
.ch-tag {{
  font-size: .72rem; font-weight: 600;
  background: var(--tag-bg); color: var(--tag-color);
  padding: 2px 7px; border-radius: 20px;
  white-space: nowrap; line-height: 1.6;
  max-width: 160px; overflow: hidden; text-overflow: ellipsis;
}}
.ch-tag.numeric {{ background: #fff3e0; color: #e65100; }}
.ch-tag.multiple {{ background: #e8eaf6; color: #3949ab; }}

.q-text {{
  font-size: 1rem; font-weight: 500; color: var(--text);
  line-height: 1.55;
}}

/* Options */
.options {{ display: flex; flex-direction: column; gap: 7px; }}
.opt-btn {{
  width: 100%; text-align: left;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1.5px solid var(--border);
  background: var(--surface2);
  color: var(--text);
  font-size: .93rem; cursor: pointer;
  transition: background .15s, border-color .15s, transform .1s;
  line-height: 1.5;
  min-height: 44px;
}}
.opt-btn:hover:not(:disabled) {{
  background: var(--tag-bg); border-color: var(--primary);
  transform: translateX(2px);
}}
.opt-btn:disabled {{ cursor: default; }}
.opt-btn.correct {{
  background: var(--correct-bg); border-color: var(--correct); color: var(--correct);
  font-weight: 600;
}}
.opt-btn.wrong {{
  background: var(--wrong-bg); border-color: var(--wrong); color: var(--wrong);
}}
/* 反向題：正確答案 = 唯一錯誤選項，黃底刪除線 */
.opt-btn.correct-neg {{
  background: #fffde7; border-color: #f9a825; color: #5d4037;
  font-weight: 600;
  text-decoration: line-through;
  text-decoration-color: #e65100;
  text-decoration-thickness: 2px;
}}
[data-theme="dark"] .opt-btn.correct-neg {{
  background: #3e2f00; border-color: #f9a825; color: #ffe082;
  text-decoration-color: #ffb300;
}}

/* Result row */
.result-row {{
  display: none; align-items: center; gap: 8px;
  padding: 8px 12px; border-radius: 8px;
  font-size: .9rem; font-weight: 600;
  flex-wrap: wrap;
}}
.result-row.show {{ display: flex; }}
.result-row.ok {{ background: var(--correct-bg); color: var(--correct); }}
.result-row.ok.neg {{ background: #fffde7; color: #e65100; }}
[data-theme="dark"] .result-row.ok.neg {{ background: #3e2f00; color: #ffb300; }}
.result-row.bad {{ background: var(--wrong-bg); color: var(--wrong); }}
.result-row.multi {{ background: #e8eaf6; color: #3949ab; }}

/* ── Multiple-select: checkboxes + submit ──────────── */
.multi-options {{ display: flex; flex-direction: column; gap: 7px; }}
.multi-btn {{
  width: 100%; text-align: left;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1.5px solid var(--border);
  background: var(--surface2);
  color: var(--text);
  font-size: .93rem; cursor: pointer;
  transition: background .15s, border-color .15s;
  line-height: 1.5; min-height: 44px;
  display: flex; align-items: center; gap: 8px;
  position: relative;
}}
.multi-btn::before {{
  content: '';
  width: 18px; height: 18px; flex-shrink: 0;
  border-radius: 4px;
  border: 1.5px solid var(--border);
  background: var(--surface);
  transition: background .15s, border-color .15s;
}}
.multi-btn.selected {{ border-color: var(--primary); background: var(--tag-bg); }}
.multi-btn.selected::before {{ background: var(--primary); border-color: var(--primary); box-shadow: inset 0 0 0 3px #fff; }}
.multi-btn:hover:not(:disabled) {{ border-color: var(--primary); background: var(--tag-bg); }}
.multi-btn:disabled {{ cursor: default; }}
.multi-btn.correct {{ background: var(--correct-bg); border-color: var(--correct); color: var(--correct); font-weight: 600; }}
.multi-btn.correct::before {{ background: var(--correct); border-color: var(--correct); box-shadow: inset 0 0 0 3px #fff; }}
.multi-btn.wrong {{ background: var(--wrong-bg); border-color: var(--wrong); color: var(--wrong); }}
.multi-btn.wrong::before {{ background: var(--wrong); border-color: var(--wrong); box-shadow: inset 0 0 0 3px #fff; }}
.multi-btn.missed {{ background: var(--correct-bg); border-color: var(--correct); color: var(--correct); font-weight: 600; opacity: .7; }}
.multi-btn.missed::before {{ background: var(--correct); border-color: var(--correct); box-shadow: inset 0 0 0 3px #fff; }}
.multi-submit {{
  margin-top: 4px; padding: 9px 18px;
  border-radius: 8px; border: none;
  background: var(--primary); color: #fff;
  font-size: .9rem; font-weight: 600; cursor: pointer;
  transition: background .15s, opacity .15s;
  align-self: flex-start;
}}
.multi-submit:hover {{ opacity: .87; }}
.multi-submit:disabled {{ opacity: .4; cursor: default; }}

.retry-btn {{
  margin-left: auto; padding: 4px 10px;
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 6px; cursor: pointer; font-size: .82rem; color: var(--text2);
}}
.retry-btn:hover {{ border-color: var(--primary); color: var(--primary); }}

/* ── Empty state ──────────────────────────────────── */
#empty {{
  display: none;
  grid-column: 1 / -1;
  text-align: center; padding: 60px 20px;
  color: var(--text2); font-size: 1.1rem;
}}

/* ── Scrollbar ─────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}

/* ── Mobile tweaks ────────────────────────────────── */
@media (max-width: 600px) {{
  header h1 {{ font-size: .9rem; }}
  .q-text {{ font-size: .97rem; }}
  .opt-btn {{ font-size: .91rem; padding: 11px 12px; min-height: 52px; }}
  .controls {{ flex-wrap: wrap; }}
  #ch-select {{ width: 100%; }}
  #search-input {{ flex: 1 1 140px; }}
  .progress-section {{ padding: 6px 12px 8px; }}
}}
</style>
</head>
<body>

<div class="sticky-top">
  <nav class="site-nav">
    <a href="/osh-quiz/">112版</a>
    <span class="sep">|</span>
    <span class="cur">113版</span>
    <span class="sep">|</span>
    <a href="/osh-quiz/kyso/">缺氧作業主管</a>
  </nav>
  <header>
    <h1>營造業丙種職業安全衛生<br>業務主管題庫<small>【113年版 (甲、乙、丙種)精選(471 題)】</small></h1>
    <button id="theme-btn" title="切換深色模式" aria-label="切換深色模式">🌙</button>
  </header>

  <div class="progress-section">
    <div class="progress-meta">
      <span class="progress-label" id="progress-label">已作答 0 / {total} 題</span>
      <span class="accuracy-label" id="accuracy-label"></span>
      <span class="progress-pct" id="progress-pct">0%</span>
    </div>
    <div class="progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="0" id="progress-track">
      <div class="progress-fill" id="progress-fill"></div>
    </div>
  </div>

  <div class="controls">
    <select id="ch-select" aria-label="依章節篩選">
{options_html}    </select>
    <input id="search-input" type="search" placeholder="🔍 關鍵字搜尋…" autocomplete="off" aria-label="搜尋題目">
    <span id="stats"></span>
    <button id="clear-wrong-btn" title="清除錯題記錄">清除錯題本</button>
    <button id="reset-progress-btn" title="重置所有作答記錄">重置進度</button>
    <button id="export-btn" title="匯出作答紀錄（JSON）">⬇ 匯出</button>
    <button id="import-btn" title="匯入作答紀錄（JSON）">⬆ 匯入</button>
    <input id="import-file" type="file" accept=".json" style="display:none">
  </div>
</div>

<main id="main-grid">
  <div id="empty">沒有符合條件的題目</div>
</main>

<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const QUESTIONS = {js_data};
const TOTAL = {total};

// ── Persistence keys (113 site, separate from root site) ──────────────────────
const WRONG_KEY    = 'osh113_wrong_v1';
const ANSWERED_KEY = 'osh113_answered_v1';
const THEME_KEY    = 'osh113_theme';

// ── Helpers for multi-answer questions ───────────────────────────────────────
function isMultiple(q) {{
  return Array.isArray(q.answer);
}}
function arraysEqual(a, b) {{
  if (!Array.isArray(a) || !Array.isArray(b)) return false;
  if (a.length !== b.length) return false;
  return [...a].sort((x,y)=>x-y).every((v,i) => v === [...b].sort((x,y)=>x-y)[i]);
}}

// ── Load persisted state ──────────────────────────────────────────────────────
let wrongSet = new Set(JSON.parse(localStorage.getItem(WRONG_KEY) || '[]'));

// answered: Map<id, {{chosen}}>
// chosen is a number (single) or sorted number[] (multi-select)
const _savedAnswered = JSON.parse(localStorage.getItem(ANSWERED_KEY) || '{{}}');
const answered = new Map(
  Object.entries(_savedAnswered).map(([k, chosen]) => {{
    return [+k, {{ chosen: Array.isArray(chosen) ? chosen : +chosen }}];
  }})
);

// ── Persist helpers ───────────────────────────────────────────────────────────
function saveWrong() {{
  localStorage.setItem(WRONG_KEY, JSON.stringify([...wrongSet]));
  updateWrongLabel();
}}
function saveAnswered() {{
  const obj = {{}};
  answered.forEach((val, id) => {{ obj[id] = val.chosen; }});
  localStorage.setItem(ANSWERED_KEY, JSON.stringify(obj));
}}

// ── Progress bar ──────────────────────────────────────────────────────────────
function updateProgress() {{
  const count = answered.size;
  const pct = TOTAL > 0 ? Math.round(count / TOTAL * 100) : 0;
  const done = pct === 100;

  document.getElementById('progress-label').textContent =
    `已作答 ${{count}} / ${{TOTAL}} 題`;
  const accEl = document.getElementById('accuracy-label');
  if (accEl) {{
    if (count > 0) {{
      const correctCount = count - wrongSet.size;
      const accPct = (correctCount / count * 100).toFixed(2);
      accEl.textContent = `✓ 正確率 ${{accPct}}%`;
    }} else {{
      accEl.textContent = '';
    }}
  }}
  const pctEl = document.getElementById('progress-pct');
  pctEl.textContent = done ? '🎉 全部完成！' : pct + '%';
  pctEl.className = 'progress-pct' + (done ? ' done' : '');

  const fill = document.getElementById('progress-fill');
  fill.style.width = pct + '%';
  fill.className = 'progress-fill' + (done ? ' done' : '');

  document.getElementById('progress-track').setAttribute('aria-valuenow', count);
  updateIncompleteLabel();
}}

// ── Wrong-answer helpers ──────────────────────────────────────────────────────
function markWrong(id) {{
  wrongSet.add(id);
  saveWrong();
  const card = document.getElementById('card-' + id);
  if (card) {{ card.classList.add('was-wrong'); card.classList.remove('answered-ok'); }}
}}
function unmarkWrong(id) {{
  wrongSet.delete(id);
  saveWrong();
  const card = document.getElementById('card-' + id);
  if (card) {{ card.classList.remove('was-wrong'); card.classList.add('answered-ok'); }}
}}

// ── Current filter state ──────────────────────────────────────────────────────
let currentFilter = '全部';
let currentSearch = '';

// ── Chapter tag display ───────────────────────────────────────────────────────
function chTag(q) {{
  // Show short chapter label
  const ch = q.chapter || '';
  // Extract e.g. "第一章" from full name
  const short = ch.length > 10 ? ch.slice(0, 10) + '…' : ch;
  let cls = 'ch-tag';
  if (q.isMultiple) cls += ' multiple';
  else if (q.isNumeric) cls += ' numeric';
  const badge = q.isMultiple ? ' ☑' : (q.isNumeric ? ' 🔢' : '');
  return `<span class="${{cls}}">${{short}}${{badge}}</span>`;
}}

// ── Render multiple-select card ───────────────────────────────────────────────
function renderMultiCard(q) {{
  const ans = answered.get(q.id);
  const wasWrong = wrongSet.has(q.id);

  let cardCls = 'card';
  if (ans) {{
    cardCls += arraysEqual(ans.chosen, q.answer) ? ' answered-ok' : ' was-wrong';
  }} else if (wasWrong) {{
    cardCls += ' was-wrong';
  }}

  const chosen = ans ? ans.chosen : [];
  const optBtns = q.options.map((opt, i) => {{
    const num = i + 1;
    let cls = 'multi-btn';
    let disabled = '';
    if (ans) {{
      disabled = 'disabled';
      const inAns    = Array.isArray(ans.chosen) && ans.chosen.includes(num);
      const inAnswer = q.answer.includes(num);
      if (inAnswer && inAns)   cls += ' correct';
      else if (!inAnswer && inAns) cls += ' wrong';
      else if (inAnswer && !inAns) cls += ' missed';
    }} else if (Array.isArray(chosen) && chosen.includes(num)) {{
      cls += ' selected';
    }}
    return `<button class="${{cls}}" ${{disabled}} data-id="${{q.id}}" data-num="${{num}}">(${{num}}) ${{opt}}</button>`;
  }}).join('\\n');

  const submitDisabled = ans ? 'disabled' : '';
  const submitBtn = `<button class="multi-submit" ${{submitDisabled}} data-id="${{q.id}}">確認答案</button>`;

  let resultHtml = '';
  if (ans) {{
    const ok = arraysEqual(ans.chosen, q.answer);
    const letters = ['A','B','C','D'];
    const correctLabels = q.answer.map(n => `(${{letters[n-1]}})`).join(' ');
    if (ok) {{
      resultHtml = `<div class="result-row ok show">✅ 答對了！<button class="retry-btn" data-id="${{q.id}}">重試</button></div>`;
    }} else {{
      resultHtml = `<div class="result-row bad show">❌ 答錯！正確選項：${{correctLabels}}<button class="retry-btn" data-id="${{q.id}}">重試</button></div>`;
    }}
  }}

  return `<div class="${{cardCls}}" id="card-${{q.id}}">
  <div class="card-header">
    <span class="q-num">Q${{q.id}}</span>
    ${{chTag(q)}}
  </div>
  <div class="q-text">${{q.text}}</div>
  <div class="multi-options">
${{optBtns}}
${{submitBtn}}
  </div>
  ${{resultHtml}}
</div>`;
}}

// ── Render single-choice card ──────────────────────────────────────────────────
function renderCard(q) {{
  if (isMultiple(q)) return renderMultiCard(q);

  const ans = answered.get(q.id);
  const wasWrong = wrongSet.has(q.id);
  const isNeg = !!q.isNegative;

  let cardCls = 'card';
  if (ans) {{
    cardCls += ans.chosen === q.answer ? ' answered-ok' : ' was-wrong';
  }} else if (wasWrong) {{
    cardCls += ' was-wrong';
  }}

  const optBtns = q.options.map((opt, i) => {{
    const num = i + 1;
    let cls = 'opt-btn';
    let disabled = '';
    if (ans) {{
      disabled = 'disabled';
      if (num === q.answer) cls += isNeg ? ' correct-neg' : ' correct';
      else if (num === ans.chosen) cls += ' wrong';
    }}
    return `<button class="${{cls}}" ${{disabled}} data-id="${{q.id}}" data-num="${{num}}">(${{num}}) ${{opt}}</button>`;
  }}).join('\\n');

  let resultHtml = '';
  if (ans) {{
    if (ans.chosen === q.answer) {{
      const okCls = isNeg ? 'result-row ok neg show' : 'result-row ok show';
      const okMsg = isNeg ? '⚠️ 答對！（此選項為題目中唯一錯誤的）' : '✅ 答對了！';
      resultHtml = `<div class="${{okCls}}">${{okMsg}}<button class="retry-btn" data-id="${{q.id}}">重試</button></div>`;
    }} else {{
      const negHint = isNeg ? '（反向題，選最不正確的）' : '';
      resultHtml = `<div class="result-row bad show">❌ 答錯！${{negHint}}正解是 (${{q.answer}}) ${{q.options[q.answer - 1]}}<button class="retry-btn" data-id="${{q.id}}">重試</button></div>`;
    }}
  }}

  const numBadge = q.isNumeric ? ' 🔢' : '';

  return `<div class="${{cardCls}}" id="card-${{q.id}}">
  <div class="card-header">
    <span class="q-num">Q${{q.id}}${{numBadge}}</span>
    ${{chTag(q)}}
  </div>
  <div class="q-text">${{q.text}}</div>
  <div class="options">${{optBtns}}</div>
  ${{resultHtml}}
</div>`;
}}

// ── Update "未完成" option label ──────────────────────────────────────────────
function updateWrongLabel() {{
  const el = document.getElementById('opt-wrong');
  if (el) el.textContent = `⭐ 我的錯題本（${{wrongSet.size}} 題）`;
}}

function updateIncompleteLabel() {{
  const cnt = QUESTIONS.filter(q => !answered.has(q.id)).length;
  const el = document.getElementById('opt-incomplete');
  if (el) el.textContent = `📝 未完成（${{cnt}} 題）`;
}}

// ── Filter logic ──────────────────────────────────────────────────────────────
function filteredQuestions() {{
  let list = QUESTIONS;
  if (currentFilter === '錯題本') {{
    list = list.filter(q => wrongSet.has(q.id));
  }} else if (currentFilter === '金庫密碼') {{
    list = list.filter(q => q.isNumeric);
  }} else if (currentFilter === '複選題') {{
    list = list.filter(q => q.isMultiple);
  }} else if (currentFilter === '未完成') {{
    list = list.filter(q => !answered.has(q.id));
  }} else if (currentFilter !== '全部') {{
    list = list.filter(q => q.chapter === currentFilter);
  }}
  if (currentSearch) {{
    const kw = currentSearch.trim().toLowerCase();
    list = list.filter(q =>
      q.text.toLowerCase().includes(kw) ||
      q.options.some(o => o.toLowerCase().includes(kw))
    );
  }}
  return list;
}}

function filteredBase() {{
  if (currentFilter === '錯題本') return wrongSet.size;
  if (currentFilter === '金庫密碼') return QUESTIONS.filter(q => q.isNumeric).length;
  if (currentFilter === '複選題') return QUESTIONS.filter(q => q.isMultiple).length;
  if (currentFilter === '未完成') return QUESTIONS.filter(q => !answered.has(q.id)).length;
  if (currentFilter === '全部') return TOTAL;
  return QUESTIONS.filter(q => q.chapter === currentFilter).length;
}}

// ── Render grid ───────────────────────────────────────────────────────────────
function render() {{
  const grid = document.getElementById('main-grid');
  const empty = document.getElementById('empty');
  const stats = document.getElementById('stats');
  const clearBtn = document.getElementById('clear-wrong-btn');
  const list = filteredQuestions();

  grid.querySelectorAll('.card').forEach(c => c.remove());

  if (list.length === 0) {{
    empty.style.display = 'block';
  }} else {{
    empty.style.display = 'none';
    const frag = document.createDocumentFragment();
    list.forEach(q => {{
      const tmp = document.createElement('div');
      tmp.innerHTML = renderCard(q);
      frag.appendChild(tmp.firstElementChild);
    }});
    grid.appendChild(frag);
  }}

  stats.textContent = currentSearch
    ? `顯示 ${{list.length}} / ${{filteredBase()}} 題`
    : `共 ${{list.length}} 題`;

  clearBtn.style.display = currentFilter === '錯題本' && wrongSet.size > 0 ? 'block' : 'none';
}}

// ── Event delegation ──────────────────────────────────────────────────────────
document.getElementById('main-grid').addEventListener('click', e => {{

  // ── Single-choice option ──
  const optBtn = e.target.closest('.opt-btn');
  if (optBtn && !optBtn.disabled) {{
    const id = +optBtn.dataset.id;
    const chosen = +optBtn.dataset.num;
    const q = QUESTIONS.find(q => q.id === id);

    answered.set(id, {{ chosen }});
    saveAnswered();
    updateProgress();

    if (chosen === q.answer) unmarkWrong(id);
    else markWrong(id);

    const card = document.getElementById('card-' + id);
    const tmp = document.createElement('div');
    tmp.innerHTML = renderCard(q);
    card.replaceWith(tmp.firstElementChild);
    return;
  }}

  // ── Multiple-select: toggle button ──
  const multiBtn = e.target.closest('.multi-btn');
  if (multiBtn && !multiBtn.disabled) {{
    multiBtn.classList.toggle('selected');
    return;
  }}

  // ── Multiple-select: confirm submit ──
  const submitBtn = e.target.closest('.multi-submit');
  if (submitBtn && !submitBtn.disabled) {{
    const id = +submitBtn.dataset.id;
    const card = document.getElementById('card-' + id);
    const q = QUESTIONS.find(q => q.id === id);

    const chosen = [];
    card.querySelectorAll('.multi-btn.selected').forEach(btn => {{
      chosen.push(+btn.dataset.num);
    }});
    chosen.sort((a, b) => a - b);

    answered.set(id, {{ chosen }});
    saveAnswered();
    updateProgress();

    if (arraysEqual(chosen, q.answer)) unmarkWrong(id);
    else markWrong(id);

    const tmp = document.createElement('div');
    tmp.innerHTML = renderCard(q);
    card.replaceWith(tmp.firstElementChild);
    return;
  }}

  // ── Retry ──
  const retryBtn = e.target.closest('.retry-btn');
  if (retryBtn) {{
    const id = +retryBtn.dataset.id;
    answered.delete(id);
    saveAnswered();
    updateProgress();

    const q = QUESTIONS.find(q => q.id === id);
    const card = document.getElementById('card-' + id);
    const tmp = document.createElement('div');
    tmp.innerHTML = renderCard(q);
    card.replaceWith(tmp.firstElementChild);
  }}
}});

// ── Controls ──────────────────────────────────────────────────────────────────
document.getElementById('ch-select').addEventListener('change', e => {{
  currentFilter = e.target.value;
  render();
}});

let searchTimer;
document.getElementById('search-input').addEventListener('input', e => {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {{
    currentSearch = e.target.value;
    render();
  }}, 220);
}});

document.getElementById('clear-wrong-btn').addEventListener('click', () => {{
  if (!confirm('確定清除所有錯題記錄？')) return;
  wrongSet.clear();
  saveWrong();
  document.querySelectorAll('.card.was-wrong').forEach(c => c.classList.remove('was-wrong'));
  render();
}});

document.getElementById('reset-progress-btn').addEventListener('click', () => {{
  if (!confirm('確定重置所有作答記錄？\\n（進度與錯題本都會清空）')) return;
  answered.clear();
  wrongSet.clear();
  saveAnswered();
  saveWrong();
  updateProgress();
  render();
}});

// ── Export / Import ───────────────────────────────────────────────────────────
document.getElementById('export-btn').addEventListener('click', () => {{
  const payload = {{
    version: 1,
    site: 'osh113',
    exportedAt: new Date().toISOString(),
    wrong: [...wrongSet],
    answered: Object.fromEntries(
      [...answered.entries()].map(([id, {{chosen}}]) => [id, chosen])
    ),
  }};
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{type: 'application/json'}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const date = new Date().toISOString().slice(0, 10);
  a.href = url;
  a.download = `osh113-quiz-backup-${{date}}.json`;
  a.click();
  URL.revokeObjectURL(url);
}});

document.getElementById('import-btn').addEventListener('click', () => {{
  document.getElementById('import-file').value = '';
  document.getElementById('import-file').click();
}});

document.getElementById('import-file').addEventListener('change', e => {{
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {{
    try {{
      const data = JSON.parse(ev.target.result);
      if (data.version !== 1 || !Array.isArray(data.wrong) || typeof data.answered !== 'object') {{
        alert('檔案格式不正確，請選擇由本系統匯出的 JSON 檔。');
        return;
      }}
      const wCnt = data.wrong.length;
      const aCnt = Object.keys(data.answered).length;
      if (!confirm(`確定匯入此紀錄？\\n・已作答：${{aCnt}} 題\\n・錯題本：${{wCnt}} 題\\n\\n匯入後將覆蓋目前的進度！`)) return;

      wrongSet = new Set(data.wrong.map(Number));
      saveWrong();

      answered.clear();
      for (const [k, chosen] of Object.entries(data.answered)) {{
        const id = +k;
        const q = QUESTIONS.find(q => q.id === id);
        if (q) answered.set(id, {{chosen: Array.isArray(chosen) ? chosen : +chosen}});
      }}
      saveAnswered();

      updateProgress();
      render();
      alert(`匯入完成！已作答 ${{answered.size}} 題，錯題本 ${{wrongSet.size}} 題。`);
    }} catch (_) {{
      alert('讀取失敗，請確認檔案是否為有效的 JSON。');
    }}
  }};
  reader.readAsText(file);
}});

// ── Dark mode ─────────────────────────────────────────────────────────────────
const themeBtn = document.getElementById('theme-btn');

function applyTheme(dark) {{
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  themeBtn.textContent = dark ? '☀️' : '🌙';
  localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light');
}}

const savedTheme = localStorage.getItem(THEME_KEY);
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
applyTheme(savedTheme ? savedTheme === 'dark' : prefersDark);

themeBtn.addEventListener('click', () => {{
  applyTheme(document.documentElement.getAttribute('data-theme') !== 'dark');
}});

// ── Fullscreen (F key) ───────────────────────────────────────────────────────
document.addEventListener('keydown', e => {{
  if ((e.key === 'f' || e.key === 'F') &&
      document.activeElement !== document.getElementById('search-input')) {{
    if (!document.fullscreenElement) {{
      document.documentElement.requestFullscreen().catch(() => {{}});
    }} else {{
      document.exitFullscreen().catch(() => {{}});
    }}
  }}
}});

// ── Init ──────────────────────────────────────────────────────────────────────
updateProgress();
updateWrongLabel();
render();
</script>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Built index.html ({len(HTML):,} chars)")
print(f"Total: {total} questions, {numeric_count} numeric, {multiple_count} multiple-choice")
