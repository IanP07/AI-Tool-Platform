# Toolkit frontend

A React + TypeScript + Vite frontend for discovering tools.

```sh
npm ci
npm run dev
```

Run `npm run build` for the TypeScript check and production build.

## Pages

- `#/`: directory with search, category/pricing filters, and sorting
- `#/tool/notion` (and other catalog IDs): overview, features, rating, pricing, and related tools
- `#/chat`: task recommendation demo with linked results and follow-up messages
- `#/saved`: bookmarked tools, persisted locally when browser storage is available

Frontend only. `src/data.ts` contains illustrative ratings, review counts, and prices. Chat uses labeled keyword matching; no AI or backend API calls are made. Google Fonts supplies optional typefaces, with local fallbacks.

Research: [tool-directory-research.md](../../docs/tool-directory-research.md).

## Manual checks

1. Search, filter by category and price, and sort. Try an unmatched search and clear filters.
2. Open a tool and a related tool. Refresh the detail URL and use browser back.
3. Save a tool, open Saved, and reload. Unsave it to check the empty state.
4. Try a suggested chat task, follow up with a free-plan constraint, and open a recommendation. Return to chat and start a new conversation.
5. Submit an unrelated task to see the no-match explanation. Empty messages cannot be sent.
6. Check mobile widths, keyboard navigation, and an invalid tool URL.
