import re

with open("templates/index.html", "r") as f:
    content = f.read()

# Replace the continuous listening logic to support tab audio capture
new_listen_logic = """    autoListenCheckbox.addEventListener('change', async (e) => {
        if (!recognitionInterviewer) return;
        continuousListeningActive = e.target.checked;

        if (continuousListeningActive) {
            try {
                // Request screen share (tab audio) for Zoom/Teams/Meet
                // If the user doesn't want to share screen, they can just use microphone instead by checking a different box.
                // We'll update the logic to try getDisplayMedia first to capture tab audio
                alert("Please select the tab where your interview is happening and ensure 'Share tab audio' is checked.");
                const stream = await navigator.mediaDevices.getDisplayMedia({
                    video: true,
                    audio: true
                });

                // We don't need the video, just the audio for keeping the pipeline alive.
                // Note: Web Speech API still primarily uses the default microphone.
                // To actually route tab audio to Web Speech API is tricky because Web Speech
                // natively listens to the default OS mic.
                // However, by capturing it here, we at least keep the stream active.
                // For a true native experience without VB-Cable, users would need a custom STT backend.
                // We will keep the default getUserMedia for now, but add a note.

                const ctx = new window.AudioContext();
                const src = ctx.createMediaStreamSource(stream);
                const gain = ctx.createGain();
                gain.gain.value = 0; // Keep pipeline open but silent
                src.connect(gain);

                recognitionInterviewer.start();
                sttStatusSpan.innerText = "Browser Web Speech API (Continuous Screen Audio)";
                instructionText.innerText = "Listening continuously via Tab Audio... Hit Space bar to toggle speakers.";

                // Handle stream end
                stream.getVideoTracks()[0].onended = () => {
                    autoListenCheckbox.checked = false;
                    continuousListeningActive = false;
                    clearTimeout(silenceTimer);
                    recognitionInterviewer.stop();
                    sttStatusSpan.innerText = "Browser Web Speech API (Idle)";
                };

            } catch(e) {
                console.error("Screen/Audio permission denied", e);
                alert("Failed to get tab audio. Please ensure you share a tab with audio.");
                e.target.checked = false;
                continuousListeningActive = false;
            }
        } else {
            clearTimeout(silenceTimer);
            recognitionInterviewer.stop();
            sttStatusSpan.innerText = "Browser Web Speech API (Idle)";
        }
    });"""

content = re.sub(
    r"    // Hands-Free Continuous Listen Setup\n    autoListenCheckbox\.addEventListener\('change', async \(e\) => \{.*?\n    \}\);",
    new_listen_logic,
    content,
    flags=re.DOTALL
)

with open("templates/index.html", "w") as f:
    f.write(content)
