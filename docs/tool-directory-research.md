# Tool discovery research

Reviewed November 8, 2026. This is a representative market survey, not an exhaustive census of every recommendation platform. Notes reflect accessible official pages; blocked pages are identified below.

| Platform | Discovery approach observed | Implication for this frontend |
| --- | --- | --- |
| [Product Hunt](https://www.producthunt.com/) | Compact product lists, short taglines, launch discovery, community vote counts | Make the home page immediately useful with scannable rows. Votes and ratings are different signals. |
| [G2](https://www.g2.com/) | Software categories, user reviews, product comparisons | Put a numerical rating and review count beside each listing; keep the source of ratings clear. |
| [Capterra](https://www.capterra.com/?authuser=0) | Official search excerpt describes comparisons across features, pricing, and reviews; full homepage could not be retrieved | Keep price visible on detail pages. Do not claim a full visual inspection. |
| [GetApp](https://www.getapp.com/) | Category discovery, numerical ratings, review distributions, saves, and comparison | Support shortlisting and show the same information consistently across views. |
| [AlternativeTo](https://alternativeto.net/) | Crowdsourced alternatives, descriptions, license and platform metadata | Include related tools and clear pricing-model labels. |
| [SaaSHub](https://www.saashub.com/) | Software alternatives and detailed category navigation | Use practical work categories rather than model or technical taxonomy. |
| [Futurepedia](https://www.futurepedia.io/) | Personalized toolkits based on role, goals, and constraints | Give task-based discovery a separate destination and invite budget/context. |
| [Toolify](https://www.toolify.ai/) | Categories, new tools, most-saved tools, usage/traffic rankings | Distinguish popularity from quality; avoid overloading the initial list. |
| [Future Tools](https://futuretools.io/) | Editorial curation, top tools, newly added tools, and browsing | Use short, understandable summaries with a calm editorial presentation. |
| [Uneed](https://www.uneed.best/tags) | Large tag-based tool directory | Provide simple category filtering without presenting an overwhelming tag taxonomy. |
| [There's An AI For That](https://theresanaiforthat.com/) | Relevant task-discovery competitor; direct page fetch was blocked | Included in market scope, but not used as verified evidence of its current UI. |

## Design decisions

The first screen is a useful directory, without a marketing-page detour. Tool rows share a consistent name, brief description, category, sample rating, sample review count, and sample starting price. A muted green accent, warm white canvas, fine rules, and editorial serif headings establish a distinct visual identity. Avoid glowing gradients, decorative AI imagery, and oversized promotional cards.

Tool pages put the title first, explanatory copy and features in the main column, and rating/pricing/actions in the side column. Related tools use the same reusable rows. The mobile layout stacks the details and preserves the most useful row metadata.

The separate recommendation page asks about tasks and returns the same tool rows, linking to exactly the same detail routes. Suggested prompts, follow-ups, no-match responses, and a reset action make the prototype navigable. Its rule-based matching is explicitly labeled a frontend demo, not a live AI integration.

## Prototype boundaries

- All catalog ratings, review counts, and prices are illustrative fixtures, clearly disclosed in the directory and detail pages. They were not copied from review services or verified as current vendor pricing.
- Tool descriptions are prototype copy. Vendor links let users inspect current offerings.
- Search, category/pricing filters, sorting, bookmarks, and task matching operate entirely in the browser.
- Bookmarks persist in localStorage when available. Chat stays in memory while moving between frontend pages.
- Hash routes support detail links, refresh, and browser back/forward without server route configuration.
- Recommendation matching uses keywords and previous user turns, with simple free-plan/budget constraints. It does not provide semantic reasoning, real review aggregation, live pricing, or backend persistence.
- Production integration should supply sourced rating counts, pricing dates and billing terms, tool metadata, and a real recommendation service. A no-match response is preferable to invented tools.
