import re

with open("templates/index.html", "r") as f:
    content = f.read()

# Since Web Speech API cannot directly listen to MediaStream objects (it only listens to the default OS mic),
# We need to add an explanation to the user or change the approach.
# Actually, we can use MediaRecorder to capture the `getDisplayMedia` audio stream,
# but we'd need to send it to a backend STT which isn't fully implemented in `main.py` yet.
# Let's add a note in the UI that explains Web Speech limitation when using getDisplayMedia
# OR we can keep the getDisplayMedia logic, and tell the user they still need to route it,
# or we use a third party JS library. Let's add a UI note.

new_html = content.replace(
    '<span id="stt-status">Browser Web Speech API (Paused for AI Response)</span>',
    '<span id="stt-status">Browser Web Speech API (Paused for AI Response)</span><br><small style="color:#6c757d; font-size: 0.8em;">Note: Continuous Listen uses Screen Share to capture Tab Audio, but Web Speech API relies on the default OS Microphone. For true meeting capture, you must either route audio (e.g. VB-Cable) or use a backend STT.</small>'
)

with open("templates/index.html", "w") as f:
    f.write(new_html)
