const API = "/api";
const resultEl = document.getElementById("result");

async function post(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

function show(data) {
  resultEl.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
}

async function register() {
  const data = await post(`${API}/register`, {
    username: document.getElementById("reg-user").value,
    password: document.getElementById("reg-pass").value,
  });
  show(data);
}

async function getBalance() {
  const data = await post(`${API}/balance`, {
    username: document.getElementById("bal-user").value,
    password: document.getElementById("bal-pass").value,
  });
  show(data);
}

async function addMoney() {
  const data = await post(`${API}/add`, {
    username: document.getElementById("add-user").value,
    password: document.getElementById("add-pass").value,
    amount: Number(document.getElementById("add-amount").value),
  });
  show(data);
}

async function transferMoney() {
  const data = await post(`${API}/transfer`, {
    username: document.getElementById("tr-user").value,
    password: document.getElementById("tr-pass").value,
    to: document.getElementById("tr-to").value,
    amount: Number(document.getElementById("tr-amount").value),
  });
  show(data);
}

async function takeLoan() {
  const data = await post(`${API}/take_loan`, {
    username: document.getElementById("loan-user").value,
    password: document.getElementById("loan-pass").value,
    amount: Number(document.getElementById("loan-amount").value),
  });
  show(data);
}

async function payLoan() {
  const data = await post(`${API}/pay_loan`, {
    username: document.getElementById("loan-user").value,
    password: document.getElementById("loan-pass").value,
    amount: Number(document.getElementById("loan-amount").value),
  });
  show(data);
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
    resultEl.innerHTML = "";
  });
});

fetch("/api/info")
  .then((r) => r.json())
  .then((data) => {
    document.getElementById("info").innerHTML =
      `<span>Pod: <strong>${data.hostname}</strong></span>` +
      `<span>IP: <strong>${data.pod_ip}</strong></span>`;
  })
  .catch(() => { });