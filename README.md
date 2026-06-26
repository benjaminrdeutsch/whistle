# Whistle

Volleyball scorebook app for **MIAA / NFHS** format (the sheet Massachusetts high schools adopted in 2019, same family as the BSN/Glover's scorebook).

Each **set** gets its own score sheet. The Python engine derives rotation, running score marks, and scoring-section notation from lineups plus match events.

## Architecture

| Layer | Stack | Role |
|---|---|---|
| Engine | Python | NFHS notation rules, rotation, libero, subs, timeouts |
| API | FastAPI | Per-set sessions, undo, REST endpoints |
| UI | React (Vite) | Setup, live scoring controls, sheet view |

## Quick start

From the project root:

```bash
./dev.sh
```

That script creates the Python venv and installs dependencies if needed, then starts:

- **API** at http://127.0.0.1:8000
- **UI** at http://localhost:5173

Press `Ctrl+C` to stop both, or run `./dev-stop.sh` from another terminal if anything is left hanging.

To verify nothing is still running:

```bash
ss -tlnp | grep -E ':8000|:5173'   # should print nothing when stopped
```

### Manual start

**Backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api` to FastAPI.

## Scoring flow

1. Enter both lineups in **serving order** (I–VI), libero numbers, set number, and first server.
2. Tap **Serve contact** when the server contacts the ball (circle, or triangle if libero).
3. Tap which team **won the rally** — the engine records slash/box/dash-bar notation.
4. Record **substitutions**, **timeouts**, and **libero in/out** between rallies.
5. **Undo** walks back one event.

## API (per set)

- `POST /api/sets` — start a new set sheet
- `POST /api/sets/{id}/serve` — serve contact
- `POST /api/sets/{id}/rally` — `{ "winner": "home" | "away" }`
- `POST /api/sets/{id}/substitution` — `{ "team", "entering", "leaving" }`
- `POST /api/sets/{id}/timeout` — `{ "team" }`
- `POST /api/sets/{id}/libero/in` — `{ "team", "slot": 0-5 }`
- `POST /api/sets/{id}/libero/out` — `{ "team" }`
- `POST /api/sets/{id}/undo`

## Not in v1

- Penalties / misconduct
- Match-level persistence (in-memory sessions only)
- Print/PDF export

## Reference

- [MIAA NFHS scoresheet (PDF)](https://www.miaa.net/sites/default/files/2024-04/volleyball_scoresheet_nfhs_201920.pdf)
- [NFHS scoring handbook (VolleyWrite)](https://volleywrite.com/wp-content/uploads/2020/08/NFHS-Paper-Scoring-Handbook.pdf)
