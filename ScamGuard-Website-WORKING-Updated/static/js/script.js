// =========================================================
// ScamGuard frontend JavaScript
// =========================================================

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function renderResult(box, data) {

    const isSafe = data.result === "SAFE";

    box.style.display = "block";
    box.style.background = isSafe ? "#ecfdf3" : "#fff7ed";
    box.style.color = "#172033";

    let reasonsHtml = "";

    data.reasons.forEach(reason => {
        reasonsHtml += `<li>${escapeHtml(reason)}</li>`;
    });

    let wordsHtml = "";

    if (data.matched_words && data.matched_words.length > 0) {
        wordsHtml = `
            <p><strong>Detected indicators:</strong></p>
            <div class="indicator-list">
                ${data.matched_words.map(
                    word => `<span class="indicator">${escapeHtml(word)}</span>`
                ).join("")}
            </div>
        `;
    }

    box.innerHTML = `
        <div class="result-title">
            ${escapeHtml(data.result)}
        </div>

        <div class="result-score">
            Risk Score: ${escapeHtml(data.risk_score)}/100
            &nbsp; | &nbsp;
            Risk Level: ${escapeHtml(data.risk_level)}
        </div>

        <strong>Why was it flagged?</strong>

        <ul>
            ${reasonsHtml}
        </ul>

        ${wordsHtml}

        <div class="recommendation">
            <strong>Recommended Action</strong>
            <p>${escapeHtml(data.recommendation)}</p>
        </div>
    `;
}


async function quickScan(inputId, resultId) {

    const input = document.getElementById(inputId);
    const box = document.getElementById(resultId);

    if (!input || !box) {
        return;
    }

    const text = input.value.trim();

    if (!text) {
        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = "<strong>Please enter some content.</strong>";
        return;
    }

    box.style.display = "block";
    box.style.background = "#eef2ff";
    box.innerHTML = "🔍 Analyzing...";

    try {

        const response = await fetch("/api/check-text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                input_type: "message",
                text: text
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || "Unable to analyze.");
        }

        renderResult(box, result.data);

    } catch (error) {

        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = `<strong>${escapeHtml(error.message)}</strong>`;
    }
}


function switchScanner(type, button) {

    const messagePanel = document.getElementById("messagePanel");
    const urlPanel = document.getElementById("urlPanel");

    document.querySelectorAll(".scan-tab")
        .forEach(tab => tab.classList.remove("active"));

    button.classList.add("active");

    if (type === "url") {
        messagePanel.style.display = "none";
        urlPanel.style.display = "block";
    } else {
        messagePanel.style.display = "block";
        urlPanel.style.display = "none";
    }
}


async function scanMessagePage() {

    const text = document.getElementById("scanMessage").value.trim();
    const box = document.getElementById("scanResult");

    if (!text) {
        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = "<strong>Please enter a message.</strong>";
        return;
    }

    box.style.display = "block";
    box.style.background = "#eef2ff";
    box.innerHTML = "🔍 Analyzing message...";

    try {

        const response = await fetch("/api/check-text", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                input_type: "message",
                text: text
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || "Unable to analyze.");
        }

        renderResult(box, result.data);

    } catch (error) {

        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = `<strong>${escapeHtml(error.message)}</strong>`;
    }
}


async function scanUrlPage() {

    const url = document.getElementById("scanUrl").value.trim();
    const box = document.getElementById("scanResult");

    if (!url) {
        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = "<strong>Please enter a URL.</strong>";
        return;
    }

    box.style.display = "block";
    box.style.background = "#eef2ff";
    box.innerHTML = "🔗 Analyzing URL...";

    try {

        const response = await fetch("/api/check-url", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: url
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || "Unable to analyze URL.");
        }

        renderResult(box, result.data);

    } catch (error) {

        box.style.display = "block";
        box.style.background = "#fee2e2";
        box.innerHTML = `<strong>${escapeHtml(error.message)}</strong>`;
    }
}
