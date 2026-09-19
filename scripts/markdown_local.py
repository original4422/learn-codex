"""Small escaped Markdown renderer for the documented course subset.

Supports headings, paragraphs, fenced code, links/images, emphasis, flat lists,
quotes, tables and rules. Raw HTML is always escaped. No external dependency.
"""
from __future__ import annotations
import html
import re
from urllib.parse import urlsplit


def slug(text):
    text = re.sub(r"[`*_]", "", text).strip().lower()
    return re.sub(r"[^\w\-\u3400-\u9fff]+", "-", text).strip("-") or "section"


def safe_url(url):
    scheme = urlsplit(html.unescape(url)).scheme.lower()
    return url if scheme in ("", "http", "https", "mailto") else "#"


def inline(text, rewrite=lambda x: x):
    pattern = r"(`+)(.+?)\1|(!?)\[([^\]]+)\]\(([^\s)]+)\)|\*\*(.+?)\*\*|(?<!\*)\*([^*]+)\*(?!\*)"
    chunks, start = [], 0
    for match in re.finditer(pattern, text):
        chunks.append(html.escape(text[start:match.start()]))
        code, content, bang, label, url, strong, em = match.groups()
        if code:
            chunks.append("<code>" + html.escape(content) + "</code>")
        elif url:
            target = html.escape(safe_url(rewrite(url)), quote=True)
            if bang:
                chunks.append(f'<img loading="lazy" src="{target}" alt="{html.escape(label, quote=True)}">')
            else:
                chunks.append(f'<a href="{target}">{inline(label, rewrite)}</a>')
        elif strong:
            chunks.append("<strong>" + inline(strong, rewrite) + "</strong>")
        else:
            chunks.append("<em>" + html.escape(em) + "</em>")
        start = match.end()
    chunks.append(html.escape(text[start:]))
    return "".join(chunks)


def render(source, rewrite=lambda x: x):
    lines, out, headings, used = source.splitlines(), [], [], {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        fence = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if fence:
            marker, language = fence.groups()
            body = []
            index += 1
            while index < len(lines) and not re.match(r"^\s*" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$", lines[index]):
                body.append(lines[index])
                index += 1
            if index == len(lines):
                raise ValueError("Unclosed code fence")
            lang = html.escape(language.strip())
            out.append(f'<div class="code-block"><div class="code-bar"><span>{lang or "text"}</span><button class="copy-code" type="button" aria-label="Copy code">Copy</button></div><pre><code>{html.escape(chr(10).join(body))}</code></pre></div>')
            index += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            hashes, label = heading.groups()
            base = slug(label)
            count = used.get(base, 0)
            used[base] = count + 1
            anchor = base if count == 0 else f"{base}-{count}"
            level = len(hashes)
            out.append(f'<h{level} id="{anchor}">{inline(label, rewrite)}</h{level}>')
            headings.append((level, label, anchor))
            index += 1
            continue
        if re.fullmatch(r"\s*([-*_])(?:\s*\1){2,}\s*", line):
            out.append("<hr>")
            index += 1
            continue
        if index + 1 < len(lines) and "|" in line and re.fullmatch(r"[| :\-]+", lines[index + 1]) and "---" in lines[index + 1]:
            rows = [line]
            index += 2
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(lines[index])
                index += 1
            out.append('<div class="table-scroll"><table>')
            for row_index, row in enumerate(rows):
                tag = "th" if row_index == 0 else "td"
                section = "thead" if row_index == 0 else "tbody"
                if row_index < 2:
                    out.append(f"<{section}>")
                # A pipe inside inline code is represented as &#124; in source.
                cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<{tag}>{inline(cell, rewrite)}</{tag}>" for cell in cells) + "</tr>")
                if row_index == 0:
                    out.append("</thead>")
            if len(rows) > 1:
                out.append("</tbody>")
            out.append("</table></div>")
            continue
        if line.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].startswith(">"):
                quote.append(lines[index][1:].lstrip())
                index += 1
            rendered, _ = render("\n".join(quote), rewrite)
            out.append("<blockquote>" + rendered + "</blockquote>")
            continue
        listing = re.match(r"^\s*(?:([-+*])|([0-9]+)[.)])\s+(.+)$", line)
        if listing:
            ordered = listing.group(2) is not None
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>")
            while index < len(lines):
                match = re.match(r"^\s*(?:([-+*])|([0-9]+)[.)])\s+(.+)$", lines[index])
                if not match or (match.group(2) is not None) != ordered:
                    break
                item = match.group(3)
                index += 1
                while index < len(lines) and lines[index].startswith("  ") and not re.match(r"^\s*([-+*]|[0-9]+[.)])\s", lines[index]):
                    item += " " + lines[index].strip()
                    index += 1
                out.append("<li>" + inline(item, rewrite) + "</li>")
            out.append(f"</{tag}>")
            continue
        para = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not re.match(r"^(#{1,6}\s|>|```|~~~|[-+*]\s|\d+[.)]\s)", lines[index]):
            para.append(lines[index])
            index += 1
        out.append("<p>" + inline("\n".join(para), rewrite) + "</p>")
    return "\n".join(out), headings
