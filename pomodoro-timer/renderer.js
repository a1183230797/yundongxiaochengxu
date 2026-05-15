const STORAGE_KEY = "pomodoro-settings-v1";
const STATS_KEY = "pomodoro-stats-v1";

const MODES = {
  focus: { label: "专注中", phase: "focus" },
  short: { label: "短休息", phase: "short" },
  long: { label: "长休息", phase: "long" },
};

const RING_LEN = 2 * Math.PI * 54;

const els = {
  timeDisplay: document.getElementById("timeDisplay"),
  phaseLabel: document.getElementById("phaseLabel"),
  ringProgress: document.getElementById("ringProgress"),
  btnPrimary: document.getElementById("btnPrimary"),
  btnReset: document.getElementById("btnReset"),
  modeBtns: document.querySelectorAll(".mode-btn"),
  durFocus: document.getElementById("durFocus"),
  durShort: document.getElementById("durShort"),
  durLong: document.getElementById("durLong"),
  completedCount: document.getElementById("completedCount"),
  cycleHint: document.getElementById("cycleHint"),
  alwaysOnTop: document.getElementById("alwaysOnTop"),
};

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { focus: 25, short: 5, long: 15 };
    const p = JSON.parse(raw);
    return {
      focus: Math.min(120, Math.max(1, Number(p.focus) || 25)),
      short: Math.min(60, Math.max(1, Number(p.short) || 5)),
      long: Math.min(60, Math.max(1, Number(p.long) || 15)),
    };
  } catch {
    return { focus: 25, short: 5, long: 15 };
  }
}

function saveSettings(s) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_KEY);
    const today = new Date().toDateString();
    if (!raw) return { date: today, focusDone: 0, sessionCount: 0 };
    const p = JSON.parse(raw);
    if (p.date !== today) return { date: today, focusDone: 0, sessionCount: 0 };
    return {
      date: today,
      focusDone: Math.max(0, Number(p.focusDone) || 0),
      sessionCount: Math.max(0, Number(p.sessionCount) || 0),
    };
  } catch {
    return { date: new Date().toDateString(), focusDone: 0, sessionCount: 0 };
  }
}

function saveStats(s) {
  localStorage.setItem(STATS_KEY, JSON.stringify(s));
}

let settings = loadSettings();
let stats = loadStats();

let currentMode = "focus";
let totalSeconds = settings.focus * 60;
let remaining = totalSeconds;
let running = false;
let tickId = null;
let audioCtx = null;

function beep() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const o = audioCtx.createOscillator();
    const g = audioCtx.createGain();
    o.connect(g);
    g.connect(audioCtx.destination);
    o.frequency.value = 880;
    o.type = "sine";
    g.gain.setValueAtTime(0.15, audioCtx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
    o.start(audioCtx.currentTime);
    o.stop(audioCtx.currentTime + 0.35);
  } catch {
    /* ignore */
  }
}

function notify(title, body) {
  if (typeof Notification !== "undefined" && Notification.permission === "granted") {
    new Notification(title, { body });
  }
}

