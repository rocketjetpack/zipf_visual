#!/usr/bin/env python3

import json
import math
import re
from collections import Counter
from pathlib import Path


FILES = [
    "huckleberry_finn.txt",
    "shakespeare_complete_works.txt",
    "alice_adventures_wonderland.txt",
]

TOP_N = 500
START_RE = re.compile(r"\*\*\* START OF THE PROJECT GUTENBERG EBOOK .* \*\*\*")
END_RE = re.compile(r"\*\*\* END OF THE PROJECT GUTENBERG EBOOK .* \*\*\*")
WORD_RE = re.compile(r"[a-z]+(?:'[a-z]+)*")
STOP_WORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


def strip_gutenberg_boilerplate(text: str) -> str:
    lines = text.splitlines()
    start_idx = 0
    end_idx = len(lines)

    for idx, line in enumerate(lines):
        if START_RE.search(line):
            start_idx = idx + 1
            break

    for idx in range(len(lines) - 1, -1, -1):
        if END_RE.search(lines[idx]):
            end_idx = idx
            break

    return "\n".join(lines[start_idx:end_idx])


def tokenize(text: str) -> list[str]:
    normalized = text.lower().replace("’", "'").replace("‘", "'").replace("`", "'")
    return WORD_RE.findall(normalized)


def filter_stop_words(tokens: list[str]) -> list[str]:
    return [token for token in tokens if len(token) > 1 and token not in STOP_WORDS]


def fit_zipf(freqs: list[int]) -> tuple[float, float, float]:
    ranks = [i + 1 for i in range(len(freqs))]
    log_ranks = [math.log10(rank) for rank in ranks]
    log_freqs = [math.log10(freq) for freq in freqs]

    mean_x = sum(log_ranks) / len(log_ranks)
    mean_y = sum(log_freqs) / len(log_freqs)

    ss_xx = sum((x - mean_x) ** 2 for x in log_ranks)
    ss_yy = sum((y - mean_y) ** 2 for y in log_freqs)
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(log_ranks, log_freqs))

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)
    return slope, intercept, r_squared


def analyze_file(path: Path) -> dict:
    raw_text = path.read_text(encoding="utf-8-sig")
    clean_text = strip_gutenberg_boilerplate(raw_text)
    tokens = filter_stop_words(tokenize(clean_text))
    counts = Counter(tokens)
    freqs = sorted(counts.values(), reverse=True)
    slope, intercept, r_squared = fit_zipf(freqs)

    top_terms = []
    for rank, (word, freq) in enumerate(counts.most_common(TOP_N), start=1):
        top_terms.append(
            {
                "rank": rank,
                "word": word,
                "frequency": freq,
                "rank_frequency": rank * freq,
                "log_rank": math.log10(rank),
                "log_frequency": math.log10(freq),
            }
        )

    return {
        "file": path.name,
        "title": path.stem.replace("_", " ").title(),
        "total_tokens": len(tokens),
        "unique_tokens": len(counts),
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_squared,
        "top_terms": top_terms,
        "top_word": counts.most_common(1)[0][0],
        "top_word_frequency": counts.most_common(1)[0][1],
        "zipf_constant_preview": sum(
            (rank + 1) * freq for rank, freq in enumerate(freqs[:10])
        )
        / min(10, len(freqs)),
    }


