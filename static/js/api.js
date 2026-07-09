const API_BASE = "/api/cards";

async function handleResponse(res) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const message = (data && data.error) || `request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

const api = {
  listCards() {
    return fetch(API_BASE).then(handleResponse);
  },

  createCard(payload) {
    return fetch(API_BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(handleResponse);
  },

  updateCard(id, payload) {
    return fetch(`${API_BASE}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(handleResponse);
  },

  deleteCard(id) {
    return fetch(`${API_BASE}/${id}`, { method: "DELETE" }).then(handleResponse);
  },

  getActivity(id) {
    return fetch(`${API_BASE}/${id}/activity`).then(handleResponse);
  },
};
