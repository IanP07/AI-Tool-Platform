"""Merge the supplied catalogs without modifying originals. Run from any directory."""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data'
FIELDS = ['id', 'name', 'description', 'price', 'tags', 'url', 'short_description', 'advantages', 'disadvantages']
PRICE_SYMBOLS = {'free': '$', 'freemium': '$$', 'paid': '$$$'}

# Explicit controlled vocabulary: task families, not arbitrary vendor keywords.
USE_CASE_GROUPS = {
    'coding': 'ai-code-editor coding-agent code-review image-to-code',
    'app-website-building': 'build-app-from-prompt',
    'ai-development': 'run-llms-locally build-ai-agents api-llm-access',
    'workflow-automation': 'workflow-automation browser-agent',
    'voice-assistants': 'voice-agents',
    'chat-assistants': 'general-assistant',
    'research': 'deep-research',
    'document-processing': 'chat-with-documents document-data-extraction summarize-content',
    'meetings-transcription': 'meeting-notes transcription',
    'audio-music': 'text-to-speech music-generation audio-cleanup',
    'image-creation-editing': 'generate-images edit-images remove-background upscale-images',
    'design-branding': 'logo-and-brand ui-design',
    'video-creation-editing': 'text-to-video ai-video-editing long-to-short-clips subtitles-and-captions ai-avatars',
    'translation-localization': 'translation video-dubbing',
    'writing-editing': 'write-content grammar-and-editing ai-detection-and-humanize',
    'marketing-seo': 'marketing-copy seo-content social-media-posts',
    'productivity-knowledge': 'email-assistant notes-and-knowledge',
    'presentations': 'presentations',
    'data-analysis': 'spreadsheets-and-data',
    'customer-support': 'customer-support-bot',
    'sales-outreach': 'sales-and-outreach',
    'education-learning': 'learning-and-tutoring',
    '3d-game-development': '3d-generation game-dev',
    'recruiting-careers': 'resume-and-career',
}
USE_CASE_MAP = {key: tag for tag, keys in USE_CASE_GROUPS.items() for key in keys.split()}
MARKET_MAP = {
    'accounting': 'finance-accounting', 'expense-management': 'finance-accounting', 'finance': 'finance-accounting',
    'ad-creative': 'marketing-seo', 'marketing': 'marketing-seo', 'copywriting': 'writing-editing',
    'coding': 'coding', 'no-code': 'app-website-building', 'contact-center': 'customer-support',
    'customer-support': 'customer-support', 'design': 'design-branding', 'education': 'education-learning',
    'film-tv': 'video-creation-editing', 'video': 'video-creation-editing', 'podcasting': 'audio-music',
    'healthcare': 'clinical-documentation-care', 'hr': 'recruiting-careers', 'recruiting': 'recruiting-careers',
    'knowledge-management': 'productivity-knowledge', 'productivity': 'productivity-knowledge',
    'legal': 'legal-contract-work', 'real-estate': 'property-management-marketing', 'sales': 'sales-outreach',
}
CSV_MAP = {
    '3D AI': '3d-game-development', 'AI Platform': 'ai-development', 'Audio AI': 'audio-music',
    'Chatbot': 'chat-assistants', 'Coding Assistant': 'coding', 'Data Science AI': 'data-analysis',
    'Design AI': 'design-branding', 'Image Generation': 'image-creation-editing', 'Marketing AI': 'marketing-seo',
    'Meeting AI': 'meetings-transcription', 'Productivity': 'productivity-knowledge', 'Research AI': 'research',
    'Search AI': 'research', 'Translation AI': 'translation-localization', 'Video AI': 'video-creation-editing',
    'Voice AI': 'audio-music', 'Writing Assistant': 'writing-editing',
}

