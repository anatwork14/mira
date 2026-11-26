# MIRA — 2-day sprint specification: SafeShare

Status: proposed implementation plan, 2026-11-26. This document narrows the initial build to a two-day sprint; DESIGN.md remains the longer-term design, not the sprint backlog. No code, integration, test result, timing or protection claim is implied.

## Product goal

Verify before you share. One shared local decision core protects the same outbound-data workflow for a person and a controlled AI tool caller. Demonstrate sensitive-data detection, destination-specific permission, explanation, redaction and successful revalidated recovery. Target individual developers and small teams first; no enterprise deployment claim.

Non-goals: broad URL reputation, CVE ingestion, universal proxy, browser interception, payment/merchant checks, trained JEV, vector DB, knowledge graph, SSO, general shell, arbitrary outbound HTTP, multi-user hosted service. OSV and browser extension are optional only after all sprint gates, preferably defer.

## Required demo and user flow

1. User pastes sample text into a local panel and chooses a named destination (approved team endpoint, public AI service, unknown destination). No raw payload goes to external APIs. The panel is advisory and does not intercept other apps.
2. Scan structured synthetic credential patterns (e.g. private-key marker, labeled API token, demo canary) and configured sensitive tags. Display category/count and masked evidence, rule IDs, destination and policy version. No claim to detect all secrets or personal data.
3. Decision: ALLOW / WARN (hold, no execution) / DENY. Hard deny for a secret or restricted data at prohibited destinations. Unknown destination or incomplete classification -> WARN, no execution. Explicitly allowed clean scoped action -> ALLOW. Unsupported tools, malformed input or unavailable required policy/scanner -> DENY. An ALLOW is policy-specific, not a guarantee of safety. Personal mode can copy a sanitized draft locally; never auto-send to a real external destination.
4. User clicks redact locally, sees masked replacement; a new check is required. Never auto-change a destination or silently send. Raw data is transient and not stored; do not log text, credentials, raw request bodies, or low-entropy secret hashes.
5. Agent demo: scripted tool caller (clearly identified) or optional actual LLM with synthetic data only invokes an owned send_report adapter. Executor owns fixed destination mapping and credentials; the caller cannot provide arbitrary URLs. A separate local mock receiver counts accepted requests. A DENY/WARN never dispatches. An approved sanitized send reaches receiver once. Label all targets/fixtures synthetic. If runner network isolation is not verified, claim only mediation of the adapter, not bypass prevention.

## Minimal architecture and stack

Single Python FastAPI app, static HTML/JS or lightweight frontend, Python regex scanner, JSON policy, SQLite sanitized journal, pytest. No Node build or GPU needed. Local-only by default (loopback binding, same-origin/CSRF safeguards, payload limits). Docker Compose only for local receiver and runner isolation if time allows; no external network from demo runner. No arbitrary request forwarding. Keep dev dependency versions pinned after smoke tests.

Files:
- app/main.py: API and static UI
- app/core.py: deterministic scanner, validation, policy, decisions and redaction
- app/adapter.py: guarded execution to fixed receiver (no redirects, short timeout, body limits)
- app/journal.py: sanitized decision and execution records
- app/static/: one workspace (check, explain, sanitize, history) and agent demo tab
- policies/demo.json: editable local rules, version, named destinations and allowed data classes
- demo/receiver.py, demo/agent.py: synthetic receiver and scripted caller
- tests/: unit and integration tests; fixtures/: synthetic cases
- README.md: actual tested install instructions after implementation

API contract: POST /api/check {destination_id, text, declared_data_class}; POST /api/redact {text}; POST /api/demo/send {destination_id, text, declared_data_class} (fixed receiver only); GET /api/history; GET /api/demo/receipts. Redact is advisory, never an execution authorization. /demo/send re-evaluates exact input and current policy server-side before any dispatch; caller-supplied classification can increase restrictions, never override scanner or server policy. No authorization grant based on a preview, no arbitrary command, no automatic retry of side effects.

