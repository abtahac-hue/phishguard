import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Finding = {
  id: string
  matched_text: string
  points: number
  explanation: string
}

type Analysis = {
  score: number
  risk_level: 'Low' | 'Medium' | 'High'
  findings: Finding[]
  notice: string
}

function App() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<Analysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleAnalyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setResult(null)

    if (!text.trim()) {
      setError('Enter a message or URL first.')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      })

      if (!response.ok) {
        throw new Error(
          `Analysis failed (${response.status}). Check your input and try again.`,
        )
      }

      const data: Analysis = await response.json()
      setResult(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not reach the analyzer. Try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="app">
      <header>
        <p>PHISHGUARD</p>
        <h1>Pause before you click.</h1>
        <p>
          Check messages and links for common phishing warning signs.
          Understand what needs a closer look.
        </p>
      </header>

      <form onSubmit={handleAnalyze}>
        <label htmlFor="message">Message or URL</label>
        <textarea
          id="message"
          rows={7}
          maxLength={10000}
          placeholder="Paste a suspicious message or an http(s):// link..."
          value={text}
          disabled={loading}
          onChange={(event) => {
            setText(event.target.value)
            setResult(null)
            setError('')
          }}
        />
        <p>
          {text.length.toLocaleString()} / 10,000 characters.
          Avoid entering passwords or personal information.
        </p>
        <button type="submit" disabled={loading || !text.trim()}>
          {loading ? 'Analyzing…' : 'Analyze message'}
        </button>
      </form>

      {error && <p role="alert">{error}</p>}

      <section aria-live="polite" aria-busy={loading}>
        {result && (
          <>
            <h2>{result.risk_level} warning level</h2>
            <p>
              <strong>{result.score} / 100</strong> — warning score
            </p>

            {result.findings.length > 0 ? (
              <ul>
                {result.findings.map((finding) => (
                  <li key={finding.id}>
                    <h3>{finding.id.replace(/_/g, ' ')}</h3>
                    <p>{finding.explanation}</p>
                    <p>
                      Matched: <q>{finding.matched_text}</q>
                    </p>
                    <small>+{finding.points} points</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p>
                No warning signs matched our current rules.
                Verify the sender and destination independently.
              </p>
            )}

            <p>{result.notice}</p>
          </>
        )}
      </section>
    </main>
  )
}

export default App