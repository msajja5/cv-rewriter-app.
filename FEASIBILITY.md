# Real-time Interview Assistant: Feasibility & Architecture Constraints

This document outlines the reality of capturing live meeting audio (Zoom, Teams, Google Meet) for real-time AI transcription from a standard web browser.

## Current State: Why Browser Web Speech API is not enough
The built-in browser Speech-to-Text (`webkitSpeechRecognition`) is convenient but inherently flawed for this use case:
1. **Audio Routing**: By default, it only listens to the OS default microphone. It cannot seamlessly listen to the speaker output (what the interviewer is saying) unless the user employs a virtual audio cable (e.g., VB-Cable, BlackHole) to route speaker output back into a virtual microphone.
2. **Accuracy & Latency**: Browser STT relies on the browser vendor's cloud services, which are often not tuned for fast, speaker-separated meeting transcription.

## Operating Modes

### Mode A: Mock Interview (User Mic Only) - ✅ **Fully Feasible Today**
- **How it works**: The user speaks into their mic, and the browser uses Web Speech API to transcribe it.
- **Use Case**: Practicing interviews alone. The AI plays the role of the interviewer or evaluates your answers.

### Mode B: Meeting Companion (Browser Tab Capture) - ⚠️ **Partially Feasible**
- **How it works**: If the interview is conducted in Google Meet or Teams *inside Chrome*, the user can use a Chrome Extension or `navigator.mediaDevices.getDisplayMedia({ video: true, audio: true })` to capture the tab's audio stream.
- **Constraints**:
  - Requires the user to actively select the correct tab to share.
  - Mixes both the interviewer's voice and the user's voice into a single audio track, making speaker diarization (knowing *who* said what) difficult for the AI without an advanced server-side STT model.
  - Cannot capture audio from native desktop apps (like the standalone Zoom or Teams clients).

### Mode C: Meeting Platform Integration (Meeting Bot) - ❌ **Not Feasible from a plain Web Page**
- **How it works**: To truly integrate with enterprise Zoom/Teams/Meet seamlessly, you must build a Meeting Bot (e.g., using Zoom Meeting SDK, Microsoft Graph Communications API, or a service like Recall.ai). The bot joins the meeting as a silent participant, receives raw separated audio streams, and streams them to your backend.
- **Constraints**:
  - Requires significant backend infrastructure.
  - Subject to strict enterprise consent policies (participants must agree to be recorded).
  - Many enterprise IT policies block unauthorized bots from joining calls.
  - **Cannot be built solely with frontend JavaScript.**

## Recommended Production Path
For a true production-grade "Live Manual Assist", the most reliable path without building a heavy Meeting Bot is:
1. **The Virtual Cable Method**: Instruct users to install VB-Audio Cable. Set the meeting app's output to the Virtual Cable, and the browser app's input to the Virtual Cable. This guarantees the browser hears the interviewer perfectly.
2. **Server-Side STT**: Stream the captured audio chunks to a low-latency STT model (like Groq Whisper API) to ensure high-accuracy transcription, replacing the browser's native API. (Stubbed in `stt_service.py` and `POST /stt`).
