(() => {
  const form = document.getElementById("upload-form");
  const runBtn = document.getElementById("run-btn");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");
  const mainList = document.getElementById("main-files");
  const extraList = document.getElementById("extra-files");

  const files = {
    crm: null,
    bank: null,
    catalog: null,
    chats: null,
  };

  function refreshReady() {
    const ready = Object.values(files).every(Boolean);
    runBtn.disabled = !ready;
  }

  function setStatus(text, kind = "") {
    statusEl.textContent = text || "";
    statusEl.className = `status${kind ? ` ${kind}` : ""}`;
  }

  function bindDrop(zone) {
    const key = zone.dataset.key;
    const input = zone.querySelector('input[type="file"]');
    const nameEl = zone.querySelector("[data-filename]");

    const assign = (file) => {
      if (!file) return;
      files[key] = file;
      nameEl.textContent = file.name;
      zone.classList.add("has-file");
      refreshReady();
    };

    input.addEventListener("change", () => {
      assign(input.files && input.files[0]);
    });

    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("dragover");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      zone.classList.remove("dragover");
      const file = event.dataTransfer.files && event.dataTransfer.files[0];
      if (!file) return;
      // синхронизируем input для единообразия
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      assign(file);
    });
  }

  form.querySelectorAll(".drop").forEach(bindDrop);

  function renderList(ul, items) {
    ul.innerHTML = "";
    items.forEach((item) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = item.url;
      a.innerHTML = `<span>${item.title}</span><span class="meta">${item.name}</span>`;
      li.appendChild(a);
      ul.appendChild(li);
    });
  }

  runBtn.addEventListener("click", async () => {
    if (runBtn.disabled) return;
    runBtn.disabled = true;
    resultsEl.classList.add("hidden");
    setStatus("Считаем… вызываем python solve.py и собираем артефакты", "busy");

    const body = new FormData();
    Object.entries(files).forEach(([key, file]) => body.append(key, file, file.name));

    try {
      const response = await fetch("/api/process", { method: "POST", body });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "ошибка обработки");
      }
      renderList(mainList, data.main || []);
      renderList(extraList, data.additional || []);
      resultsEl.classList.remove("hidden");
      setStatus("Готово. Можно скачать файлы ниже.", "");
    } catch (error) {
      setStatus(error.message || String(error), "error");
    } finally {
      refreshReady();
    }
  });
})();
