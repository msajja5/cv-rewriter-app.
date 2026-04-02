import re

with open("templates/index.html", "r") as f:
    content = f.read()

# Add overlay JS logic
overlay_js = """
    // Overlay State
    let overlayMode = "none"; // "pip", "popup", "inline", "none"
    let pipWin = null;
    let popupWin = null;
    let overlayFs = 26;

    const floatBtn = document.getElementById('float-btn');
    const inlineOverlay = document.getElementById('inline-overlay');
    const inlText = document.getElementById('inl-text');
    const inlQ = document.getElementById('inl-q');
    const inlBanner = document.getElementById('inl-banner');

    // PiP HTML Template
    function buildPipHTML() {
        return `
            <html>
            <head>
                <style>
                    body { background: #080a14; color: white; font-family: sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
                    .topbar { display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333; background: #111; }
                    .banner { text-align: center; font-weight: bold; padding: 5px; font-size: 14px; transition: background 0.2s; }
                    .banner.interviewer { background: #28a745; color: white; }
                    .banner.me { background: #6f42c1; color: white; }
                    .q-box { padding: 10px; font-size: 14px; color: #aaa; border-bottom: 1px solid #333; min-height: 40px; background: #1a1a24; }
                    .ans-box { flex: 1; overflow-y: auto; padding: 20px; font-size: ${overlayFs}px; line-height: 1.5; white-space: pre-wrap; }
                    .controls button { background: #333; color: white; border: none; padding: 5px 10px; margin: 0 2px; cursor: pointer; border-radius: 3px; }
                    .controls button:hover { background: #555; }
                    .spk-btn.active { border: 2px solid white; }
                </style>
            </head>
            <body>
                <div class="topbar">
                    <div><strong>AI Copilot</strong></div>
                    <div class="controls">
                        <button id="btn-int" class="spk-btn active" style="background: #28a745;" onclick="setSpk('interviewer')">🎤 Interviewer</button>
                        <button id="btn-me" class="spk-btn" style="background: #6f42c1;" onclick="setSpk('me')">🙋 Me</button>
                        <button onclick="changeFs(2)">A+</button>
                        <button onclick="changeFs(-2)">A-</button>
                    </div>
                </div>
                <div id="pip-banner" class="banner interviewer">Interviewer Speaking (Auto-Answer)</div>
                <div id="pip-q" class="q-box">Waiting for question...</div>
                <div id="pip-text" class="ans-box"></div>
                <script>
                    window.addEventListener("message", (e) => {
                        const d = e.data;
                        if (!d || d.type !== "ic-update") return;

                        if (d.q !== undefined) document.getElementById("pip-q").textContent = d.q;
                        if (d.text !== undefined) {
                            document.getElementById("pip-text").textContent = d.text;
                        }
                        if (d.fs) document.getElementById("pip-text").style.fontSize = d.fs + "px";
                        if (d.speaker) updateSpeakerUI(d.speaker);
                        if (d.scrollTop) {
                            document.getElementById("pip-text").scrollTop = 0;
                        }
                    });

                    function setSpk(who) {
                        window.opener.postMessage({type: "ic-speaker", speaker: who}, "*");
                    }
                    function changeFs(delta) {
                        window.opener.postMessage({type: "ic-fs", delta: delta}, "*");
                    }
                    function updateSpeakerUI(who) {
                        const banner = document.getElementById("pip-banner");
                        const btnInt = document.getElementById("btn-int");
                        const btnMe = document.getElementById("btn-me");
                        if (who === "interviewer") {
                            banner.className = "banner interviewer";
                            banner.textContent = "Interviewer Speaking (Auto-Answer)";
                            btnInt.classList.add("active");
                            btnMe.classList.remove("active");
                        } else {
                            banner.className = "banner me";
                            banner.textContent = "Me Speaking (Transcribing Only)";
                            btnMe.classList.add("active");
                            btnInt.classList.remove("active");
                        }
                    }
                </script>
            </body>
            </html>
        `;
    }

    async function openOverlay() {
        if (overlayMode !== "none") return closeOverlay();

        // Tier 1: Document PiP
        if ('documentPictureInPicture' in window && window === window.top) {
            try {
                pipWin = await window.documentPictureInPicture.requestWindow({
                    width: 500, height: 600
                });
                pipWin.document.write(buildPipHTML());
                pipWin.document.close();
                overlayMode = "pip";
                pipWin.addEventListener("pagehide", () => closeOverlay());
                return;
            } catch (e) {
                console.warn("PiP failed, trying popup", e);
            }
        }

        // Tier 2: Popup
        try {
            popupWin = window.open('', 'InterviewOverlay', 'width=500,height=600,left=1000,top=100,resizable=yes');
            if (popupWin) {
                popupWin.document.write(buildPipHTML());
                popupWin.document.close();
                overlayMode = "popup";
                return;
            }
        } catch(e) {
            console.warn("Popup failed, using inline", e);
        }

        // Tier 3: Inline
        inlineOverlay.style.display = "flex";
        overlayMode = "inline";
    }

    function closeOverlay() {
        if (pipWin) { pipWin.close(); pipWin = null; }
        if (popupWin) { popupWin.close(); popupWin = null; }
        inlineOverlay.style.display = "none";
        overlayMode = "none";
    }

    floatBtn.addEventListener('click', openOverlay);
    document.getElementById('inl-close-btn').addEventListener('click', closeOverlay);

    // Sync state to overlay
    function sendOverlayUpdate(scrollTop = false) {
        if (overlayMode === "none") return;

        const payload = {
            type: "ic-update",
            q: transcriptBox.value.trim(),
            text: aiScriptBox.innerText,
            fs: overlayFs,
            speaker: isInterviewerSpeaking ? "interviewer" : "me",
            scrollTop: scrollTop
        };

        if (overlayMode === "pip" && pipWin) pipWin.postMessage(payload, "*");
        if (overlayMode === "popup" && popupWin) popupWin.postMessage(payload, "*");
        if (overlayMode === "inline") {
            inlQ.textContent = payload.q;
            inlText.textContent = payload.text;
            inlText.style.fontSize = payload.fs + "px";
            updateInlineSpeakerUI(payload.speaker);
            if (scrollTop) inlText.parentElement.scrollTop = 0;
        }
    }

    function updateInlineSpeakerUI(who) {
        if (who === "interviewer") {
            inlBanner.style.background = "#28a745";
            inlBanner.textContent = "Interviewer Speaking (Auto-Answer)";
            document.getElementById('inl-spk-int').style.border = "2px solid white";
            document.getElementById('inl-spk-me').style.border = "none";
        } else {
            inlBanner.style.background = "#6f42c1";
            inlBanner.textContent = "Me Speaking (Transcribing Only)";
            document.getElementById('inl-spk-me').style.border = "2px solid white";
            document.getElementById('inl-spk-int').style.border = "none";
        }
    }

    // Listen for messages from PiP/Popup
    window.addEventListener("message", (e) => {
        const d = e.data;
        if (!d) return;
        if (d.type === "ic-speaker") {
            if ((d.speaker === "interviewer" && !isInterviewerSpeaking) ||
                (d.speaker === "me" && isInterviewerSpeaking)) {
                toggleSpeakerMode();
            }
        }
        if (d.type === "ic-fs") {
            overlayFs += d.delta;
            sendOverlayUpdate();
        }
    });

    document.getElementById('inl-spk-int').addEventListener('click', () => { if(!isInterviewerSpeaking) toggleSpeakerMode(); });
    document.getElementById('inl-spk-me').addEventListener('click', () => { if(isInterviewerSpeaking) toggleSpeakerMode(); });

    // Patch existing toggleSpeakerMode to notify overlay
    const origToggle = toggleSpeakerMode;
    toggleSpeakerMode = function() {
        origToggle();
        sendOverlayUpdate();
    };

    // Replace the spacebar event to toggle properly without preventing default if not needed
"""

content = content.replace("    // Compact Mode Toggles", overlay_js + "\n    // Compact Mode Toggles")

# Patch existing generate script to sync to overlay when receiving tokens
content = re.sub(
    r'aiScriptBox\.innerText = fullResponse;',
    r'aiScriptBox.innerText = fullResponse;\n                                    sendOverlayUpdate();',
    content
)

# And clear text sync
content = re.sub(
    r'aiScriptBox\.innerText = ""; // Clear for streaming',
    r'aiScriptBox.innerText = ""; // Clear for streaming\n        sendOverlayUpdate(true);',
    content
)


with open("templates/index.html", "w") as f:
    f.write(content)
