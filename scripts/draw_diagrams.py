"""Original, deterministic monochrome SVG diagrams; editable source included."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]


def draw(lang):
    zh = lang == "zh"
    labels = ["明确要求", "读取与决策", "有界工具", "检查证据"] if zh else ["Define the task", "Read & decide", "Bounded tools", "Check evidence"]
    subtitles = ["goal + constraints", "context → action", "execute → result", "tests + diff"]
    positions = [(37, 30), (207, 105), (207, 235), (37, 310)]
    nodes = []
    for i, ((x, y), label, subtitle) in enumerate(zip(positions, labels, subtitles)):
        active = i == 1
        background, foreground = ("#171717", "#ffffff") if active else ("#ffffff", "#171717")
        muted, stroke = ("#b8b8b8", "#171717") if active else ("#737373", "#dddddd")
        nodes.append(f'''<g transform="translate({x} {y})">
<rect width="157" height="80" rx="11" fill="{background}" stroke="{stroke}"/>
<text x="15" y="20" font-size="9" font-family="sans-serif" fill="{muted}">0{i+1}</text>
<text x="15" y="43" font-size="15" font-family="sans-serif" font-weight="500" fill="{foreground}">{escape(label)}</text>
<text x="15" y="63" font-size="9" font-family="sans-serif" fill="{muted}">{escape(subtitle)}</text>
</g>''')
    title = "从要求到证据的循环" if zh else "From requirements to evidence"
    description = "模型决定下一步，工具返回观察，测试和差异支撑结论。教学示意，不是内部架构全图。" if zh else "The model chooses actions, tools return observations, and tests and diffs support conclusions. A teaching diagram, not a complete internal architecture."
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="426" viewBox="0 0 400 426" role="img" aria-labelledby="title desc">
<title id="title">{title}</title><desc id="desc">{description}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#969696"/></marker></defs>
<g fill="none" stroke="#969696" stroke-width="1.1" marker-end="url(#arrow)">
<path d="M194 70 H273 Q285 70 285 82 V103"/>
<path d="M285 185 V233"/>
<path d="M207 275 H127 Q115 275 115 287 V307"/>
<path d="M37 350 H28 Q16 350 16 338 V82 Q16 70 28 70 H34" stroke-dasharray="3 5"/>
</g>
<circle cx="285" cy="209" r="3" fill="#ffffff" stroke="#969696"/>
<circle cx="115" cy="298" r="3" fill="#ffffff" stroke="#969696"/>
{''.join(nodes)}
<text x="31" y="225" transform="rotate(-90 31 225)" fill="#858585" font-size="8" letter-spacing=".8" font-family="sans-serif">ITERATE WITH EVIDENCE</text>
</svg>'''


if __name__ == "__main__":
    for language in ("zh", "en"):
        (ROOT / f"site/assets/loop-{language}.svg").write_text(draw(language), encoding="utf-8")
    print("Rendered 2 monochrome SVG diagrams from Python source")
