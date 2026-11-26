# MIRA — Efficiency and value research

Status: design recommendations, not implementation or measured results. Companion to PROXY_FIRST_48H.md; preserves the 48-hour Docker demo, Qwen3.5-0.8B, lightweight graph retrieval and dynamic trust. No scope expansion may compromise mandatory safety gates.

## 1. Critical-path design

Separate synchronous security decision from asynchronous housekeeping. In requestheaders/responseheaders determine required inspection, known size/content type, policy and whether streaming is allowed. Required inspection: bounded buffering and decompression, then check before forwarding/delivery. Oversize/unknown encoding or exhausted required buffer budget -> hold/deny. Metadata-only allowed streaming explicitly labeled; never claim body coverage or retract already sent data. Test chunked bodies, compressed content, concurrent flows, SSE and unsupported protocols. No arbitrary header/type exemption: untrusted content-type and GET do not establish safety. Use async mitmproxy hooks and pooled local inference HTTP client, bounded semaphore/queue, timeouts, avoid blocking CPU-heavy parsing on event loop. No synchronous dashboard queries. Keep default upstream TLS verification.

Fast path: immutable compiled policy, indexed exact indicators and scoped trust snapshot; deterministic payload checks for required flows. Smart path: bounded evidence graph retrieval and one Qwen call per eligible direction. Background path: aggregate telemetry, candidate review, publish versioned evidence, periodic expiry/checkpoint. Only non-required checks may be asynchronous/advisory after delivery. Separate high priority mandatory decisions from optional analysis; fail closed under load for required checks. Explicit monitor mode is advisory, not protected.

Cache only reusable evidence/retrieval metadata and verdicts for identical sanitized inputs with complete feature coverage; no domain-only allow cache, no cross-tenant or cross-principal reuse. Key includes scope, method/direction, policy, knowledge, model, prompt, extractor versions and content identity; if sensitive content, avoid result caching by default, do not persist payload hashes. TTL <= earliest evidence expiry, targeted invalidation on verified changes. Coalesce concurrent identical evidence lookups only. Caching never bypasses hard checks. Do not cache unknown/timeouts as safe.

## 2. Qwen inference

Keep one warm text-only Qwen3.5-0.8B llama-server. Benchmark Q4_K_M vs Q8_0, same corpus; non-thinking, compact schema, stable instructions, input 256/512/768 tokens candidate, max output 32/64/96 tokens selected by actual schema completion (truncation -> unknown), context 2048 per slot candidate. Compare deterministic greedy vs documented sampling only on validation; fix settings for test. Benchmark slots 1/2/4, continuous batching, threads and CPU/GPU profiles; report native vs Docker CPU (Mac Docker does not expose Metal normally). Bound cache RAM and recurrent/context checkpoints; do not persist sensitive prompt states; prefix caching only if proven isolation. Do not use speculative decoding, long contexts, external embedding model or additional LLM in sprint. Grammar guarantees structure, not truth.

Use compact enum output {"r":"PI","a":"S","e":[1]} (example; mappings published); deterministic engine validates evidence IDs and builds human explanations. Separate trusted policy and untrusted data, strip scripts/markup where appropriate but preserve security-relevant features, inspect outbound whole supported bounded body deterministically; selected excerpt is not full semantic inspection. No raw cookies, credentials, prompts or private bodies in LLM logs/requests. Incomplete/unsupported input is visible. Qwen cannot authorize, publish intelligence or call tools.

Throughput capacity: offered inference jobs/s = HTTP flows/s × eligible-direction fraction × mean calls/eligible flow. Measure sustainable service rate under batching; if offered load approaches capacity, queue/tail latency rises. Example 100 flows/s × 5% × 1 = 5 jobs/s; this is demand, not measured model capacity. Reduce optional work and hold required work if service unavailable; do not change policy to meet latency. Report per-lane p50/p95/p99 and global p95 plus routing, queue, prefill, decoding and cache hit. Use burst scenarios as well as warm steady load.

## 3. Graph, trust and storage

Keep typed SQLite graph (indexed node keys and adjacency, 1–2 hops, max 20 nodes, 3–5 facts). Seed domain/origin plus risk signal/policy class, filter exact scope, verified state and expiry; graph association is not direct proof. Precompute small evidence cards keyed by scope/version, refresh only affected nodes using reverse indexes. Use exact lookup fallback and compare exact evidence retrieval vs graph retrieval with equal token budget. No automatic LLM extraction of facts, no all-pairs traversal.

Trust remains the published time-decayed heuristic, separate from authorization and traffic volume. Recompute on verified change/revocation/expiry and lazy read refresh; snapshot validity ends by earliest relevant expiry or score refresh deadline. Keep deduplicated evidence, distinct source reliability, scope and coverage. Track observed signals separately; do not lower global trust based on one unverified model label, nor promote from popular domains, HTTPS or successful responses. UI shows score/UNKNOWN, evidence coverage, freshness and reason for changes. Do not store each access as a graph edge.

