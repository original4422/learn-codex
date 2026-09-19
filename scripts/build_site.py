"""Build a portable bilingual site; fail on missing translations or local links."""
from __future__ import annotations
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
from markdown_local import render

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PAGES = ["index", "quickstart", "01-first-task", "02-workflow", "03-agent-loop", "04-instructions", "05-skills", "06-safety", "07-context", "08-mcp", "09-subagents", "10-automation", "11-desktop", "playground", "labs", "source-map", "sources", "contributing", "acceptance"]
LABELS = {
    "zh": {"start": "开始学习", "course": "课程 · 01—11", "reference": "实验与参考", "search": "搜索课程", "menu": "打开目录", "onpage": "本页内容", "next": "下一篇", "previous": "上一篇", "done": "标记为已学", "undone": "已完成学习", "progress": "学习进度", "foot": "以证据理解工具，以实践形成方法。", "home": "课程首页", "searchhint": "搜索标题、概念与命令…", "close": "关闭", "empty": "没有匹配的页面", "hero": "把 Codex 用好。<br><em>也把它看懂。</em>", "intro": "从一个真实改动出发，走过工具循环、指令、隔离与自动化。每一步都有代码、有实验、有可复查的证据。", "begin": "从第一个任务开始", "lab": "打开机制实验室", "badge": "一份可运行的学习手册", "metric1": "双语课程", "metric2": "贯穿项目", "metric3": "第三方运行依赖", "language": "English"},
    "en": {"start": "Start here", "course": "Course · 01—11", "reference": "Labs & references", "search": "Search course", "menu": "Open navigation", "onpage": "On this page", "next": "Next", "previous": "Previous", "done": "Mark as learned", "undone": "Completed", "progress": "Your progress", "foot": "Understand tools through evidence. Build a practice through experiments.", "home": "Course home", "searchhint": "Search titles, concepts and commands…", "close": "Close", "empty": "No matching pages", "hero": "Use Codex well.<br><em>Understand it, too.</em>", "intro": "Start with a real change. Follow the tool loop, instructions, isolation and automation—with runnable code and evidence you can inspect.", "begin": "Start your first task", "lab": "Explore the mechanism lab", "badge": "A runnable field guide", "metric1": "bilingual lessons", "metric2": "continuous case", "metric3": "third-party dependencies", "language": "中文"}}


def esc(value):
    return html.escape(str(value), quote=True)


def titles_for(lang):
    return {slug: re.search(r"^# (.+)$", (ROOT / "docs" / lang / f"{slug}.md").read_text(), re.M).group(1) for slug in PAGES}


def rewrite_url(url, page):
    parts = urlsplit(url)
    if parts.scheme or url.startswith(("#", "/")):
        return url
    path = (page.parent / unquote(parts.path)).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Link escapes repository: {page}: {url}")
    if path.is_relative_to(ROOT / "docs") and path.suffix == ".md":
        target = "/" + str(path.relative_to(ROOT / "docs").with_suffix(".html"))
    elif path.is_relative_to(ROOT / "site/assets"):
        target = "/assets/" + str(path.relative_to(ROOT / "site/assets"))
    else:
        target = "/files/" + str(path.relative_to(ROOT))
    if parts.fragment:
        target += "#" + parts.fragment
    return target


def diagram(lang):
    return f'<img class="hero-diagram" src="/assets/loop-{lang}.svg" alt="{"观察、行动、验证的循环" if lang == "zh" else "The observe, act and verify loop"}">'


def playground(lang):
    zh = lang == "zh"
    return f'''<section class="simulator" aria-labelledby="sim-title">
    <div class="eyebrow">INTERACTIVE / {"教学简化" if zh else "TEACHING MODEL"}</div>
    <h2 id="sim-title">{"一次工具循环，逐步看" if zh else "A tool loop, one step at a time"}</h2>
    <p>{"这段交互在浏览器内运行固定脚本，不调用模型。" if zh else "This interaction runs a fixed browser script. It makes no model calls."}</p>
    <label for="scenario">{"选择实验" if zh else "Scenario"}</label>
    <select id="scenario"><option value="success">{"工具成功" if zh else "Tool succeeds"}</option><option value="failure">{"工具失败" if zh else "Tool fails"}</option><option value="budget">{"预算耗尽" if zh else "Budget exhausted"}</option></select>
    <div class="sim-stages"><span data-stage="0">{"要求" if zh else "Request"}</span><span data-stage="1">{"决策" if zh else "Decision"}</span><span data-stage="2">{"工具" if zh else "Tool"}</span><span data-stage="3">{"验证" if zh else "Verify"}</span></div>
    <pre id="sim-log" aria-live="polite"></pre><div class="sim-actions"><button class="button" id="step">{"下一步" if zh else "Next step"}</button><button class="button secondary" id="reset">{"重置" if zh else "Reset"}</button></div></section>
    <section class="simulator" aria-labelledby="policy-title"><div class="eyebrow">TWO INDEPENDENT CHECKS</div><h2 id="policy-title">{"审批与隔离：分开判断" if zh else "Approval and isolation: separate decisions"}</h2>
    <p>{"简化策略模型：先检查路径边界，再检查人工批准。它没有创建 OS 沙箱。" if zh else "A simplified policy: check the path boundary, then human approval. It creates no OS sandbox."}</p>
    <label class="check-label"><input id="inside" type="checkbox" checked> {"写入位置在允许目录中" if zh else "Write target is in the allowed directory"}</label>
    <label class="check-label"><input id="approved" type="checkbox"> {"已获得所需批准" if zh else "Required approval has been granted"}</label>
    <output id="policy-result" aria-live="polite"></output></section>'''


