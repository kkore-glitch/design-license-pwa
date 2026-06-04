const DATA_URL = "src/data/questions.json?v=20260603-focus";
const ASSET_VERSION = "20260603-figfix";
const STORE_KEY = "design-license-pwa-progress-v1";
const SESSION_KEY = "design-license-pwa-session-v1";
const THEME_KEY = "design-license-pwa-theme-v1";
const CHOICE_LABELS = ["A", "B", "C", "D"];

const app = document.getElementById("app");
const themeColor = document.querySelector('meta[name="theme-color"]');

let bank = null;
let state = {
  view: "mock",
  progress: loadProgress(),
  session: loadSession(),
  search: "",
  chapterFilter: "all",
  theme: loadTheme()
};

applyTheme(state.theme);

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveProgress() {
  localStorage.setItem(STORE_KEY, JSON.stringify(state.progress));
}

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
}

function saveSession() {
  if (state.session) localStorage.setItem(SESSION_KEY, JSON.stringify(state.session));
  else localStorage.removeItem(SESSION_KEY);
}

function loadTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  if (themeColor) themeColor.setAttribute("content", theme === "dark" ? "#141915" : "#f7f4ea");
}

function toggleTheme() {
  state.theme = state.theme === "dark" ? "light" : "dark";
  localStorage.setItem(THEME_KEY, state.theme);
  applyTheme(state.theme);
  render();
}

function byId(id) {
  return bank.questions.find((question) => question.id === id);
}

