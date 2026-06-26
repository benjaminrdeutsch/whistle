const API = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || response.statusText)
  }
  return data
}

export const api = {
  startSet: (body) => request('/sets', { method: 'POST', body: JSON.stringify(body) }),
  getSet: (setId) => request(`/sets/${setId}`),
  rally: (setId, winner) =>
    request(`/sets/${setId}/rally`, { method: 'POST', body: JSON.stringify({ winner }) }),
  substitution: (setId, body) =>
    request(`/sets/${setId}/substitution`, { method: 'POST', body: JSON.stringify(body) }),
  timeout: (setId, team) =>
    request(`/sets/${setId}/timeout`, { method: 'POST', body: JSON.stringify({ team }) }),
  liberoIn: (setId, body) =>
    request(`/sets/${setId}/libero/in`, { method: 'POST', body: JSON.stringify(body) }),
  liberoOut: (setId, team) =>
    request(`/sets/${setId}/libero/out`, { method: 'POST', body: JSON.stringify({ team }) }),
  undo: (setId) => request(`/sets/${setId}/undo`, { method: 'POST' }),
}
