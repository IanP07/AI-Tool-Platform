import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { transformWithOxc } from 'vite'
const source = (await readFile(new URL('../src/api.ts', import.meta.url), 'utf8')).replace('import.meta.env.BACKEND_BASE_URL', 'undefined').replace("import toolScoreOverrides from './toolScoreOverrides.json'", `const toolScoreOverrides = ${await readFile(new URL('../src/toolScoreOverrides.json', import.meta.url), 'utf8')}`)
const { code: outputText } = await transformWithOxc(source, 'api.ts')
const api = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`)
const raw = { id: 42, name: 'Example', tags: '["research","writing"]', price: 'Free; Pro USD 20/month', url: 'https://example.com', community_rating: '4.5', review_count: 2 }
test('database adapter retains IDs, full price terms, categories and actual ratings', () => {
  const tool = api.normalizeTool(raw)
  assert.equal(tool.id, '42'); assert.equal(tool.rating, 4.5); assert.equal(tool.priceLabel, raw.price)
  assert.deepEqual(tool.tags, ['research', 'writing']); assert.equal(tool.free, true)
  assert.equal(api.normalizeTool({ ...raw, url: 'javascript:alert(1)' }).url, '')
  assert.equal(api.normalizeTool({ id: 1, price: 'Contact sales' }).price, Infinity)
  assert.equal(api.normalizeTool({ ...raw, ease_of_use: '7.92', effectiveness: 8 }).easeOfUse, 7.92)
  assert.equal(api.normalizeTool({ ...raw, effectiveness: 8 }).effectiveness, 8)
  assert.equal(api.normalizeTool(raw).easeOfUse, null)
  const overridden = api.normalizeTool({ ...raw, id: 496, tags: ['app-website-building'] })
  assert.equal(overridden.easeOfUse, 6.44)
  assert.equal(overridden.effectiveness, 6.1383)
  assert.equal(api.normalizeTool({ ...raw, id: 571, tags: ['app-website-building'] }).easeOfUse, null)
  assert.equal(api.normalizeTool({ ...raw, effectiveness: null }).effectiveness, null)
})
test('catalog pagination, chat and reviews use backend contracts', async () => {
  const calls = []
  const original = globalThis.fetch
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init })
    const data = url.includes('offset=0') ? { tools: [raw], hasMore: true } : url.includes('offset=1') ? { tools: [{ ...raw, id: 43 }], hasMore: false } : url.endsWith('/prompt') ? { text: 'Try Example', tools: [raw] } : { id: 1 }
    return new Response(JSON.stringify(data), { status: 200 })
  }
  try {
    assert.equal((await api.getTools()).length, 2)
    assert.equal(calls[1].url, '/api/tools?limit=100&offset=1')
    assert.equal(calls[1].init.headers.has('Content-Type'), false)
    assert.equal((await api.recommend([{ role: 'user', text: 'Research' }])).results[0].id, '42')
    assert.deepEqual(JSON.parse(calls.at(-1).init.body), { messages: [{ role: 'user', content: 'Research' }] })
    assert.equal(calls.at(-1).init.headers.get('Content-Type'), 'application/json')
    await api.addReview('42', { rating: 5, title: 'Useful', description: 'Worked' })
    assert.equal(JSON.parse(calls.at(-1).init.body).tool_id, 42)
    assert.equal(calls.at(-1).init.headers.get('Content-Type'), 'application/json')
    await api.getTool('42'); assert.equal(calls.at(-1).url, '/api/tool/42')
  } finally { globalThis.fetch = original }
})
test('API failures are surfaced instead of replaced with demo results', async () => {
  const original = globalThis.fetch
  globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Tool not found' }), { status: 404 })
  try { await assert.rejects(api.getTool('404'), /Tool not found/) } finally { globalThis.fetch = original }
})
