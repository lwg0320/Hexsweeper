(function () {
  "use strict";

  const board = document.getElementById("board");
  const message = document.getElementById("message");
  const status = document.getElementById("game-status");
  const flagButton = document.getElementById("flag-mode");
  const baselineButton = document.getElementById("baseline-step");
  const baselineAutoButton = document.getElementById("baseline-auto");
  const modelStepButton = document.getElementById("model-step");
  const modelAutoButton = document.getElementById("model-auto");
  const modelApiNote = document.getElementById("model-api-note");
  const boardSizeSelect = document.getElementById("board-size");

  let state = null;
  let flagMode = false;
  let busy = false;
  let autoMode = null;
  let modelKeyConfigured = false;
  let modelName = "Claude";
  let modelConsentGranted = false;
  let modelSessionEnabled = false;
  let modelEnabling = false;
  let cellWidth = 48;

  function say(text, kind) {
    message.textContent = text;
    message.className = "message" + (kind ? " is-" + kind : "");
  }

  function requestJson(path, data) {
    const options = data === undefined ? {} : {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    };
    return fetch(path, options).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (payload) {
        if (!response.ok) {
          throw new Error(payload.error || "Request failed (" + response.status + ").");
        }
        return payload;
      });
    });
  }

  function updateGeometry() {
    const width = board.getBoundingClientRect().width || 500;
    cellWidth = Math.max(31, Math.min(48, (width - 22) / 9.5));
    const height = cellWidth * 2 / Math.sqrt(3);
    const radius = state ? state.observation.radius : 3;
    const stepY = height * 0.75;
    board.style.height = Math.max(260, 2 * radius * stepY + height + 20) + "px";
    board.style.setProperty("--hex-width", cellWidth + "px");
    board.style.setProperty("--hex-height", height + "px");
    board.style.setProperty("--hex-step-x", cellWidth + "px");
    board.style.setProperty("--hex-step-y", stepY + "px");
  }

  function render(next) {
    state = next;
    if (!state) return;
    updateGeometry();
    const obs = state.observation;
    const sizeName = state.board_size.charAt(0).toUpperCase() + state.board_size.slice(1);
    document.getElementById("board-caption").textContent = sizeName + " · " + obs.cells.length +
      " cells · " + obs.mine_count + " mines · radius " + obs.radius;
    if (!busy && state.board_size !== "custom") boardSizeSelect.value = state.board_size;
    document.getElementById("mine-count").textContent = String(obs.mine_count).padStart(2, "0");
    document.getElementById("revealed-count").textContent = String(obs.revealed_safe).padStart(2, "0");
    document.getElementById("flag-count").textContent = String(obs.flag_count).padStart(2, "0");
    const end = state.outcome;
    if (!end.terminal) {
      status.textContent = "In play";
      status.style.color = "";
    } else if (end.result === "win") {
      status.textContent = "Cleared";
      status.style.color = "var(--green)";
    } else if (end.result === "loss") {
      status.textContent = "Mine hit";
      status.style.color = "var(--red)";
    } else {
      status.textContent = end.reason || "Ended";
      status.style.color = "var(--red)";
    }

    board.replaceChildren();
    const boardWidth = board.getBoundingClientRect().width || 500;
    const boardHeight = board.getBoundingClientRect().height || 260;
    const stepX = cellWidth;
    const stepY = cellWidth * 2 / Math.sqrt(3) * 0.75;
    obs.cells.forEach(function (cell) {
      const tile = document.createElement("button");
      const classes = ["hex-cell"];
      if (cell.state === "revealed") classes.push("is-revealed", "number-" + cell.number);
      if (cell.state === "flagged") classes.push("is-flagged");
      if (cell.mine === true) classes.push("is-mine");
      if (cell.mine === true && end.reason === "mine_revealed" &&
          end.detail === "mine at " + cell.q + "," + cell.r) {
        classes.push("is-exploded");
      }
      tile.className = classes.join(" ");
      tile.type = "button";
      tile.setAttribute("role", "gridcell");
      tile.dataset.q = String(cell.q);
      tile.dataset.r = String(cell.r);
      tile.style.left = (boardWidth / 2 + stepX * (cell.q + cell.r / 2)) + "px";
      tile.style.top = (boardHeight / 2 + stepY * cell.r) + "px";
      tile.disabled = busy || state.outcome.terminal;
      const content = document.createElement("span");
      content.className = "hex-content";
      tile.appendChild(content);
      if (cell.state === "revealed") {
        content.textContent = cell.number > 0 ? String(cell.number) : "";
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", " + cell.number + " adjacent mines");
      } else if (cell.state === "flagged") {
        content.innerHTML = '<span class="flag-mark" aria-hidden="true">⚑</span>';
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", flagged");
      } else if (cell.mine === true) {
        content.textContent = "✹";
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", mine");
      } else {
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", hidden");
      }
      tile.addEventListener("click", onCellClick);
      tile.addEventListener("contextmenu", onCellContextMenu);
      board.appendChild(tile);
    });
    updateButtons();
  }

  function updateButtons() {
    const ended = !state || state.outcome.terminal;
    baselineButton.disabled = busy || ended || Boolean(autoMode);
    baselineAutoButton.disabled = busy || ended;
    modelStepButton.disabled = busy || ended || !modelKeyConfigured || Boolean(autoMode) || modelEnabling;
    modelAutoButton.disabled = busy || ended || !modelKeyConfigured || modelEnabling;
    modelAutoButton.textContent = autoMode === "model" ? "■ Stop Claude API agent" : "▶ Run Claude API agent";
    document.getElementById("new-game").disabled = busy || modelEnabling;
    boardSizeSelect.disabled = busy || modelEnabling;
    flagButton.disabled = busy || ended;
    flagButton.setAttribute("aria-pressed", String(flagMode));
    flagButton.innerHTML = flagMode ? "<span aria-hidden='true'>⚑</span> Reveal mode" : "<span aria-hidden='true'>⚑</span> Flag mode";
    baselineAutoButton.textContent = autoMode === "baseline" ? "■ Stop game playing agent" : "▶ Run game playing agent";
  }

  function setBusy(value) {
    busy = value;
    if (state) render(state);
    else updateButtons();
  }

  function runAction(path, body, successText) {
    if (busy || !state || state.outcome.terminal) return Promise.resolve();
    setBusy(true);
    say(successText || "The player is choosing a move…");
    return requestJson(path, body).then(function (next) {
      render(next);
      if (next.outcome.terminal) {
        const usedFallback = next.trace.length &&
          next.trace[next.trace.length - 1].actor === "random_fallback";
        const fallbackNote = usedFallback ? "Random fallback move applied. " : "";
        if (next.outcome.result === "win") say(fallbackNote + "All safe hexes cleared. You win.", "success");
        else if (next.outcome.result === "loss") say(fallbackNote + "A mine was revealed. The board is shown so you can review it.", "error");
        else say(fallbackNote + "Episode ended: " + next.outcome.reason +
          (next.outcome.detail ? ": " + next.outcome.detail : "."), "error");
      } else if (next.event && next.event.action) {
        const move = next.event.action;
        const actor = next.trace.length ? next.trace[next.trace.length - 1].actor : "";
        const who = actor === "baseline" ? "Game playing agent" :
          actor === "model" ? "Claude API agent" :
          actor === "random_fallback" ? "Random fallback" :
          actor === "human" ? "You" : "Player";
        const verb = move.type === "flag" ? "flagged" : "revealed";
        say(who + " " + verb + " hex " + move.q + "," + move.r + ".");
      } else if (next.outcome.detail) {
        say(next.outcome.detail, "error");
      }
    }).catch(function (error) {
      if (autoMode === "model") stopAuto();
      say(error.message, "error");
    }).finally(function () {
      setBusy(false);
      if (autoMode && state && !state.outcome.terminal) {
        window.setTimeout(autoStep, 420);
      } else if (state && state.outcome.terminal) {
        autoMode = null;
        updateButtons();
      }
    });
  }

  function doMove(action) {
    return runAction("/api/step", { session: state.session, action: action });
  }

  function onCellClick(event) {
    const tile = event.currentTarget;
    const q = Number(tile.dataset.q);
    const r = Number(tile.dataset.r);
    const type = flagMode ? "flag" : "reveal";
    doMove({ type: type, q: q, r: r });
  }

  function onCellContextMenu(event) {
    event.preventDefault();
    if (!state || busy || state.outcome.terminal) return;
    const tile = event.currentTarget;
    doMove({ type: "flag", q: Number(tile.dataset.q), r: Number(tile.dataset.r) });
  }

  function newGame() {
    if (busy) return;
    const selectedSize = boardSizeSelect.value;
    stopAuto();
    setBusy(true);
    say("Starting " + selectedSize + " board…");
    requestJson("/api/reset", { size: selectedSize })
      .then(function (next) {
        render(next);
        modelSessionEnabled = false;
        modelConsentGranted = false;
        say("New board ready. Your first reveal is safe.");
      })
      .catch(function (error) { say(error.message, "error"); })
      .finally(function () { setBusy(false); });
  }

  function autoStep() {
    if (!autoMode || !state || state.outcome.terminal || busy) return;
    const isModel = autoMode === "model";
    const route = isModel ? "/api/model/step" : "/api/baseline/step";
    const label = isModel ? "Claude API agent is choosing a move…" : "Game playing agent is finding a move…";
    runAction(route, { session: state.session }, label).then(function () {
      if (autoMode && state && state.outcome.terminal) stopAuto();
    });
  }

  function toggleAuto(mode) {
    if (autoMode === mode) {
      stopAuto();
      say("Auto-play stopped.");
      return;
    }
    if (mode === "model" && !confirmModelUse()) return;
    stopAuto();
    autoMode = mode;
    updateButtons();
    autoStep();
  }

  function confirmModelUse() {
    if (!modelKeyConfigured) {
      say("Add ANTHROPIC_API_KEY to the local .env file and restart the server.", "error");
      return false;
    }
    if (modelConsentGranted) return true;
    modelConsentGranted = window.confirm(
      "Run the Claude API agent? Each decision usually sends one request; an illegal move may be retried once. " +
      "Requests may incur charges, and full auto-play is capped at 80 calls. Your API key stays on this server."
    );
    if (!modelConsentGranted) say("Claude API agent not started; no API request was sent.");
    return modelConsentGranted;
  }

  function enableModelForSession() {
    if (modelSessionEnabled) return Promise.resolve();
    modelEnabling = true;
    updateButtons();
    say("Enabling the Claude API agent for this game…");
    return requestJson("/api/model/enable", { session: state.session })
      .then(function (result) {
        modelSessionEnabled = Boolean(result.enabled);
        if (!modelSessionEnabled) throw new Error("Could not enable the Claude API agent for this game.");
      })
      .finally(function () {
        modelEnabling = false;
        updateButtons();
      });
  }

  function stopAuto() {
    autoMode = null;
    updateButtons();
  }

  document.getElementById("new-game").addEventListener("click", newGame);
  boardSizeSelect.addEventListener("change", newGame);
  flagButton.addEventListener("click", function () {
    flagMode = !flagMode;
    updateButtons();
  });
  baselineButton.addEventListener("click", function () {
    runAction("/api/baseline/step", { session: state.session }, "Game playing agent is finding a move…");
  });
  modelStepButton.addEventListener("click", function () {
    if (!confirmModelUse()) return;
    enableModelForSession()
      .then(function () {
        runAction("/api/model/step", { session: state.session }, "Claude API agent is choosing a move…");
      })
      .catch(function (error) { say(error.message, "error"); });
  });
  baselineAutoButton.addEventListener("click", function () { toggleAuto("baseline"); });
  modelAutoButton.addEventListener("click", function () {
    if (autoMode === "model") {
      toggleAuto("model");
      return;
    }
    if (!confirmModelUse()) return;
    enableModelForSession()
      .then(function () {
        stopAuto();
        autoMode = "model";
        updateButtons();
        autoStep();
      })
      .catch(function (error) { say(error.message, "error"); });
  });
  window.addEventListener("resize", function () { if (state) render(state); });

  requestJson("/api/status")
    .then(function (apiStatus) {
      modelKeyConfigured = Boolean(apiStatus.model_key_configured);
      modelName = apiStatus.model || "Claude";
      modelApiNote.textContent = modelKeyConfigured
        ? modelName + " is ready. A move normally uses one API request; an illegal selection may trigger one retry. Full auto-play is capped at 80 calls; requests may incur charges."
        : "No Claude API key found. Please clone the project, copy .env.example to .env, add your key as ANTHROPIC_API_KEY, and restart the server.";
      updateButtons();
    })
    .catch(function () {
      modelApiNote.textContent = "Could not read Claude API setup status. Restart the local game server and reload this page.";
    });

  requestJson("/api/reset", { size: boardSizeSelect.value })
    .then(function (initial) {
      render(initial);
      say("Choose a hex to reveal it. Right-click or use Flag mode to place a flag.");
    })
    .catch(function (error) { say(error.message, "error"); });
})();