def page_html(lang, slug, titles):
    labels = LABELS[lang]
    page = ROOT / "docs" / lang / f"{slug}.md"
    source = page.read_text()
    body, headings = render(source, lambda url: rewrite_url(url, page))
    title = titles[slug]
    other = "en" if lang == "zh" else "zh"
    nav = []
    for label, group in [(labels["start"], PAGES[:2]), (labels["course"], PAGES[2:13]), (labels["reference"], PAGES[13:])]:
        nav.append(f'<div class="nav-group"><div class="nav-label">{label}</div>')
        for item in group:
            active = ' aria-current="page" class="active"' if slug == item else ""
            number = item[:2] if re.match(r"\d", item) else "·"
            name = re.sub(r"^\d+[.．、·\s—:：-]+", "", titles[item])
            nav.append(f'<a href="/{lang}/{item}.html"{active}><span class="nav-number">{number}</span><span>{esc(name)}</span></a>')
        nav.append("</div>")
    toc = "".join(f'<a href="#{anchor}">{esc(label)}</a>' for level, label, anchor in headings if level == 2)
    index = PAGES.index(slug)
    prev_link = f'<a href="/{lang}/{PAGES[index-1]}.html"><small>← {labels["previous"]}</small>{esc(titles[PAGES[index-1]])}</a>' if index else "<span></span>"
    next_link = f'<a href="/{lang}/{PAGES[index+1]}.html"><small>{labels["next"]} →</small>{esc(titles[PAGES[index+1]])}</a>' if index + 1 < len(PAGES) else "<span></span>"
    hero = ""
    if slug == "index":
        hero = f'''<section class="hero"><div class="hero-copy"><span class="eyebrow">LEARN / CODEX — {labels['badge']}</span><h1>{labels['hero']}</h1><p>{labels['intro']}</p><div class="hero-actions"><a class="button" href="/{lang}/quickstart.html">{labels['begin']} <span>↗</span></a><a class="text-link" href="/{lang}/playground.html">{labels['lab']} →</a></div><div class="metrics"><span><b>11</b>{labels['metric1']}</span><span><b>01</b>{labels['metric2']}</span><span><b>0</b>{labels['metric3']}</span></div></div><div class="hero-visual">{diagram(lang)}<span class="diagram-caption">01 / OBSERVE · ACT · VERIFY</span></div></section>'''
        body = re.sub(r"^<h1[^>]*>.*?</h1>", "", body, count=1)
    if slug == "playground":
        body += playground(lang)
    read_minutes = max(2, round(len(source) / (700 if lang == "zh" else 1300)))
    mark_done = f'<button class="button secondary" id="mark-done" data-done="{labels["done"]}" data-undone="{labels["undone"]}">{labels["done"]}</button>' if slug[:2].isdigit() else ''
    return f'''<!doctype html><html lang="{'zh-CN' if lang == 'zh' else 'en'}"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <meta name="description" content="{esc(labels['intro'])}"><meta name="color-scheme" content="light dark">
    <title>{esc(title)} · learn-codex</title><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css">
    <link rel="alternate" hreflang="{other}" href="/{other}/{slug}.html"><script src="/assets/app.js" defer></script></head>
    <body data-lang="{lang}" data-page="{slug}"><a class="skip" href="#main">{'跳到正文' if lang == 'zh' else 'Skip to content'}</a>
    <header class="site-header"><a class="brand" href="/{lang}/index.html"><span class="brand-mark">c_</span>learn<span>codex</span></a><span class="header-note">A FIELD GUIDE FOR BUILDERS</span><div class="header-actions"><button id="search-open" aria-label="{labels['search']}"><span>⌕</span> <span class="search-label">{labels['search']}</span><kbd>/</kbd></button><a class="language" href="/{other}/{slug}.html" lang="{other}" aria-label="{'Switch to English' if other == 'en' else '切换为中文'}">{labels['language']}</a><button id="theme" aria-label="{'切换主题' if lang == 'zh' else 'Toggle theme'}">◐</button><button id="menu" aria-label="{labels['menu']}" aria-expanded="false">☰</button></div></header>
    <div class="layout"><aside class="sidebar" id="sidebar"><nav aria-label="{labels['course']}">{''.join(nav)}</nav><div class="progress"><span>{labels['progress']}</span><span id="progress-count">0 / 11</span><div class="progress-track"><div id="progress-fill"></div></div></div><div class="version-note"><span class="status-dot"></span>CLI 0.155.1<br><small>Source-pinned · 2026-09-19</small></div></aside>
    <main id="main" class="{'home' if slug == 'index' else ''}">{hero}<div class="reading-layout"><article><div class="article-meta"><span>{'学习手册' if lang == 'zh' else 'FIELD NOTES'}</span><span>{read_minutes} MIN READ</span></div>{body}<div class="article-end">{'以运行结果为准，保留验证证据。' if lang == 'zh' else 'Check the result. Keep the evidence.'}</div>{mark_done}<nav class="page-nav" aria-label="{'篇章导航' if lang == 'zh' else 'Page navigation'}">{prev_link}{next_link}</nav></article><aside class="toc"><span class="nav-label">{labels['onpage']}</span>{toc}<a class="source-link" href="/files/docs/{lang}/{slug}.md">{'查看 Markdown 源文' if lang == 'zh' else 'Read Markdown source'} ↗</a></aside></div><footer><span>learn-codex / v1</span><span>{labels['foot']}</span><span>Independent educational project · MIT</span></footer></main></div>
    <dialog id="search-dialog"><div class="search-top"><input id="search-input" type="search" placeholder="{labels['searchhint']}" aria-label="{labels['search']}"><button id="search-close" aria-label="{labels['close']}">×</button></div><div id="search-results" data-empty="{labels['empty']}" aria-live="polite"></div><div class="search-footer">Esc · {labels['close']}</div></dialog></body></html>'''


