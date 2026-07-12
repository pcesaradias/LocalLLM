import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import './App.css'

// --- Persistence keys -------------------------------------------------------
const LS_API_KEY = 'localllm_api_key'
const LS_API_BASE = 'localllm_api_base'
const LS_THEME = 'localllm_theme'
const LS_MODEL = 'localllm_model'

const CHART_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7']

// API base URL is resolved at RUNTIME in the browser (not a build-time env var),
// so a statically-served production build talks to the API on the same host.
function defaultApiBase() {
  const host = window.location.hostname || 'localhost'
  return `http://${host}:8080`
}

function resolveInitialTheme() {
  const stored = localStorage.getItem(LS_THEME)
  if (stored === 'light' || stored === 'dark') return stored
  const prefersDark = window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
  return prefersDark ? 'dark' : 'light'
}

function App() {
  // --- Core config (persisted) ---------------------------------------------
  const [apiKey, setApiKey] = useState(() => localStorage.getItem(LS_API_KEY) || '')
  const [apiBase, setApiBase] = useState(
    () => localStorage.getItem(LS_API_BASE) || defaultApiBase()
  )
  const [theme, setTheme] = useState(resolveInitialTheme)

  const authed = !!apiKey

  // --- UI state -------------------------------------------------------------
  const [activeTab, setActiveTab] = useState('chat')
  const [toasts, setToasts] = useState([])
  const [healthStatus, setHealthStatus] = useState(null)

  // --- Chat state -----------------------------------------------------------
  const [message, setMessage] = useState('')
  const [lastPrompt, setLastPrompt] = useState('')
  const [response, setResponse] = useState('')
  const [chatMeta, setChatMeta] = useState(null)
  const [chatError, setChatError] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(
    () => localStorage.getItem(LS_MODEL) || ''
  )

  // --- Models tab state -----------------------------------------------------
  const [showPullDialog, setShowPullDialog] = useState(false)
  const [pullModelName, setPullModelName] = useState('')
  const [modelBusy, setModelBusy] = useState(false)
  const [modelMessage, setModelMessage] = useState(null) // {type, text}

  // --- Analytics state ------------------------------------------------------
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState('')

  // --- Settings state -------------------------------------------------------
  const [baseDraft, setBaseDraft] = useState(apiBase)
  const [keyDraft, setKeyDraft] = useState('')
  const [rotatedKey, setRotatedKey] = useState('')
  const [rotating, setRotating] = useState(false)
  const [copied, setCopied] = useState(false)

  // --- Gate state -----------------------------------------------------------
  const [gateKey, setGateKey] = useState('')
  const [gateBase, setGateBase] = useState(apiBase)
  const [gateBusy, setGateBusy] = useState(false)

  // Keep refs of current config so async streams read fresh values.
  const apiBaseRef = useRef(apiBase)
  const apiKeyRef = useRef(apiKey)
  useEffect(() => { apiBaseRef.current = apiBase }, [apiBase])
  useEffect(() => { apiKeyRef.current = apiKey }, [apiKey])

  // --- Theme ----------------------------------------------------------------
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(LS_THEME, theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

  // --- Toasts ---------------------------------------------------------------
  const showToast = useCallback((type, text) => {
    const id = Date.now() + Math.random()
    setToasts((prev) => [...prev, { id, type, text }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 5000)
  }, [])

  const dismissToast = (id) =>
    setToasts((prev) => prev.filter((t) => t.id !== id))

  // --- Low-level API helpers -----------------------------------------------
  const buildHeaders = useCallback((withJson) => {
    const headers = {}
    if (withJson) headers['Content-Type'] = 'application/json'
    if (apiKeyRef.current) headers.Authorization = `Bearer ${apiKeyRef.current}`
    return headers
  }, [])

  const extractError = async (res) => {
    let detail = res.statusText || `HTTP ${res.status}`
    try {
      const data = await res.json()
      detail = data.detail || data.message || detail
    } catch {
      /* body was not JSON */
    }
    return `${res.status}: ${detail}`
  }

  // Generic JSON request against the configured base URL.
  const apiRequest = useCallback(async (path, { method = 'GET', body } = {}) => {
    const res = await fetch(apiBaseRef.current + path, {
      method,
      headers: buildHeaders(!!body),
      body: body ? JSON.stringify(body) : undefined
    })
    if (!res.ok) throw new Error(await extractError(res))
    const ctype = res.headers.get('content-type') || ''
    return ctype.includes('application/json') ? res.json() : res.text()
  }, [buildHeaders])

  // --- Data loaders ---------------------------------------------------------
  const loadHealth = useCallback(async (base) => {
    try {
      const res = await fetch((base || apiBaseRef.current) + '/health')
      if (!res.ok) throw new Error(await extractError(res))
      setHealthStatus(await res.json())
      return true
    } catch (err) {
      setHealthStatus({ status: 'unreachable', error: err.message })
      return false
    }
  }, [])

  const loadModels = useCallback(async () => {
    try {
      const data = await apiRequest('/models')
      const list = data.models || []
      setModels(list)
      setSelectedModel((prev) => {
        if (prev && list.some((m) => m.name === prev)) return prev
        return list.length ? list[0].name : ''
      })
    } catch (err) {
      showToast('error', `Failed to load models — ${err.message}`)
    }
  }, [apiRequest, showToast])

  const loadStats = useCallback(async () => {
    try {
      const data = await apiRequest('/admin/stats')
      setStats(data)
      setStatsError('')
    } catch (err) {
      setStatsError(err.message)
    }
  }, [apiRequest])

  // Persist selected model.
  useEffect(() => {
    if (selectedModel) localStorage.setItem(LS_MODEL, selectedModel)
  }, [selectedModel])

  // Health check on mount and whenever base URL changes.
  useEffect(() => {
    loadHealth(apiBase)
  }, [apiBase, loadHealth])

  // Load authenticated data once a key is present.
  useEffect(() => {
    if (authed) {
      loadModels()
      loadStats()
    }
  }, [authed, apiBase, loadModels, loadStats])

  // Auto-refresh analytics while the tab is visible.
  useEffect(() => {
    if (!authed || activeTab !== 'analytics') return
    const id = setInterval(loadStats, 30000)
    return () => clearInterval(id)
  }, [authed, activeTab, loadStats])

  // --- Chat / streaming -----------------------------------------------------
  // Streams /chat/stream, invoking onChunk with the accumulated text.
  // Handles both SSE (text/event-stream) and plain chunked responses.
  const streamChat = useCallback(async (payload, onChunk) => {
    const res = await fetch(apiBaseRef.current + '/chat/stream', {
      method: 'POST',
      headers: buildHeaders(true),
      body: JSON.stringify(payload)
    })
    if (!res.ok) throw new Error(await extractError(res))
    if (!res.body) throw new Error('Streaming not supported by this browser')

    const isSSE = (res.headers.get('content-type') || '').includes('text/event-stream')
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let acc = ''
    let buffer = ''

    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })

      if (isSSE) {
        buffer += text
        const frames = buffer.split('\n\n')
        buffer = frames.pop() || ''
        for (const frame of frames) {
          for (const line of frame.split('\n')) {
            const trimmed = line.trimStart()
            if (!trimmed.startsWith('data:')) continue
            const data = trimmed.slice(5).replace(/^ /, '')
            if (data === '[DONE]') continue
            // Each frame is a JSON object: localllm emits {"token","done"},
            // OpenAI-style emits {"choices":[{"delta":{"content"}}]}. Extract
            // the text; fall back to the raw string if it isn't JSON.
            let piece = data
            try {
              const obj = JSON.parse(data)
              if (obj.done) continue
              piece = obj.token ?? obj.choices?.[0]?.delta?.content ?? ''
            } catch {
              // not JSON — treat as raw text chunk
            }
            if (piece) {
              acc += piece
              onChunk(acc)
            }
          }
        }
      } else {
        acc += text
        onChunk(acc)
      }
    }
    return acc
  }, [buildHeaders])

  const sendMessage = async () => {
    const prompt = message.trim()
    if (!prompt || isSending) return
    if (!selectedModel) {
      showToast('error', 'No model selected — pull a model first')
      return
    }

    setIsSending(true)
    setChatError('')
    setChatMeta(null)
    setResponse('')
    setLastPrompt(prompt)

    const payload = {
      message: prompt,
      model: selectedModel,
      temperature: 0.7,
      max_tokens: 2048
    }

    let partial = ''
    try {
      await streamChat(payload, (acc) => {
        partial = acc
        setResponse(acc)
      })
      setMessage('')
    } catch (streamErr) {
      if (partial) {
        // Stream started then broke — keep what we have, surface the break.
        setChatError(`Stream interrupted — ${streamErr.message}`)
        showToast('error', `Stream interrupted — ${streamErr.message}`)
        setMessage('')
      } else {
        // Graceful fallback to the non-streaming endpoint.
        try {
          const data = await apiRequest('/chat', { method: 'POST', body: payload })
          setResponse(data.response || '')
          setChatMeta({
            model: data.model,
            tokens: data.tokens_used,
            time: data.processing_time
          })
          setMessage('')
        } catch (err) {
          setChatError(err.message)
          showToast('error', `Chat failed — ${err.message}`)
        }
      }
    } finally {
      setIsSending(false)
    }
  }

  const handleChatKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // --- Models actions -------------------------------------------------------
  const pullModel = async () => {
    const name = pullModelName.trim()
    if (!name) return
    setModelBusy(true)
    setModelMessage({ type: 'info', text: `Pulling ${name}… this may take a while.` })
    try {
      await apiRequest(`/admin/models/pull?model_name=${encodeURIComponent(name)}`, {
        method: 'POST'
      })
      setModelMessage({ type: 'success', text: `Pulled ${name}.` })
      setPullModelName('')
      setShowPullDialog(false)
      await loadModels()
      setTimeout(() => setModelMessage(null), 4000)
    } catch (err) {
      setModelMessage({ type: 'error', text: `Pull failed — ${err.message}` })
    } finally {
      setModelBusy(false)
    }
  }

  const deleteModel = async (name) => {
    if (!window.confirm(`Delete ${name}? This cannot be undone.`)) return
    setModelBusy(true)
    setModelMessage({ type: 'info', text: `Deleting ${name}…` })
    try {
      await apiRequest(`/admin/models/${encodeURIComponent(name)}`, { method: 'DELETE' })
      setModelMessage({ type: 'success', text: `Deleted ${name}.` })
      await loadModels()
      setTimeout(() => setModelMessage(null), 4000)
    } catch (err) {
      setModelMessage({ type: 'error', text: `Delete failed — ${err.message}` })
      setTimeout(() => setModelMessage(null), 5000)
    } finally {
      setModelBusy(false)
    }
  }

  // --- Settings actions -----------------------------------------------------
  const saveBaseUrl = () => {
    const next = baseDraft.trim().replace(/\/+$/, '')
    if (!next) {
      showToast('error', 'API base URL cannot be empty')
      return
    }
    localStorage.setItem(LS_API_BASE, next)
    setApiBase(next)
    showToast('success', 'API base URL saved')
  }

  const resetBaseUrl = () => {
    localStorage.removeItem(LS_API_BASE)
    const next = defaultApiBase()
    setApiBase(next)
    setBaseDraft(next)
    showToast('success', 'API base URL reset to default')
  }

  const updateSessionKey = () => {
    const next = keyDraft.trim()
    if (!next) {
      showToast('error', 'API key cannot be empty')
      return
    }
    localStorage.setItem(LS_API_KEY, next)
    setApiKey(next)
    setKeyDraft('')
    showToast('success', 'Session API key updated')
  }

  const rotateKey = async () => {
    if (!window.confirm(
      'Rotate the API key? The current key stops working immediately. ' +
      'Save the new key to your .env or you will be locked out.'
    )) return
    setRotating(true)
    setRotatedKey('')
    setCopied(false)
    try {
      const data = await apiRequest('/admin/rotate-key', { method: 'POST' })
      const newKey = data.api_key
      if (!newKey) throw new Error('Response did not include api_key')
      // Adopt the new key for this session so the app keeps working.
      localStorage.setItem(LS_API_KEY, newKey)
      setApiKey(newKey)
      setRotatedKey(newKey)
      showToast('success', 'API key rotated — save the new key now')
    } catch (err) {
      showToast('error', `Rotation failed — ${err.message}`)
    } finally {
      setRotating(false)
    }
  }

  const copyKey = async () => {
    try {
      await navigator.clipboard.writeText(rotatedKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      showToast('error', 'Clipboard unavailable — copy the key manually')
    }
  }

  // --- Gate / auth ----------------------------------------------------------
  const enterWithKey = async (e) => {
    e.preventDefault()
    const key = gateKey.trim()
    const base = gateBase.trim().replace(/\/+$/, '')
    if (!key) return
    setGateBusy(true)
    if (base && base !== apiBase) {
      localStorage.setItem(LS_API_BASE, base)
      setApiBase(base)
      apiBaseRef.current = base
    }
    // Validate the key against an authenticated endpoint before entering.
    apiKeyRef.current = key
    try {
      const res = await fetch(apiBaseRef.current + '/models', {
        headers: { Authorization: `Bearer ${key}` }
      })
      if (res.status === 401 || res.status === 403) {
        apiKeyRef.current = apiKey
        showToast('error', 'That API key was rejected by the server')
        setGateBusy(false)
        return
      }
      // Any non-auth response (including reachable errors) means the key is accepted.
    } catch (err) {
      // Network failure: let the user in but warn — Settings can fix the base URL.
      showToast('error', `Could not reach ${apiBaseRef.current} — check the base URL`)
    }
    localStorage.setItem(LS_API_KEY, key)
    setApiKey(key)
    setGateKey('')
    setGateBusy(false)
  }

  const logout = () => {
    localStorage.removeItem(LS_API_KEY)
    setApiKey('')
    apiKeyRef.current = ''
    setModels([])
    setStats(null)
    setResponse('')
    setLastPrompt('')
    setRotatedKey('')
    setActiveTab('chat')
  }

  const maskKey = (k) =>
    k.length <= 8 ? '••••' : `${k.slice(0, 4)}${'•'.repeat(6)}${k.slice(-4)}`

  // --- Shared UI fragments --------------------------------------------------
  const themeToggle = (
    <button
      className="icon-button"
      onClick={toggleTheme}
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      aria-label="Toggle color theme"
    >
      {theme === 'dark' ? '☀' : '☾'}
    </button>
  )

  const toastStack = (
    <div className="toast-stack">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`} onClick={() => dismissToast(t.id)}>
          <span>{t.text}</span>
          <button className="toast-close" aria-label="Dismiss">×</button>
        </div>
      ))}
    </div>
  )

  // --- Gate screen ----------------------------------------------------------
  if (!authed) {
    const status = healthStatus?.status
    return (
      <div className="gate">
        {toastStack}
        <div className="gate-card">
          <div className="gate-brand">
            <span className="logo-dot" />
            <h1>Local LLM Manager</h1>
          </div>
          <p className="gate-sub">
            Enter your LocalLLM API key to continue. Find it in your server's
            <code>.env</code> file.
          </p>
          <form onSubmit={enterWithKey}>
            <label className="field-label" htmlFor="gate-key">API key</label>
            <input
              id="gate-key"
              type="password"
              className="input"
              value={gateKey}
              onChange={(e) => setGateKey(e.target.value)}
              placeholder="Paste your API key"
              autoFocus
            />
            <label className="field-label" htmlFor="gate-base">API base URL</label>
            <input
              id="gate-base"
              type="text"
              className="input"
              value={gateBase}
              onChange={(e) => setGateBase(e.target.value)}
              placeholder="http://host:8080"
            />
            <button type="submit" className="btn btn-primary btn-block" disabled={gateBusy || !gateKey.trim()}>
              {gateBusy ? 'Checking…' : 'Enter'}
            </button>
          </form>
          <div className="gate-foot">
            <span className={`status-pill status-${status || 'unknown'}`}>
              {status ? `Server: ${status}` : 'Server: checking…'}
            </span>
            {themeToggle}
          </div>
        </div>
      </div>
    )
  }

  // --- Authenticated app ----------------------------------------------------
  const tabs = [
    ['chat', 'Chat'],
    ['models', 'Models'],
    ['analytics', 'Analytics'],
    ['settings', 'Settings']
  ]

  const health = healthStatus?.status || 'unknown'
  const cacheRatio = typeof stats?.cache_hit_ratio === 'number' ? stats.cache_hit_ratio : 0
  const redisHits = stats?.redis_hits ?? 0
  const redisMisses = stats?.redis_misses ?? 0
  const endpointData = Object.entries(stats?.requests_by_endpoint || {})
    .map(([name, count]) => ({ name, count }))
  const topModels = Array.isArray(stats?.top_models) ? stats.top_models : []

  return (
    <div className="app">
      {toastStack}

      <header className="topbar">
        <div className="topbar-left">
          <span className="logo-dot" />
          <h1>Local LLM Manager</h1>
        </div>
        <div className="topbar-right">
          <span className={`status-pill status-${health}`}>
            {health}
            {healthStatus?.models_loaded != null && ` · ${healthStatus.models_loaded} models`}
          </span>
          {themeToggle}
          <button className="btn btn-ghost" onClick={logout}>Logout</button>
        </div>
      </header>

      <nav className="tabs" role="tablist">
        {tabs.map(([id, label]) => (
          <button
            key={id}
            role="tab"
            aria-selected={activeTab === id}
            className={activeTab === id ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      <main className="content">
        {/* ---------------- Chat ---------------- */}
        {activeTab === 'chat' && (
          <section className="card">
            <div className="chat-toolbar">
              <label className="field-label" htmlFor="chat-model">Model</label>
              <select
                id="chat-model"
                className="select"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                {models.length === 0 && <option value="">No models available</option>}
                {models.map((m) => (
                  <option key={m.name} value={m.name}>
                    {m.name}{m.size ? ` (${m.size})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="chat-thread">
              {!lastPrompt && !response && (
                <div className="empty-state">Ask the model anything to get started.</div>
              )}
              {lastPrompt && (
                <div className="bubble bubble-user">
                  <div className="bubble-role">You</div>
                  <div className="bubble-body">{lastPrompt}</div>
                </div>
              )}
              {(response || isSending) && (
                <div className="bubble bubble-assistant">
                  <div className="bubble-role">Assistant</div>
                  <div className="bubble-body">
                    {response || <span className="typing">…</span>}
                  </div>
                  {chatMeta && (
                    <div className="bubble-meta">
                      {chatMeta.model && <span>{chatMeta.model}</span>}
                      {chatMeta.tokens != null && <span>{chatMeta.tokens} tokens</span>}
                      {chatMeta.time != null && <span>{chatMeta.time}s</span>}
                    </div>
                  )}
                </div>
              )}
              {chatError && <div className="inline-error">{chatError}</div>}
            </div>

            <div className="chat-input">
              <textarea
                className="textarea"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleChatKey}
                placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
                disabled={isSending}
                rows={3}
              />
              <button
                className="btn btn-primary send-btn"
                onClick={sendMessage}
                disabled={isSending || !message.trim()}
              >
                {isSending ? 'Sending…' : 'Send'}
              </button>
            </div>
          </section>
        )}

        {/* ---------------- Models ---------------- */}
        {activeTab === 'models' && (
          <section className="card">
            <div className="section-head">
              <h2>Models</h2>
              <button
                className="btn btn-primary"
                onClick={() => setShowPullDialog(true)}
                disabled={modelBusy}
              >
                Pull model
              </button>
            </div>

            {modelMessage && (
              <div className={`inline-banner banner-${modelMessage.type}`}>
                {modelMessage.text}
              </div>
            )}

            {models.length === 0 ? (
              <div className="empty-state">No models installed. Pull one to begin.</div>
            ) : (
              <div className="model-grid">
                {models.map((m) => (
                  <div key={m.name} className="model-card">
                    <div className="model-card-head">
                      <h3>{m.name}</h3>
                      {m.status && <span className="status-pill status-healthy">{m.status}</span>}
                    </div>
                    <dl className="model-meta">
                      {m.size && (<><dt>Size</dt><dd>{m.size}</dd></>)}
                      {m.modified && (<><dt>Modified</dt><dd>{m.modified}</dd></>)}
                    </dl>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => deleteModel(m.name)}
                      disabled={modelBusy}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}

            {showPullDialog && (
              <div
                className="modal-overlay"
                onClick={() => !modelBusy && setShowPullDialog(false)}
              >
                <div className="modal" onClick={(e) => e.stopPropagation()}>
                  <h3>Pull from Ollama library</h3>
                  <p className="muted">
                    Enter a model name such as <code>llama2:latest</code> or <code>tinyllama:latest</code>.
                  </p>
                  <input
                    className="input"
                    type="text"
                    value={pullModelName}
                    onChange={(e) => setPullModelName(e.target.value)}
                    placeholder="model:tag"
                    disabled={modelBusy}
                    autoFocus
                    onKeyDown={(e) => e.key === 'Enter' && pullModel()}
                  />
                  <div className="modal-actions">
                    <button
                      className="btn btn-ghost"
                      onClick={() => setShowPullDialog(false)}
                      disabled={modelBusy}
                    >
                      Cancel
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={pullModel}
                      disabled={modelBusy || !pullModelName.trim()}
                    >
                      {modelBusy ? 'Pulling…' : 'Pull'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </section>
        )}

        {/* ---------------- Analytics ---------------- */}
        {activeTab === 'analytics' && (
          <section className="card">
            <div className="section-head">
              <h2>Analytics</h2>
              <button className="btn btn-ghost" onClick={loadStats}>Refresh</button>
            </div>

            {statsError && <div className="inline-error">{statsError}</div>}

            {!stats && !statsError && <div className="empty-state">Loading analytics…</div>}

            {stats && (
              <>
                <div className="stat-cards">
                  <div className="stat-card">
                    <div className="stat-label">Total requests</div>
                    <div className="stat-value">{stats.total_requests ?? 0}</div>
                    <div className="stat-sub">All time</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Avg response time</div>
                    <div className="stat-value">{stats.avg_response_time ?? 0}s</div>
                    <div className="stat-sub">Per request</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Cache hit ratio</div>
                    <div className="stat-value">{(cacheRatio * 100).toFixed(1)}%</div>
                    <div className="stat-sub">{redisHits} / {redisHits + redisMisses} hits</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Models loaded</div>
                    <div className="stat-value">{stats.models_loaded ?? 0}</div>
                    <div className="stat-sub">Available</div>
                  </div>
                </div>

                <div className="chart-grid">
                  <div className="chart-panel">
                    <h3>Requests by endpoint</h3>
                    {endpointData.length ? (
                      <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={endpointData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                          <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} allowDecimals={false} />
                          <Tooltip
                            contentStyle={{
                              background: 'var(--surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 8,
                              color: 'var(--text)'
                            }}
                          />
                          <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="empty-state">No endpoint data yet.</div>
                    )}
                  </div>

                  <div className="chart-panel">
                    <h3>Top models by usage</h3>
                    {topModels.length ? (
                      <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                          <Pie
                            data={topModels}
                            dataKey="count"
                            nameKey="model"
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            label
                          >
                            {topModels.map((entry, i) => (
                              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              background: 'var(--surface)',
                              border: '1px solid var(--border)',
                              borderRadius: 8,
                              color: 'var(--text)'
                            }}
                          />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="empty-state">No model usage yet.</div>
                    )}
                  </div>
                </div>

                {stats.timestamp && (
                  <div className="stats-foot muted">
                    Last updated: {new Date(stats.timestamp).toLocaleString()}
                  </div>
                )}
              </>
            )}
          </section>
        )}

        {/* ---------------- Settings ---------------- */}
        {activeTab === 'settings' && (
          <section className="card settings">
            <h2>Settings</h2>

            <div className="setting-block">
              <h3>API base URL</h3>
              <p className="muted">
                Where the browser sends requests. Defaults to
                <code>{defaultApiBase()}</code> (this host, port 8080).
              </p>
              <div className="field-row">
                <input
                  className="input"
                  type="text"
                  value={baseDraft}
                  onChange={(e) => setBaseDraft(e.target.value)}
                  placeholder="http://host:8080"
                />
                <button className="btn btn-primary" onClick={saveBaseUrl}>Save</button>
                <button className="btn btn-ghost" onClick={resetBaseUrl}>Reset</button>
              </div>
              <p className="muted small">Active: <code>{apiBase}</code></p>
            </div>

            <div className="setting-block">
              <h3>Session API key</h3>
              <p className="muted">
                Current key: <code>{maskKey(apiKey)}</code>. Replace it for this session below.
              </p>
              <div className="field-row">
                <input
                  className="input"
                  type="password"
                  value={keyDraft}
                  onChange={(e) => setKeyDraft(e.target.value)}
                  placeholder="Enter a new API key"
                />
                <button className="btn btn-primary" onClick={updateSessionKey}>Update</button>
              </div>
            </div>

            <div className="setting-block">
              <h3>Rotate API key</h3>
              <p className="muted">
                Generates a brand-new key on the server and invalidates the current one.
                This session adopts the new key automatically — but you must save it to your
                server's <code>.env</code> or you will lose access on next restart.
              </p>
              <button className="btn btn-danger" onClick={rotateKey} disabled={rotating}>
                {rotating ? 'Rotating…' : 'Rotate API key'}
              </button>

              {rotatedKey && (
                <div className="rotated-key">
                  <div className="rotated-warn">
                    ⚠ Save this key now — it is shown only once.
                  </div>
                  <div className="rotated-row">
                    <code className="rotated-value">{rotatedKey}</code>
                    <button className="btn btn-ghost btn-sm" onClick={copyKey}>
                      {copied ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
