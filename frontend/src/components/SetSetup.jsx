import { useState } from 'react'
import { ROMANS } from './ScoreSheet'

export default function SetSetup({ onStart, loading }) {
  const [homeName, setHomeName] = useState('Home')
  const [awayName, setAwayName] = useState('Away')
  const [setNumber, setSetNumber] = useState(1)
  const [firstServer, setFirstServer] = useState('home')
  const [homeLineup, setHomeLineup] = useState(['1', '2', '3', '4', '5', '6'])
  const [awayLineup, setAwayLineup] = useState(['7', '8', '9', '10', '11', '12'])
  const [homeLibero, setHomeLibero] = useState('')
  const [awayLibero, setAwayLibero] = useState('')
  const [error, setError] = useState('')

  function updateLineup(side, index, value) {
    const setter = side === 'home' ? setHomeLineup : setAwayLineup
    const current = side === 'home' ? homeLineup : awayLineup
    const next = [...current]
    next[index] = value
    setter(next)
  }

  function handleSubmit(event) {
    event.preventDefault()
    setError('')
    try {
      const parseLineup = (values) => values.map((v) => Number(v))
      const body = {
        home_name: homeName.trim(),
        away_name: awayName.trim(),
        home_lineup: parseLineup(homeLineup),
        away_lineup: parseLineup(awayLineup),
        first_server: firstServer,
        set_number: Number(setNumber),
        home_libero: homeLibero ? Number(homeLibero) : null,
        away_libero: awayLibero ? Number(awayLibero) : null,
      }
      if (body.home_lineup.some(Number.isNaN) || body.away_lineup.some(Number.isNaN)) {
        throw new Error('All lineup slots need jersey numbers')
      }
      onStart(body)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form className="set-setup" onSubmit={handleSubmit}>
      <div className="card setup-hero">
        <h1>Whistle Scorebook</h1>
        <p className="subtitle">MIAA / NFHS format · one sheet per set</p>
      </div>

      <div className="card" style={{ marginTop: '1rem' }}>
        <div className="setup-grid">
          <div className="field">
            <label>
              Home team
              <input value={homeName} onChange={(e) => setHomeName(e.target.value)} />
            </label>
          </div>
          <div className="field">
            <label>
              Away team
              <input value={awayName} onChange={(e) => setAwayName(e.target.value)} />
            </label>
          </div>
          <div className="field">
            <label>
              Set number
              <select value={setNumber} onChange={(e) => setSetNumber(e.target.value)}>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    Set {n}
                    {n === 5 ? ' (to 15)' : ' (to 25)'}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="field">
            <label>
              First server
              <select value={firstServer} onChange={(e) => setFirstServer(e.target.value)}>
                <option value="home">Home</option>
                <option value="away">Away</option>
              </select>
            </label>
          </div>
        </div>

        <div className="lineups">
          {['home', 'away'].map((side) => (
            <fieldset key={side} className="lineup-card">
              <legend>{side === 'home' ? homeName : awayName} · serving order</legend>
              <div className="lineup-grid">
                {ROMANS.map((roman, index) => (
                  <label key={roman} className="lineup-slot">
                    {roman}
                    <input
                      type="number"
                      min="0"
                      max="99"
                      value={side === 'home' ? homeLineup[index] : awayLineup[index]}
                      onChange={(e) => updateLineup(side, index, e.target.value)}
                    />
                  </label>
                ))}
              </div>
              <label className="libero-field">
                Libero #
                <input
                  type="number"
                  min="0"
                  max="99"
                  placeholder="optional"
                  value={side === 'home' ? homeLibero : awayLibero}
                  onChange={(e) =>
                    side === 'home' ? setHomeLibero(e.target.value) : setAwayLibero(e.target.value)
                  }
                />
              </label>
            </fieldset>
          ))}
        </div>

        {error && <p className="error">{error}</p>}

        <div className="setup-actions">
          <button type="submit" className="btn btn-gold btn-large" disabled={loading}>
            {loading ? 'Starting…' : 'Start set'}
          </button>
        </div>
      </div>
    </form>
  )
}
