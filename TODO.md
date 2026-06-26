# Whistle — TODO

Track completed work and deferred items. Check off with `[x]` as things ship.

---

## Basic Features

- [x] Target MIAA / NFHS scoresheet format (not NCAA)
- [x] FastAPI backend for the scorebook engine
- [x] React (Vite) frontend
- [x] Per-set model — one score sheet per set
- [x] Rally scoring (sets 1–4 to 25 win-by-2; set 5 to 15, switch courts at 8)
- [x] Lineups in serving order (I–VI) for both teams
- [x] Rally winner as the primary scoring input
- [x] Auto-derived rotation, server, and scoring-section notation
- [x] Implicit serve contact — circles/triangles inferred from possession (no separate button)
- [x] Libero in/out and first libero-serve position marker (triangle on Roman numeral)
- [x] Substitutions (S / Sx notation, player-number column updates, 18-sub cap)
- [x] Timeouts (2 per team, score recorded at time of request)
- [x] Undo last event
- [x] `dev.sh` / `dev-stop.sh` to run and stop both servers cleanly
- [x] Muted black / gold / purple UI theme
- [x] MIT license

---

## Engine & notation

- [ ] Re-serve (`RS`) — server tosses and catches; second re-serve is loss of rally
- [ ] Replay (`P`) — rally stopped and replayed; no point recorded
- [ ] Penalties and misconduct (YC, RC, delay penalties, individual penalties)
- [ ] Referee mind changes (`M`) — cancel and rewrite prior notation
- [ ] Wrong server / rotation fault — square notation, point removal, corrections
- [ ] Exceptional substitution and disqualification flows
- [ ] Service-round ink color alternation (black/red per full round of serves) in sheet view
- [ ] Cap score at 30 (sets 1–4) enforced visually on running-score column

---

## Match & data

- [ ] Match wrapper — chain sets 1–5 under one match ID
- [ ] Persist sessions to disk (SQLite) so refresh doesn't lose the set
- [ ] Match history / season archive
- [ ] Export or print score sheet (PDF matching official MIAA Form #1 / #2)
- [ ] Roster and lineup sheet entry (MIAA Form #4)
- [ ] Separate libero tracking sheet view (MIAA Form #3)

---

## UI / UX

- [ ] Pixel-perfect official scoresheet layout (SVG or canvas)
- [ ] School color customization (exact hex values beyond current theme defaults)
- [ ] Live-match mode — larger tap targets, one-handed scoring layout
- [ ] Set-complete flow — prompt to start next set with swapped sides / lineups
- [ ] Header info fields (date, site, officials, set start/end time)
- [ ] Comments and sanctions section on the sheet

---

## Infrastructure & quality

- [ ] API integration tests (httpx / FastAPI TestClient)
- [ ] End-to-end smoke test for a full sample set
- [ ] CI workflow (pytest + frontend build)
- [ ] Docker Compose for one-command deploy

---

## Misc Ideas
- [ ] Allow for saving games to an account
- [ ] Support for exporting saved games as PDFs


## Notes

**Serve inference assumption:** Every recorded rally implies exactly one serve contact by the team in possession at the start of that rally. Re-serves and replays break that 1:1 mapping and need explicit events when we add them.

**Side-out logic:** Receiving team wins → rotate clockwise, new server is position 1, dash-bar on outgoing server, boxed point on incoming server's row.

**Lineup entry:** NFHS/MIAA uses serving order I–VI for both teams regardless of who serves first (unlike the old NCAA sheet).
