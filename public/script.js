
const $ = (id) => document.getElementById(id);

let videoId = null;
let history = [];


function setStatus(text, isError = false) {
  $("status").textContent = text;
  $("status").className = isError ? "error" : "";
}


/* ================= RENDER SUMMARY ================= */

function render(text) {

  const esc = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const lines = esc.split("\n");

  let html = "";
  let inList = false;

  for (const line of lines) {

    const bullet = line.match(/^\s*[-*]\s+(.*)/);

    if (bullet && !inList) {
      html += "<ul>";
      inList = true;
    }

    if (!bullet && inList) {
      html += "</ul>";
      inList = false;
    }

    const body = (bullet ? bullet[1] : line)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    if (bullet) {
      html += `<li>${body}</li>`;
    } else if (body.trim()) {
      html += `<p>${body}</p>`;
    }
  }

  if (inList) {
    html += "</ul>";
  }

  return html;
}


/* ================= API ================= */

async function post(path, payload) {

  const res = await fetch(path, {
    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify(payload)
  });


  /*
   * Don't blindly call res.json().
   * If Flask returns HTML because of an error,
   * this prevents:
   *
   * Unexpected end of JSON input
   */

  const contentType = res.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {

    const text = await res.text();

    throw new Error(
      `Server returned an unexpected response (${res.status}). ` +
      `${text.slice(0, 150)}`
    );
  }


  const data = await res.json();


  if (!res.ok) {
    throw new Error(
      data.error || "Something went wrong."
    );
  }


  return data;
}


/* ================= CHAT ================= */

function addMsg(role, text) {

  const div = document.createElement("div");

  div.className = `msg ${role}`;

  div.textContent = text;

  $("log").appendChild(div);

  $("log").scrollTop = $("log").scrollHeight;

  return div;
}


/* ================= SUMMARIZE ================= */

$("go").addEventListener("click", async () => {

  const url = $("url").value.trim();


  if (!url) {
    setStatus("Paste a YouTube link first.", true);
    return;
  }


  $("go").disabled = true;

  setStatus(
    "Reading the video transcript and generating your summary..."
  );


  try {

    const data = await post(
      "/api/summarize",
      {
        url,
        language: $("lang").value
      }
    );


    videoId = data.video_id;

    history = [];


    $("log").innerHTML = "";


    $("player").src =
      `https://www.youtube.com/embed/${videoId}`;


    $("summary").innerHTML =
      render(data.summary);


    $("result").hidden = false;


    setStatus("");


    /*
     * Smoothly move the user to the results.
     */

    $("result").scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  }


  catch (e) {

    console.error(e);

    setStatus(e.message, true);

  }


  finally {

    $("go").disabled = false;

  }

});


/* ================= ASK QUESTION ================= */

async function sendQuestion() {

  const question = $("q").value.trim();


  if (!question || !videoId) {
    return;
  }


  $("q").value = "";

  $("send").disabled = true;


  addMsg(
    "user",
    question
  );


  const pending = addMsg(
    "bot",
    "Thinking..."
  );


  try {

    const data = await post(
      "/api/chat",
      {
        video_id: videoId,
        question,
        history,
        language: $("lang").value
      }
    );


    pending.textContent =
      data.answer;


    history.push(
      {
        role: "user",
        content: question
      },
      {
        role: "assistant",
        content: data.answer
      }
    );

  }


  catch (e) {

    pending.textContent =
      e.message;

  }


  finally {

    $("send").disabled = false;

    $("q").focus();

  }

}


/* ================= EVENTS ================= */

$("send").addEventListener(
  "click",
  sendQuestion
);


$("q").addEventListener(
  "keydown",
  (e) => {

    if (e.key === "Enter") {
      sendQuestion();
    }

  }
);


$("url").addEventListener(
  "keydown",
  (e) => {

    if (e.key === "Enter") {
      $("go").click();
    }

  }
);


