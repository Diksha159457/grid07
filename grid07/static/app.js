const runtimeBadge = document.getElementById("runtime-badge");
const runtimeMessage = document.getElementById("runtime-message");

function apiBase() {
  return "";
}

function isPreviewMode() {
  return window.location.protocol === "file:";
}

function setRuntimeMode() {
  if (isPreviewMode()) {
    runtimeBadge.textContent = "Preview Mode";
    runtimeBadge.classList.add("preview");
    runtimeMessage.textContent =
      "You are viewing the static file directly. The design is fully previewable here, but interactive API calls require the live local or Render service.";
  }
}

async function postJson(url, payload) {
  if (isPreviewMode()) {
    throw new Error("Interactive requests are disabled in file preview mode. Open the hosted or local app server to run the live demos.");
  }

  const response = await fetch(`${apiBase()}${url}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function renderJson(targetId, value) {
  const target = document.getElementById(targetId);
  target.classList.remove("loading");
  target.textContent = JSON.stringify(value, null, 2);
}

function renderError(targetId, error) {
  const target = document.getElementById(targetId);
  target.classList.remove("loading");
  target.textContent = JSON.stringify({ error: error.message }, null, 2);
}

function renderLoading(targetId, message) {
  const target = document.getElementById(targetId);
  target.classList.add("loading");
  target.textContent = message;
}

async function runAction({ targetId, buttonId, message, request }) {
  const button = document.getElementById(buttonId);
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = "Running...";
  renderLoading(targetId, message);

  try {
    const data = await request();
    renderJson(targetId, data);
  } catch (error) {
    renderError(targetId, error);
  } finally {
    button.disabled = false;
    button.textContent = originalLabel;
  }
}

async function handleRoute() {
  const post = document.getElementById("route-post").value.trim();
  await runAction({
    targetId: "route-output",
    buttonId: "route-button",
    message: "Scoring the post against the persona router...",
    request: () => postJson("/route", { post }),
  });
}

async function handleGeneratePost() {
  const botId = document.getElementById("post-bot").value;
  await runAction({
    targetId: "post-output",
    buttonId: "post-button",
    message: "Running LangGraph-style orchestration and drafting structured JSON...",
    request: () => postJson("/generate-post", { bot_id: botId }),
  });
}

async function handleReply() {
  const message = document.getElementById("reply-message").value.trim();
  await runAction({
    targetId: "reply-output",
    buttonId: "reply-button",
    message: "Constructing thread-aware defense prompt and generating a reply...",
    request: () => postJson("/reply", { bot_id: "bot_a", message }),
  });
}

function wireFillButtons() {
  document.querySelectorAll("[data-fill-target]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.getAttribute("data-fill-target");
      const targetValue = button.getAttribute("data-fill-value");
      const target = document.getElementById(targetId);
      if (target) {
        target.value = targetValue;
      }
    });
  });
}

document.getElementById("route-button").addEventListener("click", handleRoute);
document.getElementById("post-button").addEventListener("click", handleGeneratePost);
document.getElementById("reply-button").addEventListener("click", handleReply);

wireFillButtons();
setRuntimeMode();

renderJson("route-output", {
  phase: "Phase 1",
  hint: "Run the router to see which persona cares about the post.",
});

renderJson("post-output", {
  phase: "Phase 2",
  hint: "Generate a structured JSON post from the LangGraph workflow.",
});

renderJson("reply-output", {
  phase: "Phase 3",
  hint: "Test the defense engine with a hostile or injection-style reply.",
});