# Only reviewed aliases are merged; matching a hostname alone is NOT sufficient.
ALIASES = {
    'google-gemini': 'gemini', 'perplexity-ai': 'perplexity', 'runway-ml': 'runway',
    'grammarly-ai': 'grammarly', 'jasper-ai': 'jasper', 'canva-ai': 'canva-magic-studio',
    'fin': 'intercom-fin', 'fin-by-intercom': 'intercom-fin',
    'augment-code-cosmos': 'augment-code', 'bolt': 'bolt-new',
    'figma-ai-figma-make': 'figma-ai', 'v0-by-vercel': 'v0',
    'surfer': 'surfer-seo', 'windsurf-editor': 'windsurf',
    'devin-desktop-formerly-windsurf': 'windsurf',
    'builder-io-visual-copilot': 'builder-io', 'replit-agent': 'replit',
    'otter-ai': 'otter-ai', 'kaggle-ai': 'kaggle',
}
# CSV-only legacy products remain distinct from newer products/models.
URL_ENRICHMENT = {
    'stable-diffusion': 'https://stability.ai/stable-image',
    'pictory': 'https://pictory.ai/',
    'kaggle': 'https://www.kaggle.com/',
    'codeium': 'https://docs.devin.ai/windsurf/plugins/getting-started',
    'replit-ghostwriter': 'https://replit.com/',
    'dall-e': 'https://openai.com/index/dall-e-3/',
}
# Override overly broad market labels with use cases supported by the source copy.
TWO_TAGS = {
    'elevenlabs': ['audio-music'], 'pika': ['video-creation-editing'],
    'kapwing': ['video-creation-editing'], 'veed': ['video-creation-editing'],
    'luma-dream-machine': ['video-creation-editing'],
    'luma-ai': ['image-creation-editing', 'video-creation-editing', 'audio-music'],
    'photoroom': ['image-creation-editing'], 'clipdrop': ['image-creation-editing'],
    'runway': ['video-creation-editing'], 'heygen': ['video-creation-editing'],
    'meetgeek': ['meetings-transcription'], 'fathom': ['meetings-transcription'],
    'otter-ai': ['meetings-transcription'], 'fireflies-ai': ['meetings-transcription'],
    'tl-dv': ['meetings-transcription'], 'bardeen': ['workflow-automation'],
    'basedash': ['data-analysis'],
}


