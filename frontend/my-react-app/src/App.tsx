import { useEffect, useRef, useState } from 'react'
import { categories, recommend, tools } from './data'
import type { Tool } from './data'
import './App.css'

type Message = { role: 'user' | 'assistant'; text: string; results?: Tool[] }
function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    search: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
    bookmark: <path d="M6 3h12v18l-6-4-6 4z"/>,
    chat: <path d="M21 11a9 9 0 0 1-9 9H4l-2 2v-11a9 9 0 0 1 19 0ZM7 10h10M7 14h6"/>,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>,
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] ?? paths.arrow}</svg>
}
function Mark({ tool }: { tool: Tool }) { return <span aria-hidden="true" className={`tool-mark ${tool.color}`}>{tool.mark}</span> }
function App() {
  const [route, setRoute] = useState(location.hash.slice(1) || '/')
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('All tools')
  const [price, setPrice] = useState('all')
  const [sort, setSort] = useState('featured')
  const [saved, setSaved] = useState<string[]>(() => { try { const value: unknown = JSON.parse(localStorage.getItem('toolkit-saved') || '[]'); return Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : [] } catch { return [] } })
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const bottom = useRef<HTMLDivElement>(null)
  useEffect(() => { const handle = () => { setRoute(location.hash.slice(1) || '/'); window.scrollTo(0,0) }; window.addEventListener('hashchange', handle); return () => window.removeEventListener('hashchange', handle) }, [])
  useEffect(() => { try { localStorage.setItem('toolkit-saved', JSON.stringify(saved)) } catch { /* Saving remains available in memory. */ } }, [saved])
  useEffect(() => { if (messages.length && route === '/chat') bottom.current?.scrollIntoView({ block: 'end' }) }, [messages, route])
  const toggleSave = (id: string) => setSaved(old => old.includes(id) ? old.filter(v => v !== id) : [...old, id])
  const isChat = route === '/chat'
  const isSaved = route === '/saved'
  const selected = route.startsWith('/tool/') ? tools.find(t => t.id === route.split('/')[2]) : undefined
  useEffect(() => { document.title = `${selected?.name ?? (isChat ? 'Find your tool' : isSaved ? 'Saved tools' : 'Discover tools')} — Toolkit` }, [selected, isChat, isSaved])
  function submit(text: string) {
    if (!text.trim()) return
    const previous = messages.filter(m => m.role === 'user').map(m => m.text).join(' ')
    const results = recommend(`${previous} ${text}`)
    setMessages(old => [...old, { role:'user', text:text.trim() }, { role:'assistant', text:results.length ? 'Here’s a shortlist for your task. Open a tool to explore what it does, its pricing, and whether it fits your workflow.' : 'I couldn’t find a close match in this sample catalog. Tell me a little more about the task—writing, research, design, coding, meetings, or automation—and I’ll narrow it down.', results }])
    setDraft('')
  }
  function ToolRow({ tool, index }: { tool: Tool; index?: number }) {
    return <article className="tool-row">
      {index !== undefined && <span className="row-number">{String(index + 1).padStart(2,'0')}</span>}
      <a className="tool-main" href={`#/tool/${tool.id}`}><Mark tool={tool}/><div><h3>{tool.name}<span className="category-label">{tool.category}</span></h3><p>{tool.tagline}</p><span className="mobile-rating">★ {tool.rating.toFixed(1)} · {tool.free ? 'Free plan available' : `From $${tool.price}/mo`}</span></div></a>
      <div className="row-rating"><strong><span className="star">★</span> {tool.rating.toFixed(1)}</strong><small>{tool.reviews.toLocaleString()} reviews</small></div>
      <div className="row-price"><strong>{tool.free ? 'Freemium' : 'Paid'}</strong><small>From ${tool.price}/mo</small></div>
      <button className={`save-button ${saved.includes(tool.id) ? 'saved' : ''}`} onClick={() => toggleSave(tool.id)} aria-label={`${saved.includes(tool.id) ? 'Unsave' : 'Save'} ${tool.name}`} aria-pressed={saved.includes(tool.id)}><Icon name="bookmark" size={18}/></button>
      <a className="row-arrow" href={`#/tool/${tool.id}`} aria-label={`View ${tool.name}`}><Icon name="arrow" size={18}/></a>
    </article>
  }
  const filtered = tools.filter(t => (!isSaved || saved.includes(t.id)) && (category === 'All tools' || category === t.category) && (price === 'all' || (price === 'free' ? t.free : !t.free)) && `${t.name} ${t.tagline} ${t.tags.join(' ')} ${t.category}`.toLowerCase().includes(search.toLowerCase()))
    .sort((a,b) => sort === 'rating' ? b.rating-a.rating : sort === 'price' ? a.price-b.price : sort === 'name' ? a.name.localeCompare(b.name) : 0)
  const resetFilters = () => { setSearch(''); setCategory('All tools'); setPrice('all'); setSort('featured') }
  return <>
    <a className="skip-link" href="#main" onClick={e => { e.preventDefault(); document.getElementById('main')?.focus() }}>Skip to content</a>
    <header className="site-header"><div className="header-inner"><a href="#/" className="brand" aria-label="Toolkit home"><span className="brand-symbol">t.</span>toolkit<span className="brand-period">.</span></a><nav aria-label="Main navigation"><a href="#/" className={!isChat && !isSaved ? 'active' : ''}>Discover tools</a><a href="#/chat" className={isChat ? 'active' : ''}>Find my tool <span className="nav-ai">AI</span></a></nav><a href="#/saved" className={`saved-nav ${isSaved ? 'active' : ''}`}><Icon name="bookmark" size={17}/><span>Saved</span><span className="saved-count">{saved.length}</span></a></div></header>
    <main id="main" tabIndex={-1}>
      {selected ? <div className="page detail-page"><a href="#/" className="back-link">← Back to all tools</a><div className="detail-heading"><Mark tool={selected}/><div><span className="eyebrow">{selected.category}</span><h1>{selected.name}</h1><p>{selected.tagline}</p></div></div><div className="detail-layout"><div className="detail-content"><div className="detail-intro"><span className="eyebrow">THE OVERVIEW</span><h2>Meet {selected.name}.</h2><p>{selected.description}</p></div><section><h2>What you can do</h2><ul className="feature-list">{selected.features.map(feature => <li key={feature}><span>✓</span>{feature}</li>)}</ul></section><div className="fit-grid"><section><span className="eyebrow">A GOOD FIT FOR</span><p>{selected.best}</p></section><section><span className="eyebrow">WORTH KNOWING</span><p>{selected.caveat}</p></section></div><section><h2>Also worth a look</h2>{tools.filter(t => t.id !== selected.id && t.category === selected.category).concat(tools.filter(t => t.id !== selected.id && t.category !== selected.category)).slice(0,2).map(t => <ToolRow key={t.id} tool={t}/>)}</section></div><aside className="detail-sidebar"><div className="rating-summary"><span className="eyebrow">COMMUNITY RATING · DEMO</span><div><strong>{selected.rating.toFixed(1)}</strong><span><span className="stars">★★★★★</span><small>{selected.reviews.toLocaleString()} sample reviews</small></span></div></div><div className="price-summary"><span className="eyebrow">ILLUSTRATIVE PRICING</span><p><strong>${selected.price}</strong> / month</p><span>{selected.free ? 'Free plan available' : 'Paid plans only'}</span><small>Sample starting price. Check the vendor for current plans and billing terms.</small></div><a className="primary-button" href={selected.url} target="_blank" rel="noreferrer">Visit {selected.name} ↗</a><button className="secondary-button" onClick={() => toggleSave(selected.id)}><Icon name="bookmark" size={17}/>{saved.includes(selected.id) ? 'Saved to your list' : 'Save for later'}</button></aside></div></div>
      : isChat ? <div className="page chat-page"><div className="chat-topline">{messages.length > 0 && <button className="text-button" onClick={() => { setMessages([]); setDraft('') }}>New conversation ↗</button>}</div><h1>What are you working on?</h1><div className="conversation" aria-live="polite">{messages.length === 0 ? <div className="chat-welcome"><div className="chat-emblem"><Icon name="chat" size={30}/></div><p>Share what you want to do, your budget, and what matters to you.<br/>Or start with one of these.</p><div className="prompt-grid">{['I need to edit a podcast', 'Find free tools for research', 'Help me design a website', 'I want to automate repetitive tasks'].map(prompt => <button key={prompt} onClick={() => submit(prompt)}>{prompt}<Icon name="arrow" size={17}/></button>)}</div></div> : messages.map((message,index) => <div key={index} className={`message ${message.role}`}><span className="message-author">{message.role === 'user' ? 'YOU' : 'TOOLKIT'}</span><p>{message.text}</p>{!!message.results?.length && <div className="recommendations">{message.results.map(tool => <ToolRow key={tool.id} tool={tool}/>)}</div>}</div>)}<div ref={bottom}/></div><form className="chat-composer" onSubmit={e => { e.preventDefault(); submit(draft) }}><label className="sr-only" htmlFor="chat-input">Describe your task</label><textarea id="chat-input" value={draft} onChange={e => setDraft(e.target.value)} placeholder="I’m looking for a tool that can…" rows={2} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(draft) } }}/><button className="send-button" disabled={!draft.trim()} aria-label="Send message"><Icon name="arrow"/></button></form></div>
      : route !== '/' && route !== '/saved' ? <div className="page empty-state"><h1>That page isn’t here.</h1><p>Find your next tool in the directory.</p><a className="primary-button" href="#/">Browse tools →</a></div>
      : <div className="page"><section className="intro"><div><h1>{isSaved ? 'Your next great toolkit.' : <>Less searching.<br/>More <em>doing.</em></>}</h1></div><a href="#/chat" className="finder-callout"><span className="callout-icon"><Icon name="chat" size={23}/></span><span className="eyebrow">NOT SURE WHERE TO START?</span><h2>Start with what<br/>you want to do.</h2><span className="callout-action">Find my tool <Icon name="arrow" size={19}/></span></a></section><div className="directory-layout"><aside className="filters"><span className="eyebrow">BROWSE BY CATEGORY</span><div className="category-list">{categories.map((cat,index) => <button key={cat} onClick={() => setCategory(cat)} className={category === cat ? 'selected' : ''} aria-pressed={category === cat}><span>{index === 0 ? <Icon name="grid" size={17}/> : <span className="category-dot"/>}{cat}</span><small>{tools.filter(t => (cat === 'All tools' || t.category === cat) && (!isSaved || saved.includes(t.id))).length}</small></button>)}</div><div className="price-filter"><label className="eyebrow" htmlFor="pricing">PRICING</label><select id="pricing" value={price} onChange={e => setPrice(e.target.value)}><option value="all">All pricing</option><option value="free">Free plan available</option><option value="paid">Paid only</option></select></div></aside><section className="directory"><div className="search-box"><Icon name="search"/><label className="sr-only" htmlFor="tool-search">Search tools</label><input id="tool-search" placeholder="Search tools, categories, or a task…" value={search} onChange={e => setSearch(e.target.value)}/>{search && <button onClick={() => setSearch('')} aria-label="Clear search">×</button>}</div><div className="list-toolbar"><h2>{isSaved ? 'Saved tools' : category === 'All tools' ? 'Explore the directory' : category}<span>{filtered.length}</span></h2><label>Sort by <select value={sort} onChange={e => setSort(e.target.value)} aria-label="Sort tools"><option value="featured">Featured</option><option value="rating">Highest rated</option><option value="price">Lowest paid price</option><option value="name">Name A–Z</option></select></label></div><div className="table-heading"><span>TOOL</span><span>RATING</span><span>PRICING</span><span/></div><div className="tool-list">{filtered.map((tool,index) => <ToolRow key={tool.id} tool={tool} index={index}/>)}{!filtered.length && <div className="empty-state"><Icon name={isSaved ? 'bookmark' : 'search'} size={30}/><h2>{isSaved && !saved.length ? 'Your shortlist starts here.' : 'No tools found.'}</h2><p>{isSaved && !saved.length ? 'Save a tool from the directory to come back to it later.' : 'Try another search or clear your filters.'}</p>{isSaved && !saved.length ? <a href="#/" className="primary-button" onClick={resetFilters}>Explore tools →</a> : <button className="secondary-button" onClick={resetFilters}>Clear filters</button>}</div>}</div><div className="list-footer"><span>Showing {filtered.length} of {isSaved ? saved.length : tools.length} tools</span></div></section></div></div>}
    </main><footer className="site-footer"><a href="#/" className="footer-brand">toolkit.</a></footer>
  </>
}
export default App