Decision: id, ALLOW/WARN/DENY, reason_codes, matched categories and counts, rule_ids, policy_version, remediation_type, mode (ADVISORY/ENFORCED), execution_state (NOT_EXECUTED/PENDING/EXECUTED/FAILED/UNKNOWN). Return no raw secret spans or source text in journal; masking is computed in-memory. Keep sanitized result only in active user session. Unknown, scanner limits and unsupported input explicitly surfaced. SQLite is local mutable audit history, not tamper-proof.

AI role: optional semantic classification or explanation from synthetic/masked metadata, never necessary for P0 and never authoritative. If real LLM is used in demo, synthetic inputs only, output validated, no raw user data. Default offline deterministic explanations remain fully functional.

## Two-day schedule (about 16–20 productive hours, estimate, not guaranteed)

Day 1 hours 0–2: freeze schemas, rules, synthetic demo and acceptance tests. Owner sets scope; parallel agents share contract. Hours 2–6: core and API, UI and fixtures built separately. Hours 6–8: integrate, real receiver and owned tool adapter, first vertical slice. Day 1 gate: check -> reason -> redact -> recheck; denied sends produce zero target requests.

Day 2 hours 0–3: adversarial tests, failure cases, verify no payload logging, optional runner isolation. Hours 3–5: UX polish, history, one-click demo, measured local latency and fixture results. Hours 5–7: clean install/reproducibility, README, known limits, demo recording. Hours 7–8: bug buffer and final validation. Do not start optional scope until mandatory gates pass. If time is short, remove optional LLM, Docker isolation and UI decoration first (downgrade coverage claims if isolation omitted); never remove target-side checks or privacy tests.

Agent A owns app/core.py + policy + unit tests. Agent B owns main.py + static UI, using the frozen decision contract and fixtures. Agent C owns adapter, receiver, journal and integration/security tests. Agent lead integrates, independently reviews enforcement, data flow, dependencies, tests and docs. Use disjoint files/worktrees, small PRs; no concurrent edits to shared schema without lead. No generated claim of PASS without running tests. Avoid enabling autonomous writes outside assigned workspace.

## Mandatory release gates

- Clean allowed input to registered receiver -> exactly one observed request.
- Secret or prohibited destination -> zero receiver requests; unknown destination -> hold with no dispatch.
- Redaction creates a new preview; a new guarded send passes only if policy permits.
- Client manipulates declared classification, destination ID or preview result -> no bypass.
- Malformed/oversized inputs, missing policy, scanner failure or receiver error -> no implicit allow or automatic retry.
- Credential canary absent from logs, SQLite, error response and export; only expected in ephemeral synthetic input. Receiver never sees denied payload.
- Advisory vs enforced distinction visible in UI/API and README. Unknown is not safe. Optional bypass/isolation claim requires direct network access test.
- At least 30 frozen synthetic cases across benign, sensitive, prohibited, unknown and recovery paths; publish case-level outputs, counts and limitations, not broad detection accuracy. Measure median/p95 local check latency on specified hardware (no fabricated numbers).
- Clean setup from checkout; actual commands tested. Public repo contains no company information, real credentials, internal policies or user data. Licensing remains pending maintainer approval.

## Evaluation and demo

Compare no guard, static destination-only policy and MIRA scanner + policy + recovery on the same synthetic task scenarios (no-guard sends only to isolated synthetic receiver). Count forbidden effects, valid completed tasks, false blocks, recovery and review rate. No measured ROI or universal security guarantee. A 90-second demo: person checks a sensitive draft -> denied with reason -> redacts/rechecks -> allowed; scripted agent attempts the same prohibited send -> target counter unchanged -> sanitized approved send -> counter increments, journal records both. Explain one codebase, two interfaces, and limits. Optional AI demonstration explicitly separated from deterministic baseline.

Definition of done: a reproducible, working local SafeShare vertical slice, not a production DLP or full MIRA platform. Future scope requires separate design and evidence.
