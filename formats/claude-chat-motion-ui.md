# Claude chat motion UI

Reusable app-window component for reels that need to show a prompt being sent
and a useful answer arriving. The component is authored in
`videos/codex-reel-automation/claude_ui.py` and rendered into transparent PNG
frames by that project's `build_v06.py`.

## Visual system

- Reconstruct the familiar Claude web-chat surface: warm-white app panel, small
  orange sunburst mark and header, plus the message composer and send control.
- Keep chat inserts focused: type the prompt directly in the composer, animate a
  pointer tap on the send button, and omit sidebar/history unless the story needs it.
- Use the real app layout as a visual reference, but render the component locally
  as an authored animation. Do not claim that the mock is a live Claude session
  or that it returned real tool results.
- Keep the app window inside the reel safe box and below the speaker's face.
  In the 2026-11-07 automation revision, the composer/timeline is x=59..918,
  y=1200..1445;
  the English speech captions begin at y=1470.
- Animate text into the composer and a visible pointer tap on send. Avoid fake
  chat history, arbitrary loading labels, and invented counts.
- A timeline view can replace the composer on a measured music hit. Keep the
  same app surface and enlarge the timeline so it reads clearly on a phone.

## Current rendered example

The Codex automation Reel uses `Cut these clips to my script and music.` and
`Find B-roll that matches each line.` as representative prompts. The interface
animation is illustrative, not a live Claude session or actual Claude output.

Claude's documented chat product is available at [claude.ai](https://claude.ai);
Anthropic describes the web chat and its artifact/sidebar structure in the
[Help Center](https://support.anthropic.com/en/articles/8114487-what-interfaces-can-i-use-to-access-claude) and
[Artifacts guide](https://support.anthropic.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them).
