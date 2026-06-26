const ROMANS = ['I', 'II', 'III', 'IV', 'V', 'VI']

function formatMark(mark) {
  switch (mark.kind) {
    case 'serve_circle':
      return '○'
    case 'serve_triangle':
      return '△'
    case 'point_slash':
      return String(mark.value)
    case 'point_triangle':
      return `▲${mark.value}`
    case 'side_out_dash':
      return '−|'
    case 'side_out_box_scoring':
      return `[${mark.value}]`
    case 'substitution': {
      const prefix = mark.meta?.receiving_notation ? 'Sx' : 'S'
      return `${prefix} ${mark.entering}/${mark.leaving}`
    }
    case 'timeout_serving':
      return 'T'
    case 'timeout_receiving':
      return 'Tx'
    case 'libero_position_marker':
      return '▲row'
    default:
      return mark.kind
  }
}

function TeamPanel({ team, side, scoringSection, timeouts, firstServer, serving }) {
  const rows = scoringSection[side]
  return (
    <div className={`team-panel team-${side}`}>
      <header>
        <h2>{team.name}</h2>
        <div className="team-meta">
          <span className="score">{team.score}</span>
          {firstServer === side && <span className="badge">S</span>}
          {serving === side && <span className="badge serve">Serving</span>}
        </div>
      </header>

      <table className="lineup-table">
        <thead>
          <tr>
            <th>Order</th>
            <th>#</th>
            <th>Scoring</th>
          </tr>
        </thead>
        <tbody>
          {team.service_order.map((slot, index) => (
            <tr
              key={slot.roman}
              className={team.active_service_row === slot.roman ? 'active-row' : ''}
            >
              <td>
                {slot.roman}
                {team.libero_serve_row === slot.roman && <span className="libero-tri">△</span>}
              </td>
              <td className="jersey">{slot.number}</td>
              <td className="marks">
                {(rows[index] || []).map((mark, i) => (
                  <span key={i} className={`mark mark-${mark.kind}`}>
                    {formatMark(mark)}
                  </span>
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="subs-timeouts">
        <div>
          <strong>Subs</strong> {team.subs_used}/18
        </div>
        <div>
          <strong>Timeouts</strong>{' '}
          {[0, 1].map((slot) => {
            const t = timeouts[slot]
            return (
              <span key={slot} className="timeout-slot">
                {t ? t.score : '—'}
              </span>
            )
          })}
        </div>
        {team.libero && (
          <div>
            <strong>L</strong> {team.libero}
            {team.libero_on_court_slot != null && ' (on court)'}
          </div>
        )}
      </div>
    </div>
  )
}

function RunningScore({ home, away, maxScore }) {
  const points = Array.from({ length: maxScore }, (_, i) => i + 1)
  const homeMap = Object.fromEntries(home.map((m) => [m.point, m.kind]))
  const awayMap = Object.fromEntries(away.map((m) => [m.point, m.kind]))

  function renderPoint(kind, p) {
    if (kind === 'box') return `▢${p}`
    if (kind === 'slash') return `/${p}`
    if (kind === 'triangle') return `△${p}`
    return p
  }

  return (
    <div className="running-score">
      <div className="running-col away-col">
        {points.map((p) => (
          <div key={p} className={`point ${awayMap[p] || ''}`}>
            {renderPoint(awayMap[p], p)}
          </div>
        ))}
      </div>
      <div className="running-col center-col">
        {points.map((p) => (
          <div key={p} className="point-num">
            {p}
          </div>
        ))}
      </div>
      <div className="running-col home-col">
        {points.map((p) => (
          <div key={p} className={`point ${homeMap[p] || ''}`}>
            {renderPoint(homeMap[p], p)}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ScoreSheet({ state }) {
  if (!state) return null

  return (
    <section className="score-sheet">
      <div className="sheet-header">
        <h2>
          Set {state.set_number}
          {state.deciding_set && ' (deciding)'}
        </h2>
        <p>
          Play to {state.target_score}, win by 2
          {state.court_switch_at && ` · switch courts at ${state.court_switch_at}`}
          {state.court_switched && ' · courts switched'}
        </p>
      </div>

      <div className="sheet-body">
        <TeamPanel
          team={state.away}
          side="away"
          scoringSection={state.scoring_section}
          timeouts={state.timeouts.away}
          firstServer={state.first_server}
          serving={state.serving}
        />
        <RunningScore
          home={state.running_score.home}
          away={state.running_score.away}
          maxScore={state.max_score}
        />
        <TeamPanel
          team={state.home}
          side="home"
          scoringSection={state.scoring_section}
          timeouts={state.timeouts.home}
          firstServer={state.first_server}
          serving={state.serving}
        />
      </div>

      {state.completed && (
        <p className="set-complete">
          Set complete — {state.winner === 'home' ? state.home.name : state.away.name} wins
        </p>
      )}
    </section>
  )
}

export { ROMANS }
