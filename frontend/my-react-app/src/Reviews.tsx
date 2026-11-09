import { useEffect, useState } from 'react'
import { addReview, getReviews } from './api'
import type { Review } from './api'
export default function Reviews({ id, onSaved }: { id: string; onSaved: () => void }) {
  const [reviews, setReviews] = useState<Review[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError('')
    getReviews(id, controller.signal).then(setReviews).catch(e => { if (!controller.signal.aborted) setError(e.message) }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [id, revision])
  return <section className="reviews-section"><h2>Community reviews</h2>
    {loading && <p role="status">Loading reviews…</p>}
    {error && <p role="alert">{error} <button onClick={() => setRevision(v => v + 1)}>Retry</button></p>}
    {!loading && !error && !reviews.length && <p>No reviews yet. Be the first to share your experience.</p>}
    {reviews.map(review => <article className="review" key={review.id}><strong>{review.title}</strong><span>★ {review.rating}/5 · {review.date}</span><p>{review.description}</p></article>)}
    <form className="review-form" onSubmit={async e => {
      e.preventDefault()
      if (saving) return
      const form = e.currentTarget
      const data = new FormData(form)
      setSaving(true); setSaved(false); setError('')
      try {
        const review = await addReview(id, { rating: Number(data.get('rating')), title: String(data.get('title')).trim(), description: String(data.get('description')).trim() })
        setReviews(old => [review, ...old]); setSaved(true); form.reset(); onSaved()
      } catch (e) { setError(e instanceof Error ? e.message : 'Could not save your review.') }
      finally { setSaving(false) }
    }}><h3>Write a review</h3><label>Rating<select name="rating" defaultValue="5">{[5,4,3,2,1].map(n => <option key={n} value={n}>{n} / 5</option>)}</select></label><label>Title<input name="title" required maxLength={200}/></label><label>Your experience<textarea name="description" required maxLength={5000} rows={4}/></label><button className="primary-button" disabled={saving}>{saving ? 'Saving…' : 'Submit review'}</button>{saved && <p role="status">Your review has been added.</p>}</form>
  </section>
}