def build_html(payload: dict) -> str:
    data_json = json.dumps(payload, ensure_ascii=True)
    template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Zipf's Law Explorer</title>
  <style>
    :root {{
      --bg: #0f1220;
      --panel: rgba(18, 23, 39, 0.86);
      --panel-2: rgba(28, 34, 55, 0.9);
      --text: #e8eefc;
      --muted: #aab6d3;
      --grid: rgba(255,255,255,0.08);
      --accent: #7dd3fc;
      --accent-2: #f472b6;
      --good: #86efac;
      --warn: #fbbf24;
      --shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(125, 211, 252, 0.18), transparent 30%),
        radial-gradient(circle at 85% 15%, rgba(244, 114, 182, 0.14), transparent 25%),
        linear-gradient(180deg, #0b1020 0%, #12182b 100%);
      min-height: 100vh;
    }}
    .page {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px;
    }}
    header {{
      display: grid;
      gap: 10px;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.5rem);
      line-height: 1;
      letter-spacing: -0.04em;
    }}
    .subtitle {{
      margin: 0;
      max-width: 72ch;
      color: var(--muted);
      font-size: 1rem;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 2.1fr) minmax(320px, 0.9fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }}
    .chart-panel {{
      padding: 18px;
    }}
    .controls {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .control {{
      background: var(--panel-2);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px;
      padding: 12px;
    }}
    label {{
      display: block;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    select, input[type="range"] {{
      width: 100%;
    }}
    select {{
      appearance: none;
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.06);
      color: var(--text);
      border-radius: 12px;
      padding: 11px 12px;
      font: inherit;
    }}
    .range-row {{
      display: flex;
      gap: 10px;
      align-items: center;
    }}
    .range-value {{
      min-width: 68px;
      text-align: right;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 14px;
    }}
    .stat {{
      padding: 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .stat .k {{
      color: var(--muted);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 8px;
    }}
    .stat .v {{
      font-size: 1.1rem;
      font-variant-numeric: tabular-nums;
    }}
    .svg-wrap {{
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.08);
      overflow: hidden;
    }}
    svg {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .side {{
      padding: 18px;
      display: grid;
      gap: 16px;
    }}
    .card {{
      padding: 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .card h2 {{
      margin: 0 0 10px;
      font-size: 1.05rem;
    }}
    .card p, .card li {{
      color: var(--muted);
      line-height: 1.55;
    }}
    .card ul {{
      margin: 10px 0 0;
      padding-left: 18px;
    }}
    .legend {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.08);
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
    }}
    .tooltip {{
      position: fixed;
      pointer-events: none;
      background: rgba(10, 14, 26, 0.96);
      color: var(--text);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 10px 12px;
      box-shadow: var(--shadow);
      opacity: 0;
      transform: translate(-50%, -120%);
      transition: opacity 120ms ease;
      font-size: 0.9rem;
      z-index: 10;
    }}
    .footer-note {{
      margin-top: 12px;
      color: var(--muted);
      font-size: 0.88rem;
    }}
    .chart-heading {{
      margin: 20px 4px 12px;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      color: var(--text);
    }}
    @media (max-width: 1000px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .controls, .stats {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <header>
      <h1>Zipf's Law Explorer</h1>
      <p class="subtitle">Explore how word frequency falls as rank rises across three public-domain books after removing common stop words. Zipf's Law predicts that the most frequent word is roughly twice as common as the second, three times as common as the third, and so on, which produces an approximately straight line on a log-log plot.</p>
    </header>

    <div class="layout">
      <section class="panel chart-panel">
        <div class="controls">
          <div class="control">
            <label for="book">Text</label>
            <select id="book"></select>
          </div>
          <div class="control">
            <label for="topn">Ranks shown</label>
            <div class="range-row">
              <input id="topn" type="range" min="25" max="{TOP_N}" step="25" value="200" />
              <div class="range-value" id="topnValue">200</div>
            </div>
          </div>
        </div>

        <div class="stats" id="stats"></div>

        <div class="legend">
          <span class="chip"><span class="dot" style="background: var(--accent);"></span>Observed frequency</span>
          <span class="chip"><span class="dot" style="background: var(--accent-2);"></span>Zipf reference slope -1</span>
          <span class="chip"><span class="dot" style="background: var(--good);"></span>Regression fit</span>
        </div>

        <div class="chart-heading">Bar Chart: Top Word Frequencies</div>
        <div class="svg-wrap">
          <svg id="barChart" viewBox="0 0 960 540" role="img" aria-label="Horizontal bar chart of the most frequent words"></svg>
        </div>
        <div class="footer-note">The bar chart shows the most frequent words in the selected text, sorted by rank.</div>

        <div class="chart-heading">Line Chart: Zipf Plot</div>
        <div class="svg-wrap" style="margin-top: 14px;">
          <svg id="chart" viewBox="0 0 960 620" role="img" aria-label="Log-log plot of word frequency by rank"></svg>
        </div>
        <div class="footer-note">Hover a point to inspect the word, rank, and frequency. The chart uses log10 scales on both axes.</div>
      </section>

      <aside class="panel side">
        <div class="card">
          <h2>What Zipf's Law Says</h2>
          <p>In natural language, the frequency of a word tends to be inversely proportional to its rank. If you sort words from most common to least common, word <code>r</code> often appears about <code>1 / r</code> as often as the top word.</p>
          <ul>
            <li>A flat-looking vocabulary on raw counts becomes linear on a log-log chart.</li>
            <li>The law is approximate, not exact; books and genres differ.</li>
          <li>Common stop words like "the", "and", and "of" have been removed from this view.</li>
          </ul>
        </div>
        <div class="card">
          <h2>How To Read The Plot</h2>
          <ul>
            <li>Each dot is one word from the selected book.</li>
            <li>Moving right means a lower rank, so frequency should drop.</li>
            <li>If the observed points track the green line, the text is Zipf-like.</li>
          </ul>
        </div>
        <div class="card">
          <h2>Data Window</h2>
          <p id="windowSummary"></p>
        </div>
      </aside>
    </div>
  </div>
  <div id="tooltip" class="tooltip"></div>

  <script id="zipf-data" type="application/json">__DATA_JSON__</script>
  <script>
    const data = JSON.parse(document.getElementById('zipf-data').textContent);
    const bookSelect = document.getElementById('book');
    const topnInput = document.getElementById('topn');
    const topnValue = document.getElementById('topnValue');
    const chart = document.getElementById('chart');
    const barChart = document.getElementById('barChart');
    const statsEl = document.getElementById('stats');
    const windowSummary = document.getElementById('windowSummary');
    const tooltip = document.getElementById('tooltip');

    const colors = {{
      observed: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim(),
      reference: getComputedStyle(document.documentElement).getPropertyValue('--accent-2').trim(),
      fit: getComputedStyle(document.documentElement).getPropertyValue('--good').trim(),
      grid: getComputedStyle(document.documentElement).getPropertyValue('--grid').trim(),
      text: getComputedStyle(document.documentElement).getPropertyValue('--text').trim(),
      muted: getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(),
    }};

    const margin = {{ top: 32, right: 28, bottom: 74, left: 82 }};
    const width = 960;
    const height = 620;
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const barMargin = {{ top: 28, right: 26, bottom: 56, left: 150 }};
    const barWidth = 960;
    const barHeight = 540;
    const barPlotWidth = barWidth - barMargin.left - barMargin.right;
    const barPlotHeight = barHeight - barMargin.top - barMargin.bottom;

    data.books.forEach((book, idx) => {{
      const option = document.createElement('option');
      option.value = idx;
      option.textContent = book.title;
      bookSelect.appendChild(option);
    }});

    function formatInt(value) {{
      return new Intl.NumberFormat().format(value);
    }}

    function getState() {{
      const book = data.books[Number(bookSelect.value)];
      const topN = Number(topnInput.value);
      return {{ book, topN }};
    }}

    function log10(value) {{
      return Math.log(value) / Math.LN10;
    }}

    function linearScale(domainMin, domainMax, rangeMin, rangeMax, value) {{
      return rangeMin + ((value - domainMin) / (domainMax - domainMin)) * (rangeMax - rangeMin);
    }}

    function clear(node) {{
      while (node.firstChild) node.removeChild(node.firstChild);
    }}

    function el(name, attrs = {{}}) {{
      const node = document.createElementNS('http://www.w3.org/2000/svg', name);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    }}

    function integerTicks(minValue, maxValue) {{
      const start = Math.max(0, Math.ceil(minValue));
      const end = Math.max(start, Math.floor(maxValue));
      const ticks = [];
      for (let value = start; value <= end; value++) ticks.push(value);
      return ticks;
    }}

    function drawGrid(xMin, xMax, yMin, yMax) {{
      const groups = el('g');
      const xTicks = integerTicks(xMin, xMax);
      const yTicks = integerTicks(yMin, yMax);

      xTicks.forEach((tick) => {{
        const x = linearScale(xMin, xMax, margin.left, margin.left + plotWidth, tick);
        groups.appendChild(el('line', {{
          x1: x, y1: margin.top, x2: x, y2: margin.top + plotHeight,
          stroke: colors.grid, 'stroke-width': 1
        }}));
        groups.appendChild(el('text', {{
          x, y: height - 32, fill: colors.muted, 'text-anchor': 'middle', 'font-size': 14
        }}));
        groups.lastChild.textContent = tick;
      }});

      yTicks.forEach((tick) => {{
        const y = linearScale(yMin, yMax, margin.top + plotHeight, margin.top, tick);
        groups.appendChild(el('line', {{
          x1: margin.left, y1: y, x2: margin.left + plotWidth, y2: y,
          stroke: colors.grid, 'stroke-width': 1
        }}));
        groups.appendChild(el('text', {{
          x: margin.left - 14, y: y + 5, fill: colors.muted, 'text-anchor': 'end', 'font-size': 14
        }}));
        groups.lastChild.textContent = `10^${tick}`;
      }});
      return groups;
    }}

    function drawBarChart(book, topN) {{
      const displayCount = Math.min(20, topN, book.top_terms.length);
      const items = book.top_terms.slice(0, displayCount);
      const maxFrequency = Math.max(...items.map((d) => d.frequency));

      clear(barChart);

      const title = el('text', {{
        x: barMargin.left,
        y: 22,
        fill: colors.text,
        'font-size': 18,
        'font-weight': 700
      }});
      title.textContent = `${book.title}: top ${displayCount} words`;
      barChart.appendChild(title);

      const xLabel = el('text', {{
        x: barMargin.left + barPlotWidth / 2,
        y: barHeight - 12,
        fill: colors.muted,
        'text-anchor': 'middle',
        'font-size': 15
      }});
      xLabel.textContent = 'frequency';
      barChart.appendChild(xLabel);

      const yLabel = el('text', {{
        x: 22,
        y: barMargin.top + barPlotHeight / 2,
        fill: colors.muted,
        'text-anchor': 'middle',
        'font-size': 15,
        transform: `rotate(-90 22 ${barMargin.top + barPlotHeight / 2})`
      }});
      yLabel.textContent = 'word';
      barChart.appendChild(yLabel);

      const xTicks = 5;
      for (let i = 0; i <= xTicks; i++) {{
        const value = Math.round((maxFrequency / xTicks) * i);
        const x = linearScale(0, maxFrequency, barMargin.left, barMargin.left + barPlotWidth, value);
        barChart.appendChild(el('line', {{
          x1: x, y1: barMargin.top, x2: x, y2: barMargin.top + barPlotHeight,
          stroke: colors.grid, 'stroke-width': 1
        }}));
        const tickLabel = el('text', {{
          x, y: barHeight - 34, fill: colors.muted, 'text-anchor': 'middle', 'font-size': 13
        }});
        tickLabel.textContent = formatInt(value);
        barChart.appendChild(tickLabel);
      }}

      const rowHeight = barPlotHeight / items.length;
      items.forEach((d, index) => {{
        const y = barMargin.top + index * rowHeight + rowHeight * 0.16;
        const barH = rowHeight * 0.66;
        const barW = linearScale(0, maxFrequency, 0, barPlotWidth, d.frequency);
        const rect = el('rect', {{
          x: barMargin.left,
          y,
          width: barW,
          height: barH,
          rx: 8,
          fill: colors.observed,
          opacity: 0.9
        }});
        rect.addEventListener('mousemove', (event) => {{
          tooltip.style.opacity = '1';
          tooltip.style.left = `${event.clientX}px`;
          tooltip.style.top = `${event.clientY}px`;
          tooltip.innerHTML = `<strong>${d.word}</strong><br>Rank: ${d.rank}<br>Frequency: ${formatInt(d.frequency)}`;
        }});
        rect.addEventListener('mouseleave', () => {{
          tooltip.style.opacity = '0';
        }});
        barChart.appendChild(rect);

        const wordLabel = el('text', {{
          x: barMargin.left - 12,
          y: y + barH * 0.7,
          fill: colors.text,
          'text-anchor': 'end',
          'font-size': 14
        }});
        wordLabel.textContent = d.word;
        barChart.appendChild(wordLabel);
      }});
    }}

    function render() {{
      const {{ book, topN }} = getState();
      topnValue.textContent = topN.toString();
      const points = book.top_terms.slice(0, topN);
      const xVals = points.map((d) => d.log_rank);
      const yVals = points.map((d) => d.log_frequency);
      const xMin = 0;
      const xMax = Math.max(1.1, Math.max(...xVals));
      const yMin = Math.min(...yVals) - 0.2;
      const yMax = Math.max(...yVals) + 0.35;

      clear(chart);
      chart.appendChild(drawGrid(xMin, xMax, yMin, yMax));

      const title = el('text', {{
        x: margin.left,
        y: 22,
        fill: colors.text,
        'font-size': 18,
        'font-weight': 700
      }});
      title.textContent = `${book.title}: frequency vs. rank`;
      chart.appendChild(title);

      const xLabel = el('text', {{
        x: margin.left + plotWidth / 2,
        y: height - 14,
        fill: colors.muted,
        'text-anchor': 'middle',
        'font-size': 15
      }});
      xLabel.textContent = 'log10(rank)';
      chart.appendChild(xLabel);

      const yLabel = el('text', {{
        x: 22,
        y: margin.top + plotHeight / 2,
        fill: colors.muted,
        'text-anchor': 'middle',
        'font-size': 15,
        transform: `rotate(-90 22 ${margin.top + plotHeight / 2})`
      }});
      yLabel.textContent = 'log10(frequency)';
      chart.appendChild(yLabel);

      const referenceLine = [];
      const fitLine = [];
      const fitStartX = 0;
      const fitEndX = xMax;
      const refTop = book.top_word_frequency;
      const refIntercept = log10(refTop);

      for (let i = 0; i <= 100; i++) {{
        const lx = fitStartX + (fitEndX - fitStartX) * (i / 100);
        referenceLine.push([lx, refIntercept - lx]);
        fitLine.push([lx, book.intercept + book.slope * lx]);
      }}

      function pathFrom(points) {{
        return points.map(([x, y], idx) => {{
          const px = linearScale(xMin, xMax, margin.left, margin.left + plotWidth, x);
          const py = linearScale(yMin, yMax, margin.top + plotHeight, margin.top, y);
          return `${idx === 0 ? 'M' : 'L'} ${px.toFixed(2)} ${py.toFixed(2)}`;
        }}).join(' ');
      }}

      chart.appendChild(el('path', {{
        d: pathFrom(referenceLine),
        fill: 'none',
        stroke: colors.reference,
        'stroke-width': 3,
        'stroke-dasharray': '8 7',
        opacity: 0.95
      }}));

      chart.appendChild(el('path', {{
        d: pathFrom(fitLine),
        fill: 'none',
        stroke: colors.fit,
        'stroke-width': 3,
        opacity: 0.95
      }}));

      points.forEach((d) => {{
        const cx = linearScale(xMin, xMax, margin.left, margin.left + plotWidth, d.log_rank);
        const cy = linearScale(yMin, yMax, margin.top + plotHeight, margin.top, d.log_frequency);
        const circle = el('circle', {{
          cx, cy, r: d.rank <= 10 ? 5 : 3.5,
          fill: colors.observed,
          opacity: 0.88,
          stroke: 'rgba(255,255,255,0.16)',
          'stroke-width': 1
        }});
        circle.addEventListener('mousemove', (event) => {{
          tooltip.style.opacity = '1';
          tooltip.style.left = `${event.clientX}px`;
          tooltip.style.top = `${event.clientY}px`;
          tooltip.innerHTML = `<strong>${d.word}</strong><br>Rank: ${d.rank}<br>Frequency: ${formatInt(d.frequency)}`;
        }});
        circle.addEventListener('mouseleave', () => {{
          tooltip.style.opacity = '0';
        }});
        chart.appendChild(circle);
      }});

      const stats = [
        ['Total tokens', formatInt(book.total_tokens)],
        ['Unique tokens', formatInt(book.unique_tokens)],
        ['Slope', book.slope.toFixed(4)],
        ['R²', book.r_squared.toFixed(4)],
      ];
      statsEl.innerHTML = stats.map(([k, v]) => `
        <div class="stat">
          <div class="k">${k}</div>
          <div class="v">${v}</div>
        </div>
      `).join('');

      windowSummary.innerHTML = `
        Showing the top <strong>${formatInt(topN)}</strong> ranks out of <strong>${formatInt(book.unique_tokens)}</strong> unique words.
        The selected book's leading word is <strong>${book.top_word}</strong> (${formatInt(book.top_word_frequency)} occurrences).
      `;

      drawBarChart(book, topN);
    }}

    bookSelect.addEventListener('change', render);
    topnInput.addEventListener('input', render);
    render();
  </script>
</body>
</html>
"""
    return template.replace("{{", "{").replace("}}", "}").replace("__DATA_JSON__", data_json)


def main() -> None:
    base = Path(__file__).resolve().parent
    books = [analyze_file(base / name) for name in FILES]
    payload = {"books": books}
    html = build_html(payload)
    out_path = base / "zipf_interactive.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
