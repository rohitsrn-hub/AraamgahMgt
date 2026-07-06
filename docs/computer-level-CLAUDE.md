# Working with Rohit — applies to every project

<!-- This is the master copy of the computer-level CLAUDE.md.
     On Rohit's machine it lives at ~/.claude/CLAUDE.md.
     To install/update locally: open a LOCAL Claude Code desktop session and say
     "copy docs/computer-level-CLAUDE.md from the AraamgahMgt repo over ~/.claude/CLAUDE.md". -->

## Who I am
- I don't read or write code. I work entirely through chat and judge results by
  the running app and its outputs (screens, PDFs, reports).
- Talk to me in product terms — pages, buttons, report sections — never code
  jargon. If a technical point matters, give the one-line plain-English version.

## Approval gates (hard rules)
- New feature or any multi-file change: present a plan first, let me amend it,
  and write code only after my explicit approval. Small fixes I directly asked
  for may proceed — state the fix in one line before starting.
- Any action costing more than $2 in API credits: estimate it and ask first.
  Always pick the cheapest way to test. Budget isn't tight, but be efficient.
- Deleting or overwriting anything I created (files, data, records): ask first.

## Definition of done
- Pre-test every deliverable before showing me: run it, render it, screenshot
  it. Never present untested work.
- If a task is only partly achieved, say so plainly in the first sentence —
  never present partial work as complete.
- Every finished piece of work ends with: what changed in app terms, proof
  (screenshot/output), and what I need to do to see it live.

## Project memory
- Every project keeps a running history file (named in that project's
  CLAUDE.md). Read it at session start; append a dated 2–3 line entry after
  each completed feature or fix. This is how months of context survive
  between sessions — the chat itself does not.

## Installed skills (gstack, graphify, and others)
- Never auto-run a skill. When one genuinely fits my task, name it, explain in
  one sentence what it does and what it costs or saves, and ask if I want it.
- graphify is only worthwhile for "explain this codebase/topic to me"
  questions — not for routine coding work.

## Rules pack
- The coding rules in ~/.claude/rules/ecc/ (testing regime, style, security)
  apply to all projects. A project CLAUDE.md may override them where it says
  so explicitly.

## Git and cloud sessions
- Commit and push finished work to the session's designated branch without
  asking. Never merge to main — merging is mine, done on the GitHub website.
- Commit messages: plain English prose describing the change in product terms
  first — I read git history, not code.
- Cloud/web sessions cannot see this file or ~/.claude/rules/ (they run in a
  container, not on my machine). If a session says it lacks these rules,
  paste the relevant file into the chat.
