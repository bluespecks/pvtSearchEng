import { useState } from 'react'
import './App.css'

const MatrixLoader = () => {
  return (
    <div className="ai-matrix-loader-container">
      <div className="ai-matrix-loader">
        <div className="digit">0</div>
        <div className="digit">1</div>
        <div className="digit">0</div>
        <div className="digit">1</div>
        <div className="digit">1</div>
        <div className="digit">0</div>
        <div className="digit">0</div>
        <div className="digit">1</div>
        <div className="glow"></div>
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

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || loading) return

    setLoading(true)
    setError(null)
    // Do NOT setResults(null) right away so we don't snap back to home layout if we were in results mode

    const startTime = performance.now()

    try {
      const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(trimmed)}`)
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
      setError(err.message || 'Failed to fetch search results')
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  // If we haven't completed a search yet, we stay in 'home-mode'
  const isHome = !hasSearched

  return (
    <div className={`app ${isHome ? 'home-mode' : 'results-mode'}`}>
      <header className="header">
        <span className="logo">pvtsearcheng</span>
        <span className="version">v0.1</span>
      </header>

      <main className="main">
        <form onSubmit={handleSearch} className="search-container">
          <div className="search-wrapper">
            <span className="prompt">{'>'}</span>
            <input
              type="text"
              className="search-input"
              placeholder="search the web..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <button type="submit" className="search-button" aria-label="Search">
              ↵
            </button>
          </div>
        </form>

        {loading && <MatrixLoader />}

        {error && (
          <div className="status-message error">
            error: {error}
          </div>
        )}

        {!loading && !error && meta && (
          <div className="meta">
            <span>{meta.count} results</span>
            <span className="separator">·</span>
            <span>{meta.time}</span>
          </div>
        )}

        {!loading && !error && results && results.length === 0 && (
          <div className="status-message">
            0 results found for "{meta?.query}"
          </div>
        )}

        {!loading && !error && results && results.length > 0 && (
          <div className="results">
            {results.map((result, index) => (
              <div key={index} className="result">
                <div className="result-header">
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="result-title-link"
                  >
                    <h3 className="result-title">{result.title}</h3>
                  </a>
                  {result.source && (
                    <span className="result-source">[{result.source}]</span>
                  )}
                </div>
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="result-url"
                >
                  {result.url}
                </a>
                <p className="result-description">{result.description}</p>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

export default App