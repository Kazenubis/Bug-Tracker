const overlay = document.getElementById("card-modal-overlay");
const form = document.getElementById("card-form");
const modalTitle = document.getElementById("modal-title");
const modalError = document.getElementById("modal-error");
const deleteBtn = document.getElementById("delete-card-btn");
const activitySection = document.getElementById("activity-section");
const activityList = document.getElementById("activity-list");

const fields = {
  id: document.getElementById("card-id-field"),
  title: document.getElementById("title-field"),
  description: document.getElementById("description-field"),
  severity: document.getElementById("severity-field"),
  status: document.getElementById("status-field"),
  assignee: document.getElementById("assignee-field"),
  labels: document.getElementById("labels-field"),
};

function resetForm() {
  form.reset();
  fields.id.value = "";
  modalError.hidden = true;
  modalError.textContent = "";
}

function openCreateModal() {
  resetForm();
  modalTitle.textContent = "new issue";
  deleteBtn.hidden = true;
  activitySection.hidden = true;
  overlay.hidden = false;
  fields.title.focus();
}

async function openEditModal(card) {
  resetForm();
  modalTitle.textContent = `#bug-${String(card.id).padStart(3, "0")}`;
  fields.id.value = card.id;
  fields.title.value = card.title;
  fields.description.value = card.description || "";
  fields.severity.value = card.severity;
  fields.status.value = card.status;
  fields.assignee.value = card.assignee || "";
  fields.labels.value = (card.labels || []).join(", ");
  deleteBtn.hidden = false;
  overlay.hidden = false;

  activitySection.hidden = false;
  activityList.innerHTML = '<li class="activity-item">loading&hellip;</li>';
  try {
    const entries = await api.getActivity(card.id);
    renderActivity(entries);
  } catch (err) {
    activityList.innerHTML = `<li class="activity-item">couldn't load activity</li>`;
  }
}

function formatActivityEntry(entry) {
  const time = new Date(entry.timestamp).toLocaleString();
  let text;
  if (entry.event_type === "created") {
    text = "issue created";
  } else {
    text = `<strong>${entry.field}</strong> changed from <strong>${entry.from_value ?? "&mdash;"}</strong> to <strong>${entry.to_value ?? "&mdash;"}</strong>`;
  }
  return `<li class="activity-item">${text}<span class="activity-time">${time}</span></li>`;
}

function renderActivity(entries) {
  if (!entries.length) {
    activityList.innerHTML = '<li class="activity-item">no activity yet</li>';
    return;
  }
  activityList.innerHTML = entries.map(formatActivityEntry).join("");
}

function closeModal() {
  overlay.hidden = true;
}

document.getElementById("modal-close-btn").addEventListener("click", closeModal);
document.getElementById("cancel-btn").addEventListener("click", closeModal);
overlay.addEventListener("click", (e) => {
  if (e.target === overlay) closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && !overlay.hidden) closeModal();
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  modalError.hidden = true;

  const payload = {
    title: fields.title.value.trim(),
    description: fields.description.value.trim(),
    severity: fields.severity.value,
    status: fields.status.value,
    assignee: fields.assignee.value.trim(),
    labels: fields.labels.value.split(",").map((l) => l.trim()).filter(Boolean),
  };

  const cardId = fields.id.value;

  try {
    if (cardId) {
      await api.updateCard(cardId, payload);
    } else {
      await api.createCard(payload);
    }
    closeModal();
    document.dispatchEvent(new CustomEvent("card-saved"));
  } catch (err) {
    modalError.textContent = err.message;
    modalError.hidden = false;
  }
});

deleteBtn.addEventListener("click", async () => {
  const cardId = fields.id.value;
  if (!cardId) return;
  if (!confirm("delete this issue? this can't be undone.")) return;

  try {
    await api.deleteCard(cardId);
    closeModal();
    document.dispatchEvent(new CustomEvent("card-deleted"));
  } catch (err) {
    modalError.textContent = err.message;
    modalError.hidden = false;
  }
});
