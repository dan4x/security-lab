# CLAUDE.md — Web Application Security Lab (SQLi)

## Context
This repository is a **deliberately vulnerable security lab**, for studying
and practicing exploitation and remediation, running **locally**. All use
must be **authorized** — only against this lab, never against third-party
systems. The didactic goal is to write original scripts that exploit the
vulnerabilities and extract a target value in the format `CW{...}`.

## Exercise conventions
- The target value ("flag") is a string starting with `CW{`.
- Exploit scripts must be **original** (Python), **no SQLMap** and no
  wrappers around it — the learning goal is writing the technique yourself.
- Code must be **well documented** (docstrings/comments explaining the
  *why* of each step, not just the *what*).
- The database simulates **multiple applications** — do not assume the
  target is in the `users` table; enumerate the full schema.
- Prefer **deterministic and fast** execution: short timeout per request,
  network/HTTP error handling, end-to-end flow with no manual steps.

## What we already know about the vulnerable code
- Flask app (`app.py`), port 4001, `debug=True`, SQLite (`challenge.db`).
- `/api/user?username=...` — **vulnerable (SQLi)**: builds the query with
  an f-string (`f"SELECT username, email FROM users WHERE username =
  '{username}'"`), with no parameterization. This is the main entry point.
  - The query has **2 columns** in the SELECT (`username`, `email`) —
    relevant for UNION-based injection.
  - Exceptions return `str(e)` in the JSON (500 error) — SQLite error
    messages leak in the response, enabling error-based/boolean-blind
    extraction.
- `/api/profile?id=...` — uses `cursor.execute(query, (user_id,))`,
  parameterized. **Not a SQLi vector** (the flaw there is broken access
  control, not injection).

## Approach for reasoning about an exploit
1. Confirm the injection and the database type (SQLite) before extracting.
2. Enumerate the schema via `sqlite_master` (tables and columns) — don't
   assume where the target is.
3. Prioritize the fastest technique (UNION/error-based > boolean-blind >
   time-blind).
4. Deterministic script, running end-to-end on its own.
5. Comment the rationale behind each step.

## What NOT to do
- Do not use SQLMap, and do not simulate a wrapper around it.
- Do not apply these techniques outside this authorized local repo/lab.
- Do not assume table structure without confirming it via enumeration first.

## Environment
- Generate the test database: `python make_fixture.py` (creates
  `challenge.db`).
- Run the app: `python app.py` (port 4001). For local use, prefer
  `host='127.0.0.1'`.
- Test manually with a simple payload first, before automating.

## Included skill
`.claude/skills/vuln-exploit/` — audits any code in the repo guided by the
OWASP Top 10 and develops original exploits. See `SKILL.md`.
