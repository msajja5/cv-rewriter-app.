import re

with open("templates/index.html", "r") as f:
    content = f.read()

# Replace Toggle Compact Overlay button with Float Overlay button
content = re.sub(
    r'<button id="toggle-compact-btn".*?</button>',
    r'<button id="float-btn" style="width: auto; position: absolute; top: 10px; right: 10px; background: #00c9a7; font-size: 14px; padding: 5px 10px; color: black; font-weight: bold; border-radius: 5px; cursor: pointer;">⧉ Float Overlay</button>',
    content
)

# Remove the text "Toggle "Compact Overlay Mode" using the button in the top right to reduce clutter."
content = re.sub(
    r'Toggle "Compact Overlay Mode" using the button in the top right to reduce clutter.',
    r'Click "⧉ Float Overlay" to open a separate panel that stays on top of Zoom/Teams.',
    content
)

# Remove exit compact button
content = re.sub(
    r'<button id="exit-compact-btn".*?</button>',
    r'',
    content
)


# Add inline overlay HTML
inline_overlay_html = """
<!-- Inline Overlay Fallback -->
<div id="inline-overlay" style="display: none; position: fixed; right: 0; top: 0; bottom: 0; width: 420px; background: rgba(8, 10, 20, 0.96); z-index: 9999; border-left: 2px solid #00c9a7; flex-direction: column; color: white;">
    <div style="display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333;">
        <div><strong>AI Copilot</strong></div>
        <div>
            <button class="inl-spk-btn" id="inl-spk-int" style="background: #28a745; color: white; border: none; padding: 5px; margin-right: 5px; cursor: pointer;">🎤 Interviewer</button>
            <button class="inl-spk-btn" id="inl-spk-me" style="background: #6f42c1; color: white; border: none; padding: 5px; cursor: pointer;">🙋 Me</button>
        </div>
        <div>
            <button id="inl-close-btn" style="background: transparent; color: white; border: none; font-size: 16px; cursor: pointer;">✕</button>
        </div>
    </div>
    <div id="inl-banner" style="background: #28a745; text-align: center; font-weight: bold; padding: 5px; font-size: 12px;">Interviewer Speaking</div>
    <div style="padding: 10px; font-size: 12px; color: #aaa; border-bottom: 1px solid #333; min-height: 40px;" id="inl-q">Waiting for question...</div>
    <div id="inl-text-container" style="flex: 1; overflow-y: auto; padding: 15px;">
        <div id="inl-text" style="font-size: 26px; line-height: 1.5;"></div>
    </div>
    <div id="inl-stars" style="padding: 10px; border-top: 1px solid #333; display: flex; gap: 5px; justify-content: center;">
        <span class="star-badge" style="background: #333; padding: 5px 10px; border-radius: 3px;">S</span>
        <span class="star-badge" style="background: #333; padding: 5px 10px; border-radius: 3px;">T</span>
        <span class="star-badge" style="background: #333; padding: 5px 10px; border-radius: 3px;">A</span>
        <span class="star-badge" style="background: #333; padding: 5px 10px; border-radius: 3px;">R</span>
    </div>
</div>
"""
content = content.replace("</body>", inline_overlay_html + "\n</body>")


with open("templates/index.html", "w") as f:
    f.write(content)
