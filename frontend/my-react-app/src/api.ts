export type Tool = { id: string; name: string; mark: string; color: string; category: string; tagline: string; description: string; rating: number; reviews: number; price: number; priceLabel: string; free: boolean; tags: string[]; features: string[]; best: string; caveat: string; url: string }
export type Review = { id: number; tool_id: number; rating: number; title: string; date: string; description: string }
const base = (import.meta.env.BACKEND_BASE_URL || '/api').replace(/\/$/, '')
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers }, signal: init?.signal ?? AbortSignal.timeout(90000) })
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(typeof error?.detail === 'string' ? error.detail : `Request failed (${response.status}). Please try again.`)
  }
  return response.json()
}
export function normalizeTool(raw: Record<string, unknown>): Tool {
  let tags = raw.tags
  if (typeof tags === 'string') { const text = tags; try { tags = JSON.parse(text) } catch { tags = text.split(',') } }
  const list = Array.isArray(tags) ? tags.filter((tag): tag is string => typeof tag === 'string') : []
  const priceLabel = String(raw.price ?? 'Pricing unavailable')
  const amount = priceLabel.match(/(?:USD\s*|\$)(\d+(?:\.\d+)?)/i)
  const name = String(raw.name ?? '')
  return { id: String(raw.id), name, mark: name.slice(0, 1), color: 'ink', category: list[0]?.replaceAll('-', ' ') || 'Other', tagline: String(raw.short_description ?? ''), description: String(raw.description ?? ''), rating: Number(raw.community_rating ?? 0), reviews: Number(raw.review_count ?? 0), price: amount ? Number(amount[1]) : Number.POSITIVE_INFINITY, priceLabel, free: /^free\b/i.test(priceLabel) && !/^free trial/i.test(priceLabel), tags: list, features: list.map(tag => tag.replaceAll('-', ' ')), best: String(raw.advantages ?? ''), caveat: String(raw.disadvantages ?? ''), url: safeUrl(raw.url) }
}
function safeUrl(value: unknown) {
  try { const url = new URL(String(value)); return ['http:', 'https:'].includes(url.protocol) ? url.href : '' } catch { return '' }
}
export async function getTools(signal?: AbortSignal): Promise<Tool[]> {
  const result: Tool[] = []
  for (let offset = 0; ; ) {
    const page = await request<{ tools: Record<string, unknown>[]; hasMore: boolean }>(`/tools?amount=100&offset=${offset}`, { signal })
    result.push(...page.tools.map(normalizeTool))
    if (!page.hasMore || !page.tools.length) return result
    offset += page.tools.length
  }
}
export const getTool = async (id: string, signal?: AbortSignal) => normalizeTool(await request<Record<string, unknown>>(`/tool/${encodeURIComponent(id)}`, { signal }))
export const getReviews = (id: string, signal?: AbortSignal) => request<Review[]>(`/get-reviews/${encodeURIComponent(id)}`, { signal })
export const addReview = (id: string, review: { rating: number; title: string; description: string }) => request<Review>('/add-review', { method: 'POST', body: JSON.stringify({ tool_id: Number(id), ...review }) })
export async function recommend(messages: { role: string; text: string }[]) {
  const result = await request<{ text: string; tools: Record<string, unknown>[] }>('/prompt', { method: 'POST', body: JSON.stringify({ messages: messages.map(m => ({ role: m.role, content: m.text.slice(0, 4000) })) }) })
  return { text: result.text, results: result.tools.map(normalizeTool) }
}
