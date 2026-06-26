import { useState } from 'react'
import { api } from './api/client'
import SetSetup from './components/SetSetup'
import ScoringControls from './components/ScoringControls'
import ScoreSheet from './components/ScoreSheet'
import './App.css'

function App() {
  const [setId, setSetId] = useState(null)
  const [state, setState] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function run(action) {
    setLoading(true)
    setError('')
    try {
      await action()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function apply(result) {
    setSetId(result.set_id)
    setState(result.state)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true" />
          <div>
            <strong>Whistle</strong>
            <span>MIAA / NFHS scorebook</span>
          </div>
        </div>
        {setId && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setSetId(null)
              setState(null)
              setError('')
            }}
          >
            New set
          </button>
        )}
      </header>

      {error && <p className="banner error">{error}</p>}

      {!setId ? (
        <SetSetup
          loading={loading}
          onStart={(body) =>
            run(async () => {
              const result = await api.startSet(body)
              apply(result)
            })
          }
        />
      ) : (
        <main className="layout">
          <ScoringControls
            state={state}
            loading={loading}
            onRally={(winner) => run(async () => apply(await api.rally(setId, winner)))}
            onTimeout={(team) => run(async () => apply(await api.timeout(setId, team)))}
            onSub={(body) => run(async () => apply(await api.substitution(setId, body)))}
            onLiberoIn={(body) => run(async () => apply(await api.liberoIn(setId, body)))}
            onLiberoOut={(team) => run(async () => apply(await api.liberoOut(setId, team)))}
            onUndo={() => run(async () => apply(await api.undo(setId)))}
          />
          <ScoreSheet state={state} />
        </main>
      )}
    </div>
  )
}

export default App