def slug(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def url_key(value):
    p = urlsplit(value)
    return (p.hostname or '').lower().removeprefix('www.') + p.path.rstrip('/')


def normalize_url(value):
    p = urlsplit(clean(value))
    if p.scheme not in ('http', 'https') or not p.hostname:
        raise ValueError(f'Invalid source URL: {value}')
    return urlunsplit((p.scheme, p.netloc, p.path, p.query, ''))


def key_for(row, source):
    raw = slug(row.get('slug') or row.get('id') or row['name']) if source != 'csv' else slug(row['name'])
    # one.json has an extra bolt-new entry under a different slug.
    if row['name'] == 'Bolt.new':
        raw = 'bolt-new'
    return ALIASES.get(raw, ALIASES.get(slug(row['name']), raw))


def main():
    one = json.loads((ROOT / 'one.json').read_text())
    two = json.loads((ROOT / 'two.json').read_text())
    with (ROOT / 'global_ai_tools_dataset_2026.csv').open(newline='') as f:
        csv_rows = list(csv.DictReader(f))
    records = []
    excluded = []
    for source, rows in [('one', one['tools']), ('two', two['tools']), ('csv', csv_rows)]:
        for index, raw in enumerate(rows, 1):
            row = dict(raw)
            if source == 'csv':
                row['name'] = row['Tool_Name']
            key = key_for(row, source)
            record = dict.fromkeys(FIELDS, '')
            record.update(id=key, name=clean(row['name']))
            if source == 'one':
                record.update(description=clean(row['tagline']), short_description=clean(row['tagline']),
                              price=clean(row['pricing']).lower(), advantages=clean(row['plus']),
                              disadvantages=clean(row['minus']), url=normalize_url(row['url']),
                              tags=sorted({USE_CASE_MAP[x] for x in row['use_cases']}))
            elif source == 'two':
                record.update(description=clean(row['summary']), short_description=clean(row['tagline']),
                              url=normalize_url(row['url']),
                              tags=sorted(set(TWO_TAGS.get(key, [MARKET_MAP[x] for x in row['markets']]))))
            else:
                record.update(description=clean(row['Main_Function']), short_description=clean(row['Main_Function']),
                              price=clean(row['Pricing_Model']).lower(), tags=[CSV_MAP[row['Category']]],
                              url=URL_ENRICHMENT.get(key, ''))
            source_ref = {'file': {'one': 'one.json', 'two': 'two.json', 'csv': 'global_ai_tools_dataset_2026.csv'}[source],
                          'record': index, 'original_id': raw.get('slug', raw.get('id', raw.get('Tool_ID', ''))),
                          'original_name': record['name'], 'original_url': raw.get('url', ''),
                          'attribution_url': raw.get('page', ''), 'raw_record': raw}
            if re.fullmatch(r'AI_Tool_\d+', record['name']):
                excluded.append({'reason': 'Placeholder name with no identifiable product or official URL', 'tool': record, 'source': source_ref})
            else:
                records.append({'tool': record, 'source': source, 'reference': source_ref})

    # Match exact normalized names as well as reviewed source IDs and aliases.
    parents = list(range(len(records)))
    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    merge_edges = []
    for i, record in enumerate(records):
        t = record['tool']
        for match in [('id', t['id']), ('name', slug(t['name']))]:
            if match in seen:
                j = seen[match]
                if root(i) != root(j):
                    parents[root(i)] = root(j)
                    merge_edges.append({'left': records[j]['reference']['original_name'], 'right': t['name'], 'matched_by': list(match)})
            else:
                seen[match] = i
    groups = defaultdict(list)
    for i, record in enumerate(records):
        groups[root(i)].append(record)
    result, audit, conflicts = [], {}, []
    for group in groups.values():
        preferred = sorted(group, key=lambda r: {'one': 0, 'two': 1, 'csv': 2}[r['source']])
        base = preferred[0]['tool']
        merged = dict(base)
        merged['name'] = {'builder-io': 'Builder.io', 'replit': 'Replit', 'kaggle': 'Kaggle'}.get(base['id'], base['name'])
        # Prefer richer descriptions, except the November Windsurf source supersedes June's rebrand copy.
        descriptions = sorted(group, key=lambda r: {'two': 0, 'one': 1, 'csv': 2}[r['source']])
        if base['id'] == 'windsurf':
            descriptions = preferred
        for field in ['description', 'short_description']:
            merged[field] = next((r['tool'][field] for r in descriptions if r['tool'][field]), '')
        for field in ['price', 'url']:
            merged[field] = next((r['tool'][field] for r in preferred if r['tool'][field]), '')
        for field in ['advantages', 'disadvantages']:
            merged[field] = '\n'.join(dict.fromkeys(r['tool'][field] for r in preferred if r['tool'][field]))
        merged['tags'] = sorted({tag for r in group for tag in r['tool']['tags']})
        for field in ['price', 'url']:
            values = list(dict.fromkeys(r['tool'][field] for r in preferred if r['tool'][field]))
            distinct = set(url_key(v) for v in values) if field == 'url' else set(values)
            if len(distinct) > 1:
                conflicts.append({'id': merged['id'], 'field': field, 'values': values, 'selected': merged[field],
                                  'resolution': 'Prefer one.json (November snapshot), then two.json, then CSV; retain alternatives in audit.'})
        result.append(merged)
        audit[merged['id']] = [r['reference'] for r in preferred]
    result.sort(key=lambda t: t['name'].casefold())
    source_price_counts = dict(Counter(t['price'] for t in result))
    research = json.loads((OUT / 'pricing-research.json').read_text())
    assert set(research) <= {t['id'] for t in result}, 'Research contains unknown tool IDs'
    for t in result:
        if t['id'] in research:
            entry = research[t['id']]
            assert entry['sources'] and entry['basis'] and entry['checked_on']
            assert entry['price'] == PRICE_SYMBOLS[entry['model']]
            t['price'] = entry['price']
        else:
            # Missing/open-source models must be researched, never silently defaulted.
            t['price'] = PRICE_SYMBOLS[t['price']]
    for entry in excluded:
        entry['tool']['price'] = PRICE_SYMBOLS[entry['tool']['price']]
    for conflict in conflicts:
        if conflict['field'] == 'price':
            conflict['final_price'] = next(t['price'] for t in result if t['id'] == conflict['id'])
    allowed_tags = set(USE_CASE_GROUPS) | set(MARKET_MAP.values()) | set(CSV_MAP.values())
    assert len({t['id'] for t in result}) == len(result)
    for t in result:
        assert list(t) == FIELDS
        assert t['name'] and t['description'] and t['short_description'] and t['tags'], t
        assert t['url'], t
        normalize_url(t['url'])
        assert not any(host in urlsplit(t['url']).netloc for host in ['ai4sale.ai', 'toolify.ai', 'futurepedia.io'])
        assert set(t['tags']) <= allowed_tags
        assert t['tags'] == sorted(set(t['tags']))
        assert t['price'] in PRICE_SYMBOLS.values()
        # Never fabricate pros/cons from summary, capabilities, or web enrichment.
        for field, original in [('advantages', 'plus'), ('disadvantages', 'minus')]:
            expected = '\n'.join(dict.fromkeys(clean(s['raw_record'].get(original)) for s in audit[t['id']] if clean(s['raw_record'].get(original))))
            assert t[field] == expected
    inputs = {'one.json': len(one['tools']), 'two.json': len(two['tools']), 'global_ai_tools_dataset_2026.csv': len(csv_rows)}
    merged_count = len(records) - len(result)
    assert sum(inputs.values()) == len(result) + merged_count + len(excluded)
    report = {
        'input_counts': inputs, 'total_input_records': sum(inputs.values()),
        'unique_tools': len(result), 'duplicate_records_merged': merged_count,
        'merged_groups': sum(len(v) > 1 for v in audit.values()), 'placeholder_records_separated': len(excluded),
        'two_json_declared_count': two['count'], 'two_json_actual_count': len(two['tools']),
        'missing_price': sum(not t['price'] for t in result),
        'price_counts': dict(sorted(Counter(t['price'] for t in result).items())),
        'source_price_counts': source_price_counts,
        'pricing_research_count': len(research),
        'missing_advantages': sum(not t['advantages'] for t in result),
        'missing_disadvantages': sum(not t['disadvantages'] for t in result),
        'tag_counts': dict(sorted(Counter(tag for t in result for tag in t['tags']).items())),
        'source_sha256': {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in inputs},
        'field_conflicts': conflicts, 'merge_decisions': merge_edges,
        'url_enrichments': URL_ENRICHMENT,
        'notes': [
            'All input records accounted for: unique tools + merged duplicates + separated placeholders.',
            'Source URLs are vendor/product/docs/repository links, never directory listing pages. Existing URLs were not all live-checked.',
            'Price symbols encode models: $ free, $$ freemium, $$$ paid; they are not dollar amounts or relative costs.',
            'Missing and open-source source models are classified using pricing-research.json. Other source models are mapped directly, not live reverified.',
            'Research notes distinguish explicit plans, software licensing scope and inferred commercial classifications. Trials alone are not freemium.',
            'Related products sharing a URL or vendor remain separate unless their identity was explicitly matched.',
            'DALL-E, Stable Diffusion, Codeium plugins and Replit Ghostwriter remain distinct from newer models, interfaces and agents.',
            'No assertions about current product availability are made for legacy records.',
        ],
    }
    taxonomy = {'tags': sorted(allowed_tags), 'use_case_map': USE_CASE_MAP, 'market_map': MARKET_MAP, 'csv_category_map': CSV_MAP, 'tool_overrides': TWO_TAGS}
    OUT.mkdir(exist_ok=True)
    for file, data in [('tools.json', result), ('tools.merge-report.json', report), ('tools.provenance.json', audit), ('tools.excluded.json', excluded), ('tool-tags.json', taxonomy)]:
        (OUT / file).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in report.items() if k in ['input_counts','unique_tools','duplicate_records_merged','merged_groups','placeholder_records_separated','missing_price','missing_advantages','missing_disadvantages','tag_counts']}, indent=2))

if __name__ == '__main__':
    main()
