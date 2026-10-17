# Web Security Lab — SQLi & OWASP

[![Lab demo](https://github.com/dan4x/security-lab/actions/workflows/demo.yml/badge.svg)](https://github.com/dan4x/security-lab/actions/workflows/demo.yml)

A **deliberately vulnerable** lab for studying and practicing the
exploitation and remediation of web vulnerabilities, focused on **SQL
Injection** and the **OWASP Top 10** (Web / API / LLM). Everything runs
**locally**.

> ⚠️ **Authorized use only.** This repository exists for educational
> purposes. Only apply these techniques against this lab (or systems you
> have explicit permission to test). Never against third-party targets.

## Components

| File | Description |
|---|---|
| `app.py` | Intentionally vulnerable Flask app (SQLi, broken access control, misconfig). |
| `make_fixture.py` | Generates `challenge.db`, a synthetic database that simulates a payment acquirer (realistic volume; fictitious data). |
| `exploit_sqli_user.py` | Original, self-contained exploit: confirms the injection, enumerates the schema, and extracts the flag. |
| `run_demo.sh` | One-command demo: sets up the environment, starts the app, runs the exploit, and tears everything down. |
| `.claude/skills/vuln-exploit/` | Claude Code skill: audits the code guided by the OWASP Top 10 and generates original exploits. |
| `CLAUDE.md` | Lab conventions and notes about the vulnerable code. |

## Quick start

The fastest way to see it work end-to-end — sets up the venv, generates the
fixture, starts the app, runs the exploit, and stops everything:

```bash
./run_demo.sh
```

Expected output ends with something like:

```
[+] Flag found in table 'internal_config': CW{...}
[+] Total time: 0.2Xs
```

This exact flow also runs automatically in CI on every push (see the badge
above), so you can verify it works without even cloning the repo.

## Manual / step-by-step run

```bash
# 1. Environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate the test database
python make_fixture.py            # creates challenge.db

# 3. Start the app (port 4001)
python app.py
```

Test an endpoint:

```bash
curl -G "http://127.0.0.1:4001/api/user" --data-urlencode "username=alice'"
```

If the response leaks a SQLite error, the injection is confirmed. Then, in
a separate terminal, run the exploit:

```bash
python exploit_sqli_user.py
```

It enumerates the schema and extracts the target value in the format
`CW{...}`, hidden somewhere in the database — no table/column name is
assumed ahead of time.

## Vulnerabilities in the lab (for study)

- **SQL Injection** in `/api/user` (query built with an f-string, with no
  parameterization).
- **Error leakage** (`str(e)` in the 500 response) — enables error-based/
  blind extraction.
- **Broken Access Control / BOLA** — unauthenticated endpoints; reading
  data by id.
- **Security Misconfiguration** — `debug=True` + `host='0.0.0.0'`
  (exposed Werkzeug console; mostly relevant for a real deployment, not
  local dev).

`/api/profile` deliberately uses a **parameterized** query: it's there to
show what **isn't** a SQLi vector (the flaw there is broken access
control).

## Security note
Always run on `127.0.0.1` and never expose this app on the internet — it
is vulnerable by design.

## License
Educational use. Feel free to study, adapt, and contribute.
