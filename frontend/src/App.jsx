import { useState } from 'react'
import './App.css'

const MatrixLoader = () => {
  return (
    <div className="ai-matrix-loader-container" aria-label="Loading search results" role="status">
      <div className="ai-matrix-loader">
        <span className="digit">0</span>
        <span className="digit">1</span>
        <span className="digit">0</span>
        <span className="digit">1</span>
        <span className="digit">1</span>
        <span className="digit">0</span>
        <span className="digit">0</span>
        <span className="digit">1</span>
      </div>
    </div>
  )
}

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [meta, setMeta] = useState(null)

  const [hasSearched, setHasSearched] = useState(false)
  const [page, setPage] = useState(1)
  const [loadingMore, setLoadingMore] = useState(false)

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    setPage(1)
    // Do NOT setResults(null) right away so we don't snap back to home layout if we were in results mode

    const startTime = performance.now()

    try {
      const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(trimmed)}&page=1`)
      if (!response.ok) {
        throw new Error(`Server returned ${response.status} ${response.statusText}`)
      }
      const data = await response.json()
      const elapsed = ((performance.now() - startTime) / 1000).toFixed(2)
      const resList = data.results || []

      setResults(resList)
      setMeta({
        count: resList.length,
        time: `${elapsed}s`,
        query: trimmed,
      })
      setHasSearched(true)
    } catch (err) {
      setError(err.message || 'search service unavailable')
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = async () => {
    if (loadingMore || loading || !query) return
    setLoadingMore(true)

    const nextPage = page + 1
    const trimmed = query.trim()

    try {
      const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(trimmed)}&page=${nextPage}`)
      if (!response.ok) {
        throw new Error(`Server returned ${response.status} ${response.statusText}`)
      }
      const data = await response.json()
      const newResults = data.results || []

      setResults(prev => [...prev, ...newResults])
      setPage(nextPage)
      setMeta(prev => prev ? { ...prev, count: prev.count + newResults.length } : null)
    } catch (err) {
      // Just keep existing results on error, maybe log or subtle toast in future
      console.error(err)
    } finally {
      setLoadingMore(false)
    }
  }

  const handleReset = () => {
    setQuery('')
    setResults(null)
    setMeta(null)
    setError(null)
    setHasSearched(false)
  }

  // If we haven't completed a search yet, we stay in 'home-mode'
  const isHome = !hasSearched

  return (
    <div className={`app ${isHome ? 'home-mode' : 'results-mode'}`}>
      <header className="header">
        <div className="brand-group">
          {isHome ? (
            <span className="logo">PvtSearchEng</span>
          ) : (
            <button
              type="button"
              className="logo-btn"
              onClick={handleReset}
              title="Return to home"
            >
              <span className="logo">PvtSearchEng</span>
            </button>
          )}
          {isHome && <span className="tagline">private search. no history.</span>}
        </div>
        {!isHome && <span className="version">v0.1</span>}
      </header>

      <main className="main">
        <form onSubmit={handleSearch} className="search-container">
          <div className="search-wrapper">
            <span className="prompt" aria-hidden="true">{'>'}</span>
            <input
              type="text"
              className="search-input"
              placeholder="search the web..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
              autoComplete="off"
              spellCheck="false"
              aria-label="Search query"
            />
            <button type="submit" className="search-button" aria-label="Search">
              ↵
            </button>
          </div>
        </form>

        {loading && <MatrixLoader />}

        {error && (
          <div className="status-message error" role="alert">
            <span className="prompt" aria-hidden="true">{'>'}</span> error: {error}
          </div>
        )}

        {!loading && !error && meta && results && results.length > 0 && (
          <div className="meta">
            <span>{meta.count} results</span>
            <span className="separator">·</span>
            <span>{meta.time}</span>
          </div>
        )}

        {!loading && !error && results && results.length === 0 && (
          <div className="status-message" role="status">
            <span className="prompt" aria-hidden="true">{'>'}</span> 0 results found for "{meta?.query}"
          </div>
        )}

        {!loading && !error && results && results.length > 0 && (
          <div className="results">
            {results.map((result, index) => (
              <article key={index} className="result">
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="result-title-link"
                >
                  <h2 className="result-title">{result.title}</h2>
                </a>
                <div className="result-url">{result.url}</div>
                {result.description && (
                  <p className="result-description">{result.description}</p>
                )}
                {result.source && (
                  <div className="result-meta">
                    <span className="result-source">[{result.source}]</span>
                  </div>
                )}
              </article>
            ))}

            <div className="load-more-container">
              {loadingMore ? (
                <MatrixLoader />
              ) : (
                <button
                  type="button"
                  className="load-more-btn"
                  onClick={loadMore}
                >
                  fetch more results ↵
                </button>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App