function progressOf(id) {
  if (!state.progress[id]) {
    state.progress[id] = {
      attempts: 0,
      correct: 0,
      wrong: 0,
      streak: 0,
      saved: false,
      mastered: false,
      lastAnswered: null
    };
  }
  return state.progress[id];
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

function isSameAnswer(selected, correct) {
  if (selected.length !== correct.length) return false;
  const left = [...selected].sort().join(",");
  const right = [...correct].sort().join(",");
  return left === right;
}

function availableForMock() {
  return bank.questions.filter((question) => !question.needsImage);
}

function startSession(mode, questions, title, timed = false) {
  const orderedQuestions = questions.length > 1 ? shuffle(questions) : questions;
  state.session = {
    mode,
    title,
    ids: orderedQuestions.map((question) => question.id),
    index: 0,
    selected: [],
    submitted: false,
    results: [],
    startedAt: Date.now(),
    timeLimitSeconds: timed ? 100 * 60 : null
  };
  saveSession();
  render();
  scrollToTop();
}

function startMock() {
  startSession("mock", shuffle(availableForMock()).slice(0, 80), "80 題模擬測驗", true);
}

function startRandom(count = 20) {
  startSession("practice", shuffle(bank.questions).slice(0, count), `${count} 題隨機練習`, false);
}

function startChapter(chapter) {
  const questions = bank.questions.filter((question) => question.chapter === chapter);
  startSession("chapter", questions, chapter, false);
}

function startQuestionList(title, questions) {
  if (!questions.length) return;
  startSession("practice", questions, title, false);
}

function toggleChoice(index) {
  const session = state.session;
  if (!session || session.submitted) return;
  const question = byId(session.ids[session.index]);
  if (question.answerIndices.length === 1) {
    session.selected = [index];
  } else if (session.selected.includes(index)) {
    session.selected = session.selected.filter((item) => item !== index);
  } else {
    session.selected = [...session.selected, index];
  }
  saveSession();
  updateChoiceSelection();
}

function updateChoiceSelection() {
  const session = state.session;
  if (!session) return;
  document.querySelectorAll("[data-choice]").forEach((button) => {
    button.classList.toggle("selected", session.selected.includes(Number(button.dataset.choice)));
  });
  const submit = document.querySelector('[data-action="submit-answer"]');
  if (submit) submit.disabled = session.selected.length === 0;
}

function submitAnswer() {
  const session = state.session;
  const question = byId(session.ids[session.index]);
  if (!session.selected.length) return;

  const correct = isSameAnswer(session.selected, question.answerIndices);
  const item = progressOf(question.id);
  item.attempts += 1;
  item.lastAnswered = new Date().toISOString();
  if (correct) {
    item.correct += 1;
    item.streak += 1;
    if (item.streak >= 2) item.mastered = true;
  } else {
    item.wrong += 1;
    item.streak = 0;
    item.mastered = false;
  }

  session.submitted = true;
  session.results[session.index] = { id: question.id, selected: session.selected, correct };
  saveProgress();
  saveSession();
  render({ animate: false });
}

function goNext() {
  const session = state.session;
  if (session.index >= session.ids.length - 1) {
    session.finishedAt = Date.now();
  } else {
    session.index += 1;
    session.selected = [];
    session.submitted = false;
  }
  saveSession();
  render();
  scrollToTop();
}

function endSession() {
  state.session = null;
  saveSession();
  render();
}

function toggleSaved(id) {
  const item = progressOf(id);
  item.saved = !item.saved;
  saveProgress();
  render({ animate: false });
}

function markMastered(id) {
  const item = progressOf(id);
  item.mastered = true;
  item.streak = Math.max(item.streak, 2);
  saveProgress();
  render({ animate: false });
}

function scrollToTop() {
  requestAnimationFrame(() => window.scrollTo({ top: 0, left: 0, behavior: "auto" }));
}

function visibleQuestions() {
  const query = state.search.trim().toLowerCase();
  return bank.questions.filter((question) => {
    const chapterOk = state.chapterFilter === "all" || question.chapter === state.chapterFilter;
    const queryOk =
      !query ||
      question.question.toLowerCase().includes(query) ||
      question.choices.some((choice) => choice.toLowerCase().includes(query));
    return chapterOk && queryOk;
  });
}

function wrongQuestions() {
  return bank.questions.filter((question) => {
    const item = state.progress[question.id];
    return item && item.wrong > 0 && !item.mastered;
  });
}

function savedQuestions() {
  return bank.questions.filter((question) => state.progress[question.id]?.saved);
}

function answeredQuestions() {
  return bank.questions.filter((question) => state.progress[question.id]?.attempts > 0);
}

function timerLabel(session) {
  if (!session.timeLimitSeconds) return "";
  const elapsed = Math.floor((Date.now() - session.startedAt) / 1000);
  const remain = Math.max(0, session.timeLimitSeconds - elapsed);
  const minutes = String(Math.floor(remain / 60)).padStart(2, "0");
  const seconds = String(remain % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function header() {
  const isDark = state.theme === "dark";
  return `
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <p class="eyebrow">12600 乙級</p>
          <h1>室內裝修工程管理題庫</h1>
        </div>
        <div class="top-actions">
          <div class="source-note">
            ${bank.meta.questionCount} 題<br />
            A12 公開題庫
          </div>
          <button class="theme-toggle" data-action="toggle-theme" aria-label="切換${isDark ? "日間" : "夜間"}模式">
            <span>${isDark ? "日間" : "夜間"}</span>
          </button>
        </div>
      </div>
    </header>
  `;
}

function nav() {
  const items = [
    ["mock", "模擬"],
    ["bank", "題庫"],
    ["wrong", `錯題 ${wrongQuestions().length}`],
    ["saved", `收藏 ${savedQuestions().length}`],
    ["progress", "進度"]
  ];
  return `
    <nav class="bottom-nav" aria-label="主要功能">
      <div class="bottom-nav-inner">
        ${items
          .map(
            ([view, label]) =>
              `<button class="nav-btn ${state.view === view ? "active" : ""}" data-view="${view}">${label}</button>`
          )
          .join("")}
      </div>
    </nav>
  `;
}

function renderShell(content, options = {}) {
  const focus = Boolean(options.focus);
  const animate = options.animate !== false;
  app.classList.toggle("focus-shell", focus);
  app.innerHTML = `${focus ? "" : header()}<main class="main ${focus ? "main-focus" : ""}"><div class="page-transition ${animate ? "" : "no-motion"}">${content}</div></main>${focus ? "" : nav()}`;
  bindGlobalEvents();
}

function renderMock() {
  const total = bank.questions.length;
  const ready = availableForMock().length;
  const wrong = wrongQuestions().length;
  const saved = savedQuestions().length;
  const answered = answeredQuestions().length;

  renderShell(`
    <section class="panel hero">
      <div>
        <p class="eyebrow">主流程</p>
        <h2 class="hero-title">80 題模擬測驗</h2>
        <p class="hero-copy">每次從可直接作答的題目中抽 80 題。複選題會要求選出全部正確選項，交卷後可查看錯題與章節分布。</p>
        <div class="quick-strip" aria-label="目前題庫狀態">
          <span>${ready} 題可抽考</span>
          <span>${wrong} 題待複習</span>
          <span>${saved} 題收藏</span>
        </div>
        <div class="actions">
          <button class="btn primary" data-action="start-mock">開始 80 題</button>
          <button class="btn" data-action="start-random">20 題練習</button>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat"><span>題庫</span><strong>${total}</strong></div>
        <div class="stat"><span>可抽考</span><strong>${ready}</strong></div>
        <div class="stat"><span>已作答</span><strong>${answered}</strong></div>
        <div class="stat"><span>錯題</span><strong>${wrong}</strong></div>
        <div class="stat"><span>收藏</span><strong>${saved}</strong></div>
        <div class="stat"><span>需看圖</span><strong>${total - ready}</strong></div>
      </div>
    </section>

    <div class="section-title">
      <h2>章節練習</h2>
      <span>依官方工作項目</span>
    </div>
    <section class="chapter-grid">
      ${bank.chapters
        .map((chapter) => {
          const count = bank.questions.filter((question) => question.chapter === chapter.name).length;
          return `<button class="chapter-row" data-chapter="${chapter.name}">
            <span><strong>${chapter.id} ${chapter.name}</strong><span>${count} 題可練</span></span>
            <span class="row-action">開始</span>
          </button>`;
        })
        .join("")}
    </section>
  `);
}

function renderBank() {
  const questions = visibleQuestions();
  renderShell(`
    <div class="section-title">
      <h2>完整題庫</h2>
      <span>${questions.length} / ${bank.questions.length} 題</span>
    </div>
    <div class="filters">
      <input class="field" id="search" value="${escapeHtml(state.search)}" placeholder="搜尋題幹或選項" />
      <select class="field" id="chapterFilter">
        <option value="all">全部章節</option>
        ${bank.chapters
          .map((chapter) => `<option value="${chapter.name}" ${state.chapterFilter === chapter.name ? "selected" : ""}>${chapter.name}</option>`)
          .join("")}
      </select>
    </div>
    <div class="actions">
      <button class="btn primary" data-action="practice-filtered">練目前清單</button>
      <button class="btn" data-action="start-random">20 題隨機</button>
    </div>
    <section class="question-list">
      ${questions.slice(0, 120).map(questionLine).join("")}
    </section>
    ${questions.length > 120 ? `<p class="empty-state">目前只顯示前 120 題，請用搜尋或章節篩選縮小範圍。</p>` : ""}
  `);
}

function questionLine(question) {
  const item = state.progress[question.id] || {};
  const isMulti = question.answerIndices.length > 1;
  const labels = [
    question.needsImage ? "<mark>需看圖</mark>" : "",
    isMulti ? `<mark class="multi-mark">複選</mark>` : "",
    item.saved ? "<mark>收藏</mark>" : "",
    item.mastered ? "<mark>已掌握</mark>" : ""
  ]
    .filter(Boolean)
    .join(" ");
  return `<button class="question-line ${isMulti ? "multi-line" : ""}" data-open-question="${question.id}">
    <span><strong>${question.number}. ${escapeHtml(question.question)}</strong><span>${question.chapter} ${labels}</span></span>
  </button>`;
}

function renderWrong() {
  const questions = wrongQuestions();
  renderShell(`
    <div class="section-title"><h2>錯題</h2><span>${questions.length} 題</span></div>
    ${
      questions.length
        ? `<div class="actions"><button class="btn primary" data-action="practice-wrong">重練錯題</button><button class="btn" data-action="start-random">20 題隨機</button></div><section class="question-list">${questions.map(questionLine).join("")}</section>`
        : `<div class="empty-state">目前沒有待複習錯題。答錯的題目會自動進來，連續答對或手動標記後會離開這裡。</div>`
    }
  `);
}

function renderSaved() {
  const questions = savedQuestions();
  renderShell(`
    <div class="section-title"><h2>收藏</h2><span>${questions.length} 題</span></div>
    ${
      questions.length
        ? `<div class="actions"><button class="btn primary" data-action="practice-saved">練收藏題</button><button class="btn warn" data-action="clear-saved">清除收藏</button></div><section class="question-list">${questions.map(questionLine).join("")}</section>`
        : `<div class="empty-state">還沒有收藏題。作答或瀏覽題庫時可以把需要回看的題目加進收藏。</div>`
    }
  `);
}

function renderProgress() {
  const answered = answeredQuestions();
  const totalAttempts = Object.values(state.progress).reduce((sum, item) => sum + item.attempts, 0);
  const totalCorrect = Object.values(state.progress).reduce((sum, item) => sum + item.correct, 0);
  const accuracy = totalAttempts ? Math.round((totalCorrect / totalAttempts) * 100) : 0;
  const byChapter = bank.chapters.map((chapter) => {
    const questions = bank.questions.filter((question) => question.chapter === chapter.name);
    const done = questions.filter((question) => state.progress[question.id]?.attempts > 0).length;
    return { ...chapter, done, total: questions.length };
  });

  renderShell(`
    <div class="section-title"><h2>進度</h2><span>本機紀錄</span></div>
    <section class="result-grid">
      <div class="stat"><span>已練題數</span><strong>${answered.length}</strong></div>
      <div class="stat"><span>作答次數</span><strong>${totalAttempts}</strong></div>
      <div class="stat"><span>正答率</span><strong>${accuracy}%</strong></div>
      <div class="stat"><span>錯題</span><strong>${wrongQuestions().length}</strong></div>
    </section>
    <div class="section-title"><h2>章節覆蓋</h2><span>${bank.chapters.length} 章</span></div>
    <section class="chapter-grid">
      ${byChapter
        .map(
          (chapter) => `<div class="chapter-row">
            <span><strong>${chapter.id} ${chapter.name}</strong><span>${chapter.done} / ${chapter.total} 題已練</span></span>
            <span class="row-action">${chapter.total ? Math.round((chapter.done / chapter.total) * 100) : 0}%</span>
          </div>`
        )
        .join("")}
    </section>
    <div class="actions">
      <button class="btn warn" data-action="reset-progress">清除本機紀錄</button>
      <button class="btn" data-action="start-random">20 題隨機</button>
    </div>
  `);
}

function renderSession(options = {}) {
  const session = state.session;
  if (session.finishedAt) return renderResult();
  const question = byId(session.ids[session.index]);
  const item = state.progress[question.id] || {};
  const pct = Math.round(((session.index + 1) / session.ids.length) * 100);
  const isMulti = question.answerIndices.length > 1;
  const selected = session.selected || [];
  const result = session.results[session.index];

  renderShell(`
    <section class="panel session-card ${isMulti ? "multi-session" : ""}">
      <div class="session-head">
        <div>
          <p class="eyebrow">${session.title}</p>
          <strong>${session.index + 1} / ${session.ids.length}</strong>
        </div>
        <button class="btn ghost" data-action="end-session">離開</button>
      </div>
      <div class="session-top-actions">
        <button class="btn" data-action="toggle-save" data-id="${question.id}">${item.saved ? "取消收藏" : "收藏"}</button>
        <button class="btn" data-action="mark-mastered" data-id="${question.id}">${item.mastered ? "已掌握" : "標記已掌握"}</button>
      </div>
      <div class="progress-track"><div class="progress-bar" style="width:${pct}%"></div></div>
      <div class="question-meta">
        <span class="pill">${question.chapter}</span>
        <span class="pill ${isMulti ? "multi-pill" : ""}">${isMulti ? "複選題" : "單選題"}</span>
        ${question.needsImage ? `<span class="pill">需看圖，未放入模擬測驗</span>` : ""}
        ${session.timeLimitSeconds ? `<span class="pill">剩餘 ${timerLabel(session)}</span>` : ""}
      </div>
      <h2 class="question-text">${escapeHtml(question.question)}</h2>
      ${question.image ? `<figure class="question-figure"><img src="${escapeHtml(`${question.image}?v=${ASSET_VERSION}`)}" alt="題目圖例" loading="lazy" /></figure>` : ""}
      <div class="choice-grid">
        ${question.choices
          .map((choice, index) => {
            const selectedClass = selected.includes(index) ? "selected" : "";
            const correctnessClass = session.submitted
              ? question.answerIndices.includes(index)
                ? "correct"
                : selected.includes(index)
                  ? "incorrect"
                  : ""
              : "";
            return `<button class="choice ${selectedClass} ${correctnessClass}" data-choice="${index}">
              <span class="badge">${CHOICE_LABELS[index]}</span>
              <span>${escapeHtml(choice)}</span>
            </button>`;
          })
          .join("")}
      </div>
      ${answerPanel(question, session, result, isMulti)}
      <div class="session-actions">
        ${
          session.submitted
            ? `<button class="btn primary" data-action="next-question">${session.index >= session.ids.length - 1 ? "查看結果" : "下一題"}</button>`
            : `<button class="btn primary" data-action="submit-answer" ${selected.length ? "" : "disabled"}>送出答案</button>`
        }
      </div>
    </section>
  `, { focus: true, animate: options.animate });
}

function renderResult() {
  const session = state.session;
  const correct = session.results.filter((result) => result.correct).length;
  const score = Math.round((correct / session.ids.length) * 100);
  const wrong = session.results.filter((result) => !result.correct).map((result) => byId(result.id));
  const chapterCount = session.results.reduce((acc, result) => {
    const chapter = byId(result.id).chapter;
    acc[chapter] = acc[chapter] || { total: 0, correct: 0 };
    acc[chapter].total += 1;
    if (result.correct) acc[chapter].correct += 1;
    return acc;
  }, {});

  renderShell(`
    <section class="panel session-card">
      <p class="eyebrow">${session.title}</p>
      <h2 class="hero-title">結果 ${score}%</h2>
      <section class="result-grid">
        <div class="stat"><span>題數</span><strong>${session.ids.length}</strong></div>
        <div class="stat"><span>答對</span><strong>${correct}</strong></div>
        <div class="stat"><span>答錯</span><strong>${wrong.length}</strong></div>
        <div class="stat"><span>及格線</span><strong>${score >= 60 ? "通過" : "未達"}</strong></div>
      </section>
      <div class="section-title"><h2>章節分布</h2><span>答對 / 題數</span></div>
      <section class="chapter-grid">
        ${Object.entries(chapterCount)
          .map(
            ([chapter, item]) => `<div class="chapter-row"><span><strong>${chapter}</strong><span>${item.correct} / ${item.total}</span></span><span>${Math.round((item.correct / item.total) * 100)}%</span></div>`
          )
          .join("")}
      </section>
      <div class="actions">
        <button class="btn primary" data-action="start-mock">再做一回</button>
        <button class="btn" data-action="end-session">回首頁</button>
      </div>
    </section>
    <div class="section-title"><h2>本回錯題</h2><span>${wrong.length} 題</span></div>
    ${wrong.length ? `<section class="question-list">${wrong.map(questionLine).join("")}</section>` : `<div class="empty-state">本回沒有錯題。</div>`}
  `);
}

function answerPanel(question, session, result, isMulti) {
  if (!session.submitted) {
    return isMulti ? `<div class="answer-box">這題是複選。請選出所有正確選項後送出。</div>` : "";
  }
  const answerText = question.answerIndices.map((index) => `${CHOICE_LABELS[index]} ${question.choices[index]}`).join("、");
  return `<div class="answer-box ${result.correct ? "good" : "bad"}">
    <strong>${result.correct ? "作答正確" : "作答錯誤"}</strong>
    <div class="answer-line">正解：${escapeHtml(answerText)}</div>
  </div>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function bindGlobalEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      render();
    });
  });

  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "start-mock") startMock();
      if (action === "start-random") startRandom();
      if (action === "toggle-theme") toggleTheme();
      if (action === "practice-filtered") startQuestionList("篩選題庫練習", visibleQuestions());
      if (action === "practice-wrong") startQuestionList("錯題重練", wrongQuestions());
      if (action === "practice-saved") startQuestionList("收藏題練習", savedQuestions());
      if (action === "submit-answer") submitAnswer();
      if (action === "next-question") goNext();
      if (action === "end-session") endSession();
      if (action === "toggle-save") toggleSaved(button.dataset.id);
      if (action === "mark-mastered") markMastered(button.dataset.id);
      if (action === "clear-saved") {
        savedQuestions().forEach((question) => {
          progressOf(question.id).saved = false;
        });
        saveProgress();
        render();
      }
      if (action === "reset-progress" && confirm("要清除所有本機作答與收藏紀錄嗎？")) {
        state.progress = {};
        saveProgress();
        render();
      }
    });
  });

  document.querySelectorAll("[data-chapter]").forEach((button) => {
    button.addEventListener("click", () => startChapter(button.dataset.chapter));
  });

  document.querySelectorAll("[data-open-question]").forEach((button) => {
    button.addEventListener("click", () => startQuestionList("單題查看", [byId(button.dataset.openQuestion)]));
  });

  document.querySelectorAll("[data-choice]").forEach((button) => {
    button.addEventListener("click", () => toggleChoice(Number(button.dataset.choice)));
  });

  const search = document.getElementById("search");
  if (search) {
    search.addEventListener("input", (event) => {
      state.search = event.target.value;
      renderBank();
    });
  }

  const chapterFilter = document.getElementById("chapterFilter");
  if (chapterFilter) {
    chapterFilter.addEventListener("change", (event) => {
      state.chapterFilter = event.target.value;
      renderBank();
    });
  }
}

function render(options = {}) {
  if (state.session) return renderSession(options);
  if (state.view === "bank") return renderBank();
  if (state.view === "wrong") return renderWrong();
  if (state.view === "saved") return renderSaved();
  if (state.view === "progress") return renderProgress();
  return renderMock();
}

fetch(DATA_URL)
  .then((response) => {
    if (!response.ok) throw new Error("question data load failed");
    return response.json();
  })
  .then((payload) => {
    bank = payload;
    render();
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("sw.js")
        .then((registration) => registration.update())
        .catch(() => {});
    }
    setInterval(() => {
      if (state.session?.timeLimitSeconds && !state.session.finishedAt) render({ animate: false });
    }, 30000);
  })
  .catch(() => {
    app.innerHTML = `<main class="loading-view"><p class="eyebrow">載入失敗</p><h1>題庫資料無法載入</h1><p>請用本機伺服器或 GitHub Pages 開啟，不要直接用 file://。</p></main>`;
  });

document.addEventListener("gesturestart", (event) => event.preventDefault(), { passive: false });
document.addEventListener("gesturechange", (event) => event.preventDefault(), { passive: false });
