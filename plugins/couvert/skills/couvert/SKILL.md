---
name: couvert
description: >
  Lightweight session open/close ritual — top-and-tail a work session without a
  full work-tracker. Use when the user says open/start a session ("/open", "let's
  start") or close/wrap one ("/close", "wrap up"). Orients at the start; reflects,
  captures a short note, and commits at the end.
---

# Couvert — session lifecycle (no work-tracker)

A *couvert* is the cover laid before service and cleared after. This skill does
the same for a work session: a light open and a light close, no ticketing system
required.

## Open

1. **Orient.** Read the latest session note (if any — see the session log below)
   and `git status`; summarise in 2–3 lines where things stand.
2. **Surface open loops.** Name any obvious unfinished edits or loose threads.
3. **State intent.** Say the session's intent in one sentence. Ask once if it's
   unclear — this is orientation, not interrogation.

## Close

1. **Reflect.** What changed this session — 3–5 past-tense bullets.
2. **Next Action.** Name the single thing to resume with.
3. **Capture.** Append a short note (date, intent, what-changed, next-action) to
   the session log.
4. **Commit.** Commit staged work with a concise message. Closing seals; it does
   not open new threads.

## The session log

A plain markdown file the open step reads and the close step appends to. Default
location: `SESSION_LOG.md` at the repo root (create it on first close). Keep
entries short — this is a memory aid, not a journal.
