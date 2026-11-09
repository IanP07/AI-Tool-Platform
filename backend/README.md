# Toolkit API and frontend

The frontend now loads the database catalog, individual tools and reviews through FastAPI. Recommendations use OpenRouter on the server and return database tools, so recommendation links and directory links share the same detail route.

## Run locally

From `backend/`:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in DATABASE_URL and OPENROUTER_API_KEY in .env.
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Use the existing database with `tool` and `review` tables. The catalog expects database-generated integer tool IDs and the CSV fields `name`, `price`, `tags`, `url`, `short_description`, `description`, `advantages`, and `disadvantages`. Reviews use `id`, `tool_id`, `rating`, `title`, `date`, and `description`. This change does not import the CSV or migrate the database.

Run `migrations/001_review_scores.sql` against PostgreSQL before using the updated add-review route. It adds nullable `effectiveness`, `ease_of_use`, and `price` columns; existing reviews stay unchanged. New reviews are analyzed by JEV using the backend's `OPENROUTER_API_KEY`, then saved with scores from 1–10 and the original pricing sentence (or null when unmentioned). If JEV fails, the route returns 502 without saving the review.

In another terminal, from `frontend/my-react-app/`:

```sh
npm install
npm run dev
```

Restart an already-running Vite server to load the new proxy configuration. `/api/*` proxies to `http://127.0.0.1:8000/*`. Override the target using `API_PROXY_TARGET` in the frontend's `.env` when necessary.

For production, route `/api/*` to FastAPI with the prefix removed, or set `VITE_API_BASE_URL` to the backend's public URL **before building**. Prefer a same-origin reverse proxy; a separately hosted cross-origin API requires CORS configuration on the server. API keys and the database URL belong only in the backend environment.

## Route contracts

- `GET /tools?amount=100&offset=0`: catalog page, count, and `hasMore`. The frontend follows pages before applying search, category, saved, pricing, and sort controls.
- `GET /tool/{id}`: tool details from the database. The frontend displays rating aggregates if returned; otherwise it shows unrated.
- `GET /get-reviews/{tool_id}`: reviews for the selected tool.
- `POST /add-review`: `{tool_id, rating, title, description}`. Calls JEV and returns the saved review including `effectiveness`, `ease_of_use`, and `price`; the frontend refreshes the tool's rating.
- `POST /update-tool-scores`: no body. Updates every tool's `effectiveness` and `ease_of_use` to its review averages and returns `{updated: count}`. Null review scores are ignored; tools with no scores get null. Run `migrations/002_tool_scores.sql` against PostgreSQL before using this route.
- `POST /prompt`: `{messages: [{role: "user" | "assistant", content: "..."}]}`. Returns `{text, tools}`. Replaces the old hardcoded GET placeholder. The model receives catalog facts and conversation context; unknown recommended IDs are rejected. Missing configuration retains the original 500 response; malformed recommendation output returns 502. The frontend shows errors and a retry action, without demo recommendations.

Prices remain the database's full text, including currency and billing qualifiers. The lowest-price sort extracts USD amounts where present and places nonnumeric/other-currency entries last rather than doing implicit currency conversions. Tags may be native arrays or JSON-encoded CSV strings.

## Verify

```sh
# From backend/, with its virtual environment active:
pip install httpx
python -m unittest discover -s tests -v

# From frontend/my-react-app/:
node --test tests/api.test.mjs
npm run build
```

Backend tests use an isolated SQLite database and a mocked OpenRouter response; they never write to the configured database or spend API credits. Frontend tests verify pagination, adapters, routing contracts, and failure propagation. A live PostgreSQL/OpenRouter/browser smoke test still requires configured services.
