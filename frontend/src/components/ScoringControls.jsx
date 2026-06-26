import { useState } from 'react'
import { ROMANS } from './ScoreSheet'

export default function ScoringControls({
  state,
  onRally,
  onTimeout,
  onSub,
  onLiberoIn,
  onLiberoOut,
  onUndo,
  loading,
}) {
  const [subTeam, setSubTeam] = useState('home')
  const [entering, setEntering] = useState('')
  const [leaving, setLeaving] = useState('')
  const [liberoTeam, setLiberoTeam] = useState('home')
  const [liberoSlot, setLiberoSlot] = useState('0')

  if (!state) return null

  const servingTeam = state.serving
  const servingName = servingTeam === 'home' ? state.home.name : state.away.name

  function handleSub(event) {
    event.preventDefault()
    onSub({
      team: subTeam,
      entering: Number(entering),
      leaving: Number(leaving),
    })
    setEntering('')
    setLeaving('')
  }

  return (
    <section className="scoring-controls">
      <div className="scoreboard">
        <div className={`score-block away ${servingTeam === 'away' ? 'serving' : ''}`}>
          <span className="label">{state.away.name}</span>
          <span className="value">{state.away.score}</span>
          <span className="server">
            #{state.away.current_server}
            {state.away.is_libero_serving && ' △'}
          </span>
        </div>
        <div className="score-divider">:</div>
        <div className={`score-block home ${servingTeam === 'home' ? 'serving' : ''}`}>
          <span className="label">{state.home.name}</span>
          <span className="value">{state.home.score}</span>
          <span className="server">
            #{state.home.current_server}
            {state.home.is_libero_serving && ' △'}
          </span>
        </div>
      </div>

      <p className="serving-note">
        {servingName} serving · Set {state.set_number}
        {state.completed && ' · SET OVER'}
      </p>

      <div className="action-row">
        <button
          type="button"
          className="btn btn-gold"
          onClick={() => onRally('away')}
          disabled={loading || state.completed}
        >
          {state.away.name} wins
        </button>
        <button
          type="button"
          className="btn btn-gold"
          onClick={() => onRally('home')}
          disabled={loading || state.completed}
        >
          {state.home.name} wins
        </button>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onUndo}
          disabled={loading || !state.events.length}
        >
          Undo
        </button>
      </div>

      <div className="secondary-actions">
        <div className="action-panel timeout-actions">
          <span className="action-panel-title">Timeouts</span>
          <button
            type="button"
            className="btn btn-subtle"
            disabled={loading || state.completed || state.home.timeouts_used >= 2}
            onClick={() => onTimeout('home')}
          >
            {state.home.name} ({state.home.timeouts_used}/2)
          </button>
          <button
            type="button"
            className="btn btn-subtle"
            disabled={loading || state.completed || state.away.timeouts_used >= 2}
            onClick={() => onTimeout('away')}
          >
            {state.away.name} ({state.away.timeouts_used}/2)
          </button>
        </div>

        <form className="action-panel sub-form" onSubmit={handleSub}>
          <span className="action-panel-title">Substitution</span>
          <select value={subTeam} onChange={(e) => setSubTeam(e.target.value)}>
            <option value="home">{state.home.name}</option>
            <option value="away">{state.away.name}</option>
          </select>
          <input
            type="number"
            placeholder="In"
            value={entering}
            onChange={(e) => setEntering(e.target.value)}
            required
          />
          <input
            type="number"
            placeholder="Out"
            value={leaving}
            onChange={(e) => setLeaving(e.target.value)}
            required
          />
          <button type="submit" className="btn btn-subtle" disabled={loading || state.completed}>
            Record
          </button>
        </form>

        <div className="action-panel libero-actions">
          <span className="action-panel-title">Libero</span>
          <select value={liberoTeam} onChange={(e) => setLiberoTeam(e.target.value)}>
            <option value="home">{state.home.name}</option>
            <option value="away">{state.away.name}</option>
          </select>
          <select value={liberoSlot} onChange={(e) => setLiberoSlot(e.target.value)}>
            {ROMANS.map((roman, index) => (
              <option key={roman} value={index}>
                Slot {roman}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="btn btn-subtle"
            disabled={loading || state.completed}
            onClick={() => onLiberoIn({ team: liberoTeam, slot: Number(liberoSlot) })}
          >
            In
          </button>
          <button
            type="button"
            className="btn btn-subtle"
            disabled={loading || state.completed}
            onClick={() => onLiberoOut(liberoTeam)}
          >
            Out
          </button>
        </div>
      </div>
    </section>
  )
}
