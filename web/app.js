const API = "/api/tasks";
const tasksEl = document.getElementById("tasks");
const form = document.getElementById("task-form");
const searchInput = document.getElementById("search");
const infoEl = document.getElementById("info");

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
  return new Date(iso).toLocaleString("en-US", {
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
    tasksEl.innerHTML = '<p class="empty">No tasks found</p>';
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

async function loadInfo() {
  try {
    const data = await request("/api/info");
    infoEl.innerHTML =
      `<span>Pod: <strong>${escapeHtml(data.hostname)}</strong></span>` +
      `<span>IP: <strong>${escapeHtml(data.pod_ip)}</strong></span>` +
      `<span>Kafka: ${data.kafka ? "✓" : "✗"}</span>` +
      `<span>ES: ${data.elasticsearch ? "✓" : "✗"}</span>`;
  } catch {
    infoEl.innerHTML = "<span>Backend unavailable</span>";
  }
}

// Search with debounce
let searchTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    const q = searchInput.value.trim();
    if (!q) {
      await loadTasks();
      return;
    }
    const results = await request(`${API}/search?q=${encodeURIComponent(q)}`);
    renderTasks(results);
  }, 300);
});

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
  searchInput.value = "";
  await loadTasks();
  await loadInfo();
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
  await loadInfo();
});

loadTasks();
loadInfo();