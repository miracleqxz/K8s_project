const API = "/api/tasks";
const tasksEl = document.getElementById("tasks");
const form = document.getElementById("task-form");

async function request(url, opts = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (res.status === 204) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function formatDate(iso) {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function renderTasks(tasks) {
  if (!tasks.length) {
    tasksEl.innerHTML = '<p class="empty">Tasks not found</p>';
    return;
  }
  tasksEl.innerHTML = tasks
    .map(
      (t) => `
    <div class="task-card ${t.done ? "done" : ""}" data-id="${t.id}">
      <input type="checkbox" ${t.done ? "checked" : ""}>
      <div class="task-body">
        <div class="task-title">${escapeHtml(t.title)}</div>
        ${t.description ? `<div class="task-desc">${escapeHtml(t.description)}</div>` : ""}
        <div class="task-meta">${formatDate(t.created_at)}</div>
      </div>
      <button class="task-delete" title="Delete">&times;</button>
    </div>`
    )
    .join("");
}

async function loadTasks() {
  renderTasks(await request(API));
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value.trim();
  const description = document.getElementById("description").value.trim();
  if (!title) return;
  await request(API, {
    method: "POST",
    body: JSON.stringify({ title, description }),
  });
  form.reset();
  await loadTasks();
});

tasksEl.addEventListener("change", async (e) => {
  if (e.target.type !== "checkbox") return;
  const id = e.target.closest(".task-card").dataset.id;
  await request(`${API}/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ done: e.target.checked }),
  });
  await loadTasks();
});

tasksEl.addEventListener("click", async (e) => {
  if (!e.target.classList.contains("task-delete")) return;
  const id = e.target.closest(".task-card").dataset.id;
  await request(`${API}/${id}`, { method: "DELETE" });
  await loadTasks();
});

loadTasks();
