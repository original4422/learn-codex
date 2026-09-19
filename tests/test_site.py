import sys
import re
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from markdown_local import render, inline
from build_site import rewrite_url, ROOT, PAGES


class MarkdownTests(unittest.TestCase):
    def test_code_does_not_execute_or_turn_into_links(self):
        body, _ = render('```html\n<script>alert(1)</script> [x](bad)\n```')
        self.assertIn('&lt;script&gt;', body)
        self.assertNotIn('<script>', body)
        self.assertNotIn('<a ', body)

    def test_unsafe_links_cannot_execute(self):
        self.assertIn('href="#"', inline('[bad](javascript:alert%281%29)'))
        self.assertNotIn('href="javascript:', inline('[bad](javascript:alert%281%29)'))

    def test_duplicate_headings_get_distinct_anchors(self):
        body, headings = render('# 同一个标题\n\n## 同一个标题')
        self.assertEqual([h[2] for h in headings], ['同一个标题', '同一个标题-1'])

    def test_unclosed_fence_fails_build(self):
        with self.assertRaises(ValueError):
            render('```python\nprint(1)')

    def test_link_rewriting_preserves_fragments_and_languages(self):
        page = ROOT / 'docs/zh/index.md'
        self.assertEqual(rewrite_url('../en/quickstart.md#install', page), '/en/quickstart.html#install')
        self.assertEqual(rewrite_url('../../src/codex_lab/__main__.py', page), '/files/src/codex_lab/__main__.py')

    def test_link_cannot_escape_repository(self):
        with self.assertRaises(ValueError):
            rewrite_url('../../../../secret', ROOT / 'docs/zh/index.md')

    def test_table_and_nested_inline_code(self):
        body, _ = render('| Input | Result |\n| --- | --- |\n| `--json` | **events** |')
        self.assertIn('<thead>', body)
        self.assertIn('<code>--json</code>', body)
        self.assertIn('<strong>events</strong>', body)


class TranslationTests(unittest.TestCase):
    def test_complete_language_coverage(self):
        for lang in ('zh', 'en'):
            self.assertEqual({p.stem for p in (ROOT / 'docs' / lang).glob('*.md')}, set(PAGES))

    def test_matching_section_and_code_block_coverage(self):
        for slug in PAGES:
            pair = [(ROOT / 'docs' / lang / (slug + '.md')).read_text() for lang in ('zh', 'en')]
            with self.subTest(page=slug):
                self.assertEqual(pair[0].count('\n## '), pair[1].count('\n## '))
                self.assertEqual(re.findall(r'^```\w*', pair[0], re.M), re.findall(r'^```\w*', pair[1], re.M))

    def test_chapters_are_substantive_and_have_runnable_examples(self):
        for lang in ('zh', 'en'):
            for slug in PAGES[2:13]:
                text = (ROOT / 'docs' / lang / (slug + '.md')).read_text()
                with self.subTest(lang=lang, slug=slug):
                    self.assertGreater(len(text), 1800)
                    self.assertGreaterEqual(text.count('\n## '), 4)
                    self.assertIn('```', text)
                    self.assertRegex(text, r'https://(?:github.com/openai|learn.chatgpt.com|developers.openai.com)')


if __name__ == '__main__':
    unittest.main()
