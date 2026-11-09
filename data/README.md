# Normalized tool catalog

## CSV pricing edition

`tools.csv` contains the same 470 tools with blank IDs and this column order:

```text
id,name,price,tags,url,short_description,description,advantages,disadvantages
```

The CSV replaces symbolic prices with researched amounts and billing details. The target is the lowest paid plan, with any free tier noted. Monthly billing is preferred; annual commitments and monthly equivalents of annual or quarterly payments are explicitly labeled. Per-user fees, usage charges, one-time purchases, regional currencies, and sales quotes retain their actual units. Trials are distinguished from permanent free tiers. A free self-hosted license does not include hardware or third-party API costs.


Research was performed November 8, 2026. `actual-pricing-research.json` records sources, notes, and verification status by the original JSON tool ID. **37 entries still need verification** because an amount, billing term, currency, current plan, or product availability could not be established reliably. Missing amounts are explicitly marked unavailable; tentative published figures are flagged. Browser rendering was unavailable, and several public pages returned loading placeholders. The dataset does not claim all 470 tools have a verified numeric monthly price.

The original `tools.json` retains its symbolic classification described below. Regenerating that JSON does not regenerate this separately researched CSV. Names, descriptions, tags, URLs, advantages, disadvantages, row order, and blank CSV IDs are preserved.

`tools.json` is the combined catalog, using exactly these fields in order:

```json
{
  "id": "tool-slug",
  "name": "Tool name",
  "description": "Source description or summary",
  "price": "$$",
  "tags": ["coding", "app-website-building"],
  "url": "https://vendor.example/product",
  "short_description": "Source tagline or main function",
  "advantages": "",
  "disadvantages": ""
}
```

## Results

- Inputs: 328 records from `one.json`, 200 from `two.json`, and 300 CSV rows.
- Output: 470 unique tool records, after merging 88 duplicate records across 77 groups.
- Separately preserved: 270 CSV placeholder rows named `AI_Tool_31` through `AI_Tool_300`. These have no identifiable products or vendor URLs and are in `tools.excluded.json`, with normalized fields and their original rows.
- `two.json` declares a count of 1,016 but only contains 200 records. No missing records were fabricated.
- 28 normalized task categories; tools can have multiple tags.
- All 470 tools have a pricing symbol. The 135 missing prices and 62 open-source labels were researched and classified. 143 tools have no supplied advantages or disadvantages.

Pricing totals: `$`: 44, `$$`: 262, `$$$`: 164.

## Field rules

- IDs are deterministic source slugs, with an explicit alias map for duplicates. Names and URLs alone are not fuzzily merged.
- Descriptions prefer the longer summaries from `two.json`, then taglines from `one.json`, then the CSV main function. Missing long-form copy is not invented; in those cases the long and short descriptions can be the same.
- The November `one.json` entry takes precedence for Windsurf/Devin Desktop because the older June summary describes retired branding/features. The complete original copies remain in the provenance file.
- `price` is `$` for free, `$$` for freemium, or `$$$` for paid. These symbols encode access models, not amounts or relative expense. Free trials and introductory credits alone count as paid. Free self-hosted editions with paid hosted or enterprise offerings count as freemium. Free libraries and downloadable models can still incur model API, hosting, hardware, or commercial licensing costs; individual scope limits are recorded in the research notes.
- `pricing-research.json` records sources, checked date, and reasoning for the 197 researched classifications. Some enterprise products do not publish plans; their paid classification is inferred from commercial licensing or sales offerings, as noted in each entry. The other 273 source models are mapped directly and have not been reverified. This is a model classification, not a verification of exact prices or every license entitlement.
- Tags combine source use cases, markets, and CSV categories through the mappings in `tool-tags.json`. Targeted overrides replace misleading industry categories, such as ElevenLabs being listed under design, with the task supported by the source description.
- URLs are the supplied vendor/product sites, official documentation, or official open-source repositories. `page` directory links are retained only as source attribution, never as the tool URL. Existing URLs were not all live-checked.
- Advantages/disadvantages come only from `one.json`'s `plus`/`minus` fields. Missing values are empty strings, never generated from capabilities or marketing copy. Distinct supplied statements are merged with newlines.
- Conflicting source prices and URLs use `one.json`, then `two.json`, then CSV. Research overrides the selected source price where available, then pricing symbols are applied. Price conflicts retain the original selected model and final symbol in the merge report. Source contents may be outdated; the conversion does not certify their claims.

## Deduplication

Exact normalized names, matching source IDs, and reviewed aliases identify duplicates. Examples include Bolt/Bolt.new, Fin/Fin by Intercom, Google Gemini/Gemini, and Perplexity AI/Perplexity. Builder.io and its Visual Copilot listing are consolidated at the platform level, as are Replit and Replit Agent; original component-specific claims remain traceable.

A shared domain or URL is insufficient to merge. ChatGPT, its agent and image experiences remain separate, as do Claude/Claude Code, Gemini/Gemini Image, Figma AI/Figma Make, and Luma AI/Dream Machine/Genie. DALL-E is preserved separately from the current ChatGPT image experience. Stable Diffusion is distinct from the AUTOMATIC1111 interface. Codeium plugins and legacy Replit Ghostwriter remain separate from their vendors' newer agents/editors.

## Website enrichment

The six real CSV-only records without supplied URLs received official links:

- [Pictory](https://pictory.ai/)
- [Kaggle](https://www.kaggle.com/)
- [Stable Diffusion](https://stability.ai/stable-image)
- [DALL-E](https://openai.com/index/dall-e-3/)
- [Codeium/Windsurf plugin documentation](https://docs.devin.ai/windsurf/plugins/getting-started)
- [Replit](https://replit.com/) for the legacy Ghostwriter entry. This is the vendor website, not a claim that the old product is still offered.

The DALL-E official page distinguishes the historical model from the current image experience. The plugin documentation also marks legacy maintenance limitations. URLs resolve product identity; they do not establish current availability or pricing.

## Supporting files

- `tools.merge-report.json`: counts, merges, conflicting values, input checksums, and URL enrichments.
- `pricing-research.json`: pricing classifications with source URLs and scope or inference notes, checked November 8, 2026.
- `tools.provenance.json`: every included original source record, indexed by output ID. Preserves `ai4sale.ai` attribution links.
- `tools.excluded.json`: all 270 placeholder records, preserved for inspection.
- `tool-tags.json`: controlled vocabulary, source mappings, and explicit overrides.

Original files remain unchanged. This task prepares the dataset; it does not replace frontend demo data or alter the backend.

Regenerate and validate from the repository root:

```sh
python3 scripts/normalize_tools.py
python3 -m unittest discover -s scripts -p 'test_normalize_tools.py'
```