def build():
    for lang in ("zh", "en"):
        actual = {p.stem for p in (ROOT / "docs" / lang).glob("*.md")}
        if actual != set(PAGES):
            raise ValueError(f"{lang}: missing {set(PAGES)-actual}, unregistered {actual-set(PAGES)}")
    if DIST.is_symlink():
        raise ValueError("dist must be a generated directory, not a symbolic link")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "site/assets", DIST / "assets", dirs_exist_ok=True)
    files = DIST / "files"
    files.mkdir(exist_ok=True)
    for directory in ("docs", "src", "scripts", "examples", "tests", "references", "reports"):
        source = ROOT / directory
        if source.exists():
            shutil.copytree(source, files / directory, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info", ".cache", ".local", ".venv", "live-*"))
    for name in ("README.md", "README.en.md", "LICENSE", "AGENTS.md", "PROJECT_BRIEF.md", "pyproject.toml", "CONTRIBUTING.md"):
        if (ROOT / name).exists():
            shutil.copy2(ROOT / name, files / name)
    for lang in ("zh", "en"):
        dest = DIST / lang
        dest.mkdir(exist_ok=True)
        titles = titles_for(lang)
        index = []
        for slug in PAGES:
            (dest / f"{slug}.html").write_text(page_html(lang, slug, titles))
            content = (ROOT / "docs" / lang / f"{slug}.md").read_text()
            plain = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", content)
            plain = re.sub(r"[`#*|]", " ", plain)
            plain = re.sub(r"\s+", " ", plain)
            index.append({"title": titles[slug], "url": f"/{lang}/{slug}.html", "text": plain})
        (dest / "search.json").write_text(json.dumps(index, ensure_ascii=False))
    shutil.copy2(DIST / "zh/index.html", DIST / "index.html")
    print(f"Built {len(PAGES) * 2 + 1} pages → {DIST}")


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for name in ("href", "src"):
            if attrs.get(name):
                self.links.append(attrs[name])
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise ValueError(f"Duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])


def validate():
    parsed = {}
    for path in DIST.rglob("*.html"):
        parser = LinkCollector()
        parser.feed(path.read_text())
        parsed[path] = parser
    errors, links = [], 0
    for path, parser in parsed.items():
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            target = ((DIST / unquote(parts.path.lstrip("/"))) if parts.path.startswith("/") else (path.parent / unquote(parts.path))).resolve() if parts.path else path
            if target.is_dir():
                target /= "index.html"
            links += 1
            if not target.is_file():
                errors.append(f"{path.relative_to(DIST)} → missing {link}")
            elif parts.fragment and target in parsed and unquote(parts.fragment) not in parsed[target].ids:
                errors.append(f"{path.relative_to(DIST)} → missing anchor {link}")
    if errors:
        raise ValueError("\n".join(errors))
    print(f"Validated {len(parsed)} HTML pages, {links} local links/assets and all translated routes")
    return {"pages": len(parsed), "local_links": links}


if __name__ == "__main__":
    build()
    validate()