function requestNotifyPermission() {
  if (typeof Notification !== "undefined" && Notification.permission === "default") {
    Notification.requestPermission();
  }
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function setRingProgress(ratio) {
  const offset = RING_LEN * (1 - ratio);
  els.ringProgress.style.strokeDasharray = `${RING_LEN}`;
  els.ringProgress.style.strokeDashoffset = String(offset);
}

function applyBodyMode() {
  document.body.classList.remove("mode-focus", "mode-short", "mode-long");
  document.body.classList.add(`mode-${MODES[currentMode].phase}`);
}

function getDurationMinutes(mode) {
  return settings[mode === "focus" ? "focus" : mode === "short" ? "short" : "long"];
}

function syncDurationInputs() {
  els.durFocus.value = String(settings.focus);
  els.durShort.value = String(settings.short);
  els.durLong.value = String(settings.long);
}

function updateStatsUI() {
  stats = loadStats();
  els.completedCount.textContent = String(stats.focusDone);
  const n = stats.sessionCount;
  if (n > 0 && n % 4 === 0) {
    els.cycleHint.textContent = "刚完成一组，建议长休";
  } else {
    const left = 4 - (n % 4);
    els.cycleHint.textContent = `再走 ${left} 个专注 → 长休`;
  }
}

function resetTimerForMode() {
  stopTick();
  totalSeconds = getDurationMinutes(currentMode) * 60;
  remaining = totalSeconds;
  running = false;
  els.btnPrimary.textContent = "开始";
  els.phaseLabel.textContent = "准备开始";
  els.timeDisplay.textContent = formatTime(remaining);
  setRingProgress(1);
  els.btnPrimary.disabled = false;
}

function stopTick() {
  if (tickId !== null) {
    clearInterval(tickId);
    tickId = null;
  }
}

function onComplete() {
  stopTick();
  running = false;
  remaining = 0;
  els.timeDisplay.textContent = formatTime(0);
  setRingProgress(0);
  els.btnPrimary.textContent = "开始";
  els.phaseLabel.textContent = "本轮结束";

  if (currentMode === "focus") {
    stats = loadStats();
    stats.focusDone += 1;
    stats.sessionCount += 1;
    saveStats(stats);
    updateStatsUI();
    notify("专注完成", "休息一下吧。");
    beep();
  } else {
    notify("休息结束", "可以开始下一轮专注。");
    beep();
  }
}

function tick() {
  remaining -= 1;
  if (remaining <= 0) {
    onComplete();
    return;
  }
  els.timeDisplay.textContent = formatTime(remaining);
  setRingProgress(remaining / totalSeconds);
}

function start() {
  requestNotifyPermission();
  if (remaining <= 0) {
    totalSeconds = getDurationMinutes(currentMode) * 60;
    remaining = totalSeconds;
  }
  running = true;
  els.btnPrimary.textContent = "暂停";
  els.phaseLabel.textContent = MODES[currentMode].label;
  setRingProgress(remaining / totalSeconds);
  stopTick();
  tickId = setInterval(tick, 1000);
}

function pause() {
  running = false;
  els.btnPrimary.textContent = "继续";
  els.phaseLabel.textContent = "已暂停";
  stopTick();
}

els.modeBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    if (running) return;
    const mode = btn.dataset.mode;
    if (!mode || mode === currentMode) return;
    currentMode = mode;
    els.modeBtns.forEach((b) => {
      const active = b.dataset.mode === currentMode;
      b.classList.toggle("is-active", active);
      b.setAttribute("aria-selected", active ? "true" : "false");
    });
    applyBodyMode();
    resetTimerForMode();
  });
});

els.btnPrimary.addEventListener("click", () => {
  if (running) pause();
  else start();
});

els.btnReset.addEventListener("click", () => {
  settings = {
    focus: Math.min(120, Math.max(1, Number(els.durFocus.value) || 25)),
    short: Math.min(60, Math.max(1, Number(els.durShort.value) || 5)),
    long: Math.min(60, Math.max(1, Number(els.durLong.value) || 15)),
  };
  saveSettings(settings);
  syncDurationInputs();
  resetTimerForMode();
});

["durFocus", "durShort", "durLong"].forEach((id) => {
  document.getElementById(id).addEventListener("change", () => {
    settings = {
      focus: Math.min(120, Math.max(1, Number(els.durFocus.value) || 25)),
      short: Math.min(60, Math.max(1, Number(els.durShort.value) || 5)),
      long: Math.min(60, Math.max(1, Number(els.durLong.value) || 15)),
    };
    saveSettings(settings);
  });
});

els.alwaysOnTop.addEventListener("change", async () => {
  const on = els.alwaysOnTop.checked;
  if (window.pomodoro?.setAlwaysOnTop) {
    await window.pomodoro.setAlwaysOnTop(on);
  }
});

applyBodyMode();
syncDurationInputs();
resetTimerForMode();
updateStatsUI();

document.addEventListener("visibilitychange", () => {
  /* timer uses setInterval; no extra work */
});