Use domain ID dictionary, short enums, flow IDs and timestamps, separate event details from aggregates. SQLite WAL single writer, short reader transactions, bounded batch queue for routine telemetry; security-critical receipt durable before permitted side effects if required by policy, outcome appended after; uncertain outcome explicit. One writer owns DB; dashboard read-only via local API or short queries. Raw metadata TTL 24h proposal, aggregates 30d, incident/evidence retention configured. Aggregate by time/domain/decision and direction; bounded cardinality, no user/URL label explosion. WAL checkpoints, deletion/space reclamation tested, disk quota includes WAL and model volume. No raw traffic dumps, full paths/queries, cookies, body, PII, secret hashes. Dashboard refresh 2–5s candidate or server-sent aggregate deltas; no polling all historical flows. Count observed vs inspected vs forwarded vs delivered; exact bytes at defined accounting boundary.

## 4. Product expansion ranked by value and effort

P0 after core gates (reuse existing events, policy and graph):
- Explainable Trust Passport: per destination score, scope, coverage, freshness, verified evidence and change reasons; action decision separately. Personal understanding, enterprise review.
- Security Receipt and Safe Next Step: blocked request vs withheld response, reason IDs, applicable policy, safe recheck suggestion (remove sensitive fields locally, verified destination, authorized review); no automatic resend or traffic rewrite.
- AI Usage / Shadow AI Visibility: categorize known AI provider domains via maintained explicit mapping; aggregate observed requests, volumes, blocked sharing, not prompts or individual productivity. Domain mapping indicates observed endpoint, not proof of AI use, intent or billable tokens. Personal privacy view; enterprise inventory with consent and access control.
- Evidence impact view: before/after verified update, list affected observed domains/flows using metadata; retrospective match only where stored features suffice, otherwise unknown. Show how new intelligence changes future decisions without claiming historical attacks.

P1, only after core and benchmarks: shadow-policy simulator (replay sanitized metadata and supported evidence flags, clearly mark incomplete cases, no network side effects); incident timeline grouping by scoped indicators and time window, not causal attribution; user report/review/revoke workflow; curated licensed URL threat feed with local matching and opt-in external verification; optional signed policy/evidence export. OSV package-version advisory only when exact package+version available via authorized integration, not guessing CVEs from website traffic. Do not ship broad threat crawling, employee rankings, price/cost inference from generic HTTPS or merchant scores. P2: managed host egress, consent/SSO/tenant isolation, targeted browser integration, privacy-preserving cross-team intelligence, independently verifiable receipts.

Differentiation hypothesis: lightweight local-first personal and team proxy, evidence-backed temporal destination trust and a closed loop from observed flow to explainable protection to policy review/recovery; test against existing projects. Pipelock already offers mediated egress, DLP, prompt injection and signed receipts; Cloudflare Gateway also offers AI/DLP visibility. No first-of-kind or superiority claim. Prioritize inspectability and measurable safe productivity.

## 5. Evaluation plan

Baseline proxy-only, rules-only, rules+Qwen, rules+exact-RAG+Qwen, rules+graph-RAG+Qwen; optimize one dimension at a time (routing, cache, batching, quantization, context, aggregation). Freeze same workloads, policy floor, timeouts, labels, hardware and versions; separate tuning from held-out evaluation by scenario family and time. Include clean static/API flows, benign suspicious-looking text, blocked credential, unknown/new destination, verified update, stale evidence, indirect injection, chunked/oversized flows, model timeout, DB/queue failure. Minimum 30 synthetic smoke cases per existing plan; expand before accuracy claims. Test no bypass and no sensitive log leakage. Report counts, detection recall/precision, false block/hold, actual effects, inspection coverage and abstention. Latency target candidates: local fast-path p95 <= 20ms added (excluding upstream), smart path p95 <= 2s on specified test hardware if achievable; never promise or trade mandatory controls. Report cold and warm, throughput, CPU/RAM/model and DB/WAL bytes, loss/queue depth. Compare graph exact vs multi-hop for evidence correctness, coverage and incremental quality. Track safe task completion, recovery, policy review time, time-to-protection and monitored false positives; no ROI without field evidence.

48-hour priority: implement existing core first, then trust passport and receipts in the same domain/event screens; AI usage counters are optional low-cost aggregate addition, evidence impact view only if all tests pass. No new infrastructure, no extra services. Policy simulator and incident grouping post-sprint. Use Docker isolated synthetic traffic; no real private traffic or real secrets.

## References
- https://docs.mitmproxy.org/stable/addons/examples/
- https://docs.mitmproxy.org/stable/overview/features/
- https://docs.mitmproxy.org/stable/api/mitmproxy/http.html
- https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- https://huggingface.co/Qwen/Qwen3.5-0.8B
- https://www.sqlite.org/wal.html
- https://microsoft.github.io/graphrag/
- https://prometheus.io/docs/practices/instrumentation/
- https://github.com/pipelab-org/pipelock
- https://developers.cloudflare.com/cloudflare-one/data-loss-prevention/
- https://docs.cloud.google.com/web-risk/docs/update-api (optional external commercial service, license/cost/privacy review)
- https://openssf.org/blog/2026/05/20/detecting-malicious-packages-using-the-osv-api/
- https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

Documentation-level research only; actual runtime behavior and compatibility must be tested.
