const COLUMNS = ["Open", "In Progress", "Testing", "Closed"];

const boardEl = document.getElementById("board");
const searchInput = document.getElementById("search-input");
const severityFilter = document.getElementById("severity-filter");
const newCardBtn = document.getElementById("new-card-btn");

let allCards = [];
let sortableInstances = [];

function columnSlug(status) {
  return status.toLowerCase().replace(/\s+/g, "_");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

function cardMatchesFilters(card) {
  const query = searchInput.value.trim().toLowerCase();
  const severity = severityFilter.value;

  if (severity && card.severity !== severity) return false;

  if (query) {
    const haystack = [card.title, ...(card.labels || [])].join(" ").toLowerCase();
    if (!haystack.includes(query)) return false;
  }
  return true;
}

function renderCard(card) {
  const labelsHtml = (card.labels || [])
    .map((l) => `<span class="card-label">${escapeHtml(l)}</span>`)
    .join("");

  return `
    <div class="card" data-card-id="${card.id}" data-severity="${card.severity}">
      <div class="card-id">#BUG-${String(card.id).padStart(3, "0")}</div>
      <div class="card-title">${escapeHtml(card.title)}</div>
      <div class="card-meta">
        <div class="card-labels">${labelsHtml}</div>
        <div class="card-assignee">${card.assignee ? escapeHtml(card.assignee) : "unassigned"}</div>
      </div>
    </div>
  `;
}

function renderBoard() {
  boardEl.innerHTML = "";
  sortableInstances.forEach((s) => s.destroy());
  sortableInstances = [];

  COLUMNS.forEach((status) => {
    const cardsInColumn = allCards
      .filter((c) => c.status === status)
      .filter(cardMatchesFilters)
      .sort((a, b) => a.position - b.position);

    const column = document.createElement("div");
    column.className = "column";
    column.dataset.status = status;

    column.innerHTML = `
      <div class="column-header">
        <span><span class="prompt">$</span> ${escapeHtml(columnSlug(status))}</span>
        <span class="column-count">${cardsInColumn.length}</span>
      </div>
      <div class="column-body" data-status="${status}">
        ${
          cardsInColumn.length
            ? cardsInColumn.map(renderCard).join("")
            : '<div class="column-empty">no issues</div>'
        }
      </div>
    `;

    boardEl.appendChild(column);
  });

  // wire drag-and-drop + click-to-open per column body
  document.querySelectorAll(".column-body").forEach((body) => {
    const sortable = Sortable.create(body, {
      group: "board",
      animation: 150,
      ghostClass: "sortable-ghost",
      chosenClass: "sortable-chosen",
      onEnd: handleCardMoved,
    });
    sortableInstances.push(sortable);

    body.querySelectorAll(".card").forEach((cardEl) => {
      cardEl.addEventListener("click", () => {
        const id = Number(cardEl.dataset.cardId);
        const card = allCards.find((c) => c.id === id);
        if (card) openEditModal(card);
      });
    });
  });
}

async function handleCardMoved(evt) {
  const cardId = Number(evt.item.dataset.cardId);
  const newStatus = evt.to.dataset.status;

  const siblings = Array.from(evt.to.children).filter((el) => el.classList.contains("card"));
  const idx = siblings.indexOf(evt.item);
  const beforeEl = siblings[idx - 1];
  const afterEl = siblings[idx + 1];

  const payload = {
    status: newStatus,
    before_id: beforeEl ? Number(beforeEl.dataset.cardId) : null,
    after_id: afterEl ? Number(afterEl.dataset.cardId) : null,
  };

  try {
    const updated = await api.updateCard(cardId, payload);
    const idxInAll = allCards.findIndex((c) => c.id === cardId);
    if (idxInAll !== -1) allCards[idxInAll] = updated;
    // Sortable only moves the dragged element -- it doesn't know about the
    // "no issues" placeholder for whichever column just emptied out (or
    // needs its placeholder removed after receiving a card). Re-render so
    // both the source and target columns end up in the right state.
    renderBoard();
  } catch (err) {
    // roll back the visual move on failure
    alert(`couldn't move card: ${err.message}`);
    await loadCards();
  }
}

async function loadCards() {
  allCards = await api.listCards();
  renderBoard();
}

searchInput.addEventListener("input", renderBoard);
severityFilter.addEventListener("change", renderBoard);
newCardBtn.addEventListener("click", () => openCreateModal());

document.addEventListener("card-saved", loadCards);
document.addEventListener("card-deleted", loadCards);

loadCards();
