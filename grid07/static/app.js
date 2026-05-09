async function postJson(url, payload) {
  const response = await fetch(url, {
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
  target.textContent = JSON.stringify(value, null, 2);
}

function renderError(targetId, error) {
  const target = document.getElementById(targetId);
  target.textContent = JSON.stringify({ error: error.message }, null, 2);
}

async function handleRoute() {
  const post = document.getElementById("route-post").value.trim();
  try {
    const data = await postJson("/route", { post });
    renderJson("route-output", data);
  } catch (error) {
    renderError("route-output", error);
  }
}

async function handleGeneratePost() {
  const botId = document.getElementById("post-bot").value;
  try {
    const data = await postJson("/generate-post", { bot_id: botId });
    renderJson("post-output", data);
  } catch (error) {
    renderError("post-output", error);
  }
}

async function handleReply() {
  const message = document.getElementById("reply-message").value.trim();
  try {
    const data = await postJson("/reply", { bot_id: "bot_a", message });
    renderJson("reply-output", data);
  } catch (error) {
    renderError("reply-output", error);
  }
}

document.getElementById("route-button").addEventListener("click", handleRoute);
document.getElementById("post-button").addEventListener("click", handleGeneratePost);
document.getElementById("reply-button").addEventListener("click", handleReply);

renderJson("route-output", {
  hint: "Click 'Route Post' to run persona matching.",
});
renderJson("post-output", {
  hint: "Click 'Generate Post' to run the content engine.",
});
renderJson("reply-output", {
  hint: "Click 'Generate Defended Reply' to test prompt-injection defense.",
});
