"""Regression checks for the generated catalog and lossless source accounting."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads((ROOT/'data/tools.json').read_text())
        cls.tools = {t['id']: t for t in cls.rows}
        cls.report = json.loads((ROOT/'data/tools.merge-report.json').read_text())
        cls.provenance = json.loads((ROOT/'data/tools.provenance.json').read_text())
        cls.excluded = json.loads((ROOT/'data/tools.excluded.json').read_text())

    def test_every_input_record_accounted_for_exactly_once(self):
        sources = [s for group in self.provenance.values() for s in group]
        sources.extend(t['source'] for t in self.excluded)
        identities = [(s['file'], s['record']) for s in sources]
        self.assertEqual(len(identities), len(set(identities)))
        expected = {(f,i) for f,n in self.report['input_counts'].items() for i in range(1,n+1)}
        self.assertEqual(set(identities), expected)

    def test_aliases_merge(self):
        names = {s['original_name'] for s in self.provenance['bolt-new']}
        self.assertEqual(names, {'Bolt', 'Bolt.new'})
        self.assertEqual(len(self.provenance['bolt-new']), 3)
        for tool_id, names in [('gemini', {'Google Gemini', 'Gemini'}), ('perplexity', {'Perplexity AI', 'Perplexity'})]:
            self.assertEqual({s['original_name'] for s in self.provenance[tool_id]}, names)

    def test_shared_sites_do_not_merge_different_products(self):
        for tool_id in ['chatgpt', 'chatgpt-agent', 'chatgpt-images', 'gemini', 'gemini-nano-banana', 'dall-e', 'stable-diffusion', 'figma-ai', 'figma-make']:
            self.assertIn(tool_id, self.tools)

    def test_no_fabricated_missing_fields(self):
        for row in self.rows:
            original = self.provenance[row['id']]
            if not any(s['raw_record'].get('plus') for s in original):
                self.assertEqual(row['advantages'], '')
            if not any(s['raw_record'].get('minus') for s in original):
                self.assertEqual(row['disadvantages'], '')

    def test_pricing_symbols_and_research_coverage(self):
        research = json.loads((ROOT/'data/pricing-research.json').read_text())
        symbols = {'free': '$', 'freemium': '$$', 'paid': '$$$'}
        self.assertEqual(len(self.rows), 470)
        self.assertEqual(self.report['missing_price'], 0)
        self.assertEqual(len(research), 197)
        for row in self.rows:
            self.assertIn(row['price'], symbols.values())
            if row['id'] in research:
                entry = research[row['id']]
                self.assertEqual(row['price'], symbols[entry['model']])
                self.assertTrue(entry['sources'] and entry['basis'] and entry['checked_on'])
                self.assertTrue(all(url.startswith('https://') for url in entry['sources']))
        for tool_id in ['harvey', 'sunsama', 'stager-ai', 'nabla']:
            self.assertEqual(self.tools[tool_id]['price'], '$$$')
        self.assertEqual(self.tools['coursebox']['price'], '$$')
        self.assertEqual(self.tools['aider']['price'], '$')

    def test_schema_and_taxonomy(self):
        fields = ['id', 'name', 'description', 'price', 'tags', 'url', 'short_description', 'advantages', 'disadvantages']
        tags = set(json.loads((ROOT/'data/tool-tags.json').read_text())['tags'])
        self.assertEqual(len(self.rows), len(self.tools))
        for row in self.rows:
            self.assertEqual(list(row), fields)
            self.assertTrue(set(row['tags']) <= tags)
            self.assertTrue(row['url'].startswith('https://'))

    def test_originals_unchanged(self):
        for file, digest in self.report['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/file).read_bytes()).hexdigest(), digest)

    def test_placeholder_separation(self):
        self.assertEqual(len(self.excluded), 270)
        self.assertTrue(all(not t['name'].startswith('AI_Tool_') for t in self.rows))
        self.assertTrue(all(t['tool']['url'] == '' for t in self.excluded))

if __name__ == '__main__':
    unittest.main()
