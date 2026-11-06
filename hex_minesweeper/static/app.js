(function () {
  "use strict";

  const board = document.getElementById("board");
  const message = document.getElementById("message");
  const status = document.getElementById("game-status");
  const flagButton = document.getElementById("flag-mode");
  const baselineButton = document.getElementById("baseline-step");
  const baselineAutoButton = document.getElementById("baseline-auto");
  const modelPlaybackButton = document.getElementById("model-playback");
  const modelPlaybackNote = document.getElementById("model-playback-note");
  const boardSizeSelect = document.getElementById("board-size");
  const modelRecordingMode = new URLSearchParams(window.location.search).get("recording") === "model";

  let state = null;
  let flagMode = false;
  let busy = false;
  let autoMode = null;
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
    const height = cellWidth * 1.12;
    const radius = state ? state.observation.radius : 3;
    const stepY = height * 0.75;
    board.style.height = Math.max(260, 2 * radius * stepY + height + 20) + "px";
    board.style.setProperty("--hex-width", cellWidth + "px");
    board.style.setProperty("--hex-height", height + "px");
    board.style.setProperty("--hex-step-x", (cellWidth * 0.96) + "px");
    board.style.setProperty("--hex-step-y", (height * 0.75) + "px");
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
    const stepX = cellWidth * 0.96;
    const stepY = cellWidth * 1.12 * 0.75;
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
      if (cell.state === "revealed") {
        tile.textContent = cell.number > 0 ? String(cell.number) : "";
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", " + cell.number + " adjacent mines");
      } else if (cell.state === "flagged") {
        tile.innerHTML = '<span class="flag-mark" aria-hidden="true">⚑</span>';
        tile.setAttribute("aria-label", "Hex " + cell.q + "," + cell.r + ", flagged");
      } else if (cell.mine === true) {
        tile.textContent = "✹";
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
    baselineButton.hidden = modelRecordingMode;
    baselineButton.disabled = busy || ended || modelRecordingMode;
    baselineAutoButton.hidden = modelRecordingMode;
    baselineAutoButton.disabled = busy || ended || modelRecordingMode;
    modelPlaybackButton.hidden = !modelRecordingMode;
    modelPlaybackButton.disabled = busy || ended || !modelRecordingMode;
    modelPlaybackButton.textContent = autoMode === "model" ? "■ Stop live model playback" : "▶ Start live model playback";
    modelPlaybackNote.hidden = !modelRecordingMode;
    document.getElementById("new-game").disabled = busy;
    boardSizeSelect.disabled = busy;
    flagButton.disabled = busy || ended;
    flagButton.setAttribute("aria-pressed", String(flagMode));
    flagButton.innerHTML = flagMode ? "<span aria-hidden='true'>⚑</span> Reveal mode" : "<span aria-hidden='true'>⚑</span> Flag mode";
    baselineAutoButton.textContent = autoMode ? "■ Stop game playing agent" : "▶ Run game playing agent";
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
        if (next.outcome.result === "win") say("All safe hexes cleared. You win.", "success");
        else if (next.outcome.result === "loss") say("A mine was revealed. The board is shown so you can review it.", "error");
        else say("Episode ended: " + next.outcome.reason +
          (next.outcome.detail ? ": " + next.outcome.detail : "."), "error");
      } else if (next.event && next.event.action) {
        const move = next.event.action;
        const actor = next.trace.length ? next.trace[next.trace.length - 1].actor : "";
        const who = actor === "baseline" ? "Game playing agent" :
          actor === "model" ? "Model agent" : actor === "human" ? "You" : "Player";
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
    requestJson("/api/reset", {
      size: selectedSize,
      model_playback_enabled: modelRecordingMode
    })
      .then(function (next) {
        render(next);
        say("New board ready. Your first reveal is safe.");
      })
      .catch(function (error) { say(error.message, "error"); })
      .finally(function () { setBusy(false); });
  }

  function autoStep() {
    if (!autoMode || !state || state.outcome.terminal || busy) return;
    const isModel = autoMode === "model";
    const route = isModel ? "/api/model/step" : "/api/baseline/step";
    const label = isModel ? "Model agent is choosing a move…" : "Game playing agent is finding a move…";
    runAction(route, { session: state.session }, label).then(function () {
      if (autoMode && state && state.outcome.terminal) stopAuto();
    });
  }

  function toggleAuto() {
    if (autoMode) {
      stopAuto();
      say("Auto-play stopped.");
      return;
    }
    autoMode = "baseline";
    updateButtons();
    autoStep();
  }

  function toggleModelPlayback() {
    if (!modelRecordingMode || !state || busy || state.outcome.terminal) return;
    if (autoMode === "model") {
      stopAuto();
      say("Live model playback stopped.");
      return;
    }
    stopAuto();
    autoMode = "model";
    updateButtons();
    autoStep();
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
  baselineAutoButton.addEventListener("click", toggleAuto);
  modelPlaybackButton.addEventListener("click", toggleModelPlayback);
  window.addEventListener("resize", function () { if (state) render(state); });

  if (modelRecordingMode) {
    document.getElementById("agent-description-title").textContent = "Live model player.";
    document.getElementById("agent-description").textContent =
      "It receives the public board and legal actions, then submits its own moves through the game interface.";
  }

  requestJson("/api/reset", { model_playback_enabled: modelRecordingMode })
    .then(function (initial) {
      render(initial);
      say("Choose a hex to reveal it. Right-click or use Flag mode to place a flag.");
    })
    .catch(function (error) { say(error.message, "error"); });
})();
