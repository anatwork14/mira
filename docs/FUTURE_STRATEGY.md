# MIRA — Long-term product and research strategy

Date: 2026-11-26. Proposed roadmap, not implemented features or measured results. This document complements PROXY_FIRST_48H.md, EFFICIENCY_AND_VALUE.md and HYBRID_GRAPHRAG.md; it does not change the active 48-hour sprint acceptance criteria. The current branch contains a standalone retrieval prototype, not a verified proxy runtime.

## 1. Product thesis

Evolve from a local intelligent HTTP(S) proxy to a privacy-preserving adaptive trust intelligence layer for humans and agents. Prioritize safe task completion, evidence-backed adaptation, and low overhead. Do not compete by reproducing every SWG, SIEM, EDR or agent firewall capability. Existing alternatives already cover bidirectional scanning, DLP, signed receipts and AI usage discovery. Test whether MIRA's temporal evidence, lightweight local retrieval, safe recovery and transparent policy experimentation provide incremental utility.

## 2. Product opportunities

### A. Temporal Flow Intelligence (primary research bet)
A request can be harmless in isolation but suspicious in context. Separate the long-lived verified Knowledge Graph from short-lived Observation/Flow Graph. The latter records sanitized direction, destination scope, timestamp, session ID from authenticated/configured client, reason flags and observed outcome. Correlate explicit flow IDs or trusted agent task IDs; temporal proximity alone is correlation, not causal provenance. A proxy cannot infer which local file was read, what a user intended, or whether two flows share an agent unless an authorized adapter supplies this. Browser-only or unauthenticated client observations remain uncertain.

First incremental implementation: bounded per-client/session window, e.g. 5 minutes and 32–128 events, simple sequence rules (inbound suspicious content then outbound sensitive transfer, new destination then policy violation), no GNN or per-event embeddings. Aggregate non-security events; preserve security-relevant event IDs, expiry and relationship confidence. Never link unrelated users; no durable raw bodies. Qwen sees compact sanitized sequence summaries only on ambiguous cases. Verify required checks synchronously before dispatch. Correlation raises a review signal, not a permanent domain label or proof of compromise.

### B. Trust Passport 2.0: destination, action, and evidence separated
Keep the existing evidence-backed Dynamic Trust Score for destination scope. Add explicit action-level risk (data class, permitted action, destination, authority, observed behavior), confidence/coverage and identity provenance as separate fields; do not average trust into authorization. The same trusted domain can allow reading but deny sensitive upload. Unknown remains unknown. Expose change reasons, evidence expiry, verification scope, and possible next actions; provide no person/employee trust scores. Only verified scope-relevant evidence updates long-lived profiles; repeated observations and model outputs remain review candidates.

### C. Intent-scoped Agent Security (adapter-dependent)
Introduce an opt-in task manifest from trusted user/operator or authenticated orchestration layer: task ID, agent identity, allowed tools/destinations/actions/data classes, expiry and quotas. Proxy sees only mediated network actions, not all local tool calls. Adapter passes authenticated task context via local control plane, never trust arbitrary headers from traffic. Independent enforcement prevents out-of-scope mediated actions. Future MCP/tool adapter and runtime sandbox supply data-flow labels and capabilities; do not claim CaMeL-style guarantees from HTTP observation alone. Narrow authority per task and support revoke/expiry. No automatic policy widening by LLM.

### D. Policy Flight Simulator
Shadow evaluate candidate policies beside active policy without weakening the active hard floor. Compare allowed/held/denied counts, newly affected services, reasons and missing-feature rate; distinguish replay on retained metadata from live shadow checks. Record policy version and evidence snapshot; do not resend historical requests. Promote only after authorized review, staged rollout and rollback plan. Actual prevented effects require active enforcement; shadow mode reports counterfactuals only. Do not infer productivity from traffic.

### E. Safe Recovery and Security Inbox
Group related sanitized findings by scope, reason and time; show which request was blocked and which response was withheld, evidence and owner-approved remediation. Suggestions: remove secret locally, choose approved destination, update dependency to verified fixed version, request scoped review. Revalidate every new action. No auto-replay, auto-upload, auto-install or unreviewed policy edits. Capture explicit resolved/rejected/unknown state; measure legitimate task recovery, not number of alerts.

### F. Risk budgets and resource governance
Maintain deterministic counters for per-task requests, outbound bytes, new destinations and optionally provider-reported token usage on supported authenticated AI APIs. Set explicit budget and expiry; when exceeded hold or stop as configured. These are observable consumption caps, not inferred monetary costs or worker productivity. Bound inference queue and optional analysis compute separately; required checks cannot be dropped to achieve throughput. Optimize by risk-tier and measured coverage.

### G. Open Security Knowledge Packs
Versioned signed packs of public, licensed indicators, mitigation cards, policy templates and graph edges. Each record includes provenance, scope, observed time, expiry, verification and revocation. Validate signature against explicitly trusted publisher key; signatures authenticate origin, not correctness. Stage/review before activation; rollback and invalidation must respect current revocations, expiry and anti-rollback rules. No raw user telemetry, private organization policy, or automatic export. STIX 2/TAXII adapter later; keep internal schema minimal. Source-specific terms and redistribution rights must be checked. Community feedback is untrusted until reviewed.

### H. Exposure and supply-chain intelligence
Join verified new domain/URL indicators with previously retained compatible observation features to assess potential historical exposure, not past compromise. For CVE/OSV use actual affected product/package ecosystem and version from opt-in inventory or lockfile, not guess from HTTP domain. CISA KEV/EPSS can help prioritize confirmed affected versions; not permission scores. Produce impacted resource list and remediation ticket candidate, with unknowns. Integrate existing tooling rather than build a scanner.

### I. Interoperability and deployment
Expose small versioned decision/receipt API, JSONL export, OCSF mapping for security events, OpenTelemetry metrics for model/proxy timings and provider-reported token usage where available. OPA adapter and MCP gateway integration later. Separate data plane, knowledge/control plane, local dashboard. Support offline personal mode first; managed team mode requires authentication, identity binding, RBAC, tenant isolation, retention/consent, signed policy rollout and authorized TLS inspection. Do not deploy transparent interception outside explicitly authorized environments. Linux network containment, Windows/macOS capture, non-HTTP and pinned TLS require independent tests. No hidden monitoring or employee surveillance.

## 3. Optimized architecture and data lifecycle

Two graphs, one SQLite deployment initially:
- Knowledge Graph: verified, versioned evidence and scoped relationships, durable subject to expiry/revocation; existing exact/BM25/dense/graph retrieval.
- Observation Graph: short bounded window of sanitized events and correlations, not authoritative facts; aggregate/expire normal activity, retain minimal incident receipts by policy. Bridge through explicit typed entity IDs; never auto-promote observed correlations to verified relations.
Fast path: deterministic checks, indexed exact indicators, current policy and bounded recent counters. Smart path: selective hybrid graph retrieval + compact Qwen3.5-0.8B classifier with abstention. Background: aggregate, candidate review, verified updates, optional shadow policy, signed pack verification. Cache scoped by policy/knowledge version and freshness; do not cache domain-only authorization. No GNN, second LLM, vector DB or per-flow embeddings required. Use bounded windows and TTL, no raw payload storage. Separate inference routing, evidence relevance, trust and final policy decisions.

## 4. Roadmap and gates

P0 (48h): existing proxy-first mandatory scope, no new hard requirements. Trust Passport and Security Receipt reuse existing UI after gates. Optional single aggregate AI destination counter. First verify actual E5 retrieval, Qwen, HTTPS, isolation and target-side effects.
P1 (1–2 week candidate, not estimate guarantee): temporal window/correlation with explicit provenance, shadow policy diff, security inbox/recovery, incident-level storage. Test split-session false linkage and policy rollback. 
P2 (1–2 month candidate): opt-in authenticated agent task manifest, quotas, curated public intelligence packs, exposure analysis, adapters and structured event exports. Validate tampering, expiry, identity spoofing and data isolation. 
P3 (long-term): managed endpoint coverage, enterprise identity and deployment controls, independent signed receipt verification, federated knowledge distribution if licensing and privacy permit. Consider more scalable graph/vector index only after profiling. No merchant/payment or whole-device protection claims without authorized integration.

## 5. Research program

R1 temporal context: same scanner and Qwen, compare single-flow vs bounded sequence rules vs sequence+hybrid evidence. Use held-out workflow families, benign lookalikes, interleaved sessions, randomized order and no-authorized-task-ID cases. Measure attack goal success, utility under attack, false holds, attribution error, p95 latency and bytes/event.
R2 adaptive routing: compare always-Qwen, rules, rules+selective Qwen, exact/BM25+dense and graph expansion. Equal security floors, evidence snapshots and token budgets; measure risk/coverage, abstention, inference rate, throughput, RAM, DB growth and downstream safe completion. Do not force invocation ratio at expense of required checks.
R3 temporal trust: compare static indicators, freshness-aware verified evidence, and graph-aware retrieval. Test revocation, stale evidence, source conflicts, poisoning, unrelated associations and recovery. Measure update delay and false blocks, not accuracy of an uncalibrated score.
R4 policy productivity: paired baseline tasks and shadow policy, compare safe task completion, recovery time, false hold and reviewer effort. No ROI or field claims without observed data.
R5 knowledge packs: test replay, signature failures, unauthorized publication, expired indicators, selective invalidation and rollback. Verify no private telemetry included.
Use AgentDojo (task-level evaluation where adapter mapping is valid), isolated HTTP(S) synthetic target for proxy effects, and own public bilingual hard-negative fixtures. No live malicious services or private data. Report limitations, failures and actual measurements.

## 6. References and prior art (documentation-level review)
- Pipelock: https://github.com/pipelab-org/pipelock
- Cloudflare AI Security: https://www.cloudflare.com/solutions/ai-security/
- CaMeL: https://arxiv.org/abs/2503.18813
- CaMeLs Can Use Computers Too: https://arxiv.org/abs/2601.09923
- MotifTrace: https://link.springer.com/article/10.1186/s42400-026-00651-x
- FuseChain (preprint): https://arxiv.org/abs/2606.15811
- NIST Agent Identity Management: https://www.nist.gov/blogs/cybersecurity-insights/design-tenets-agent-identity-management-systems
- NIST Zero Trust: https://csrc.nist.gov/pubs/sp/800/207/final
- OWASP Agentic Applications 2026: https://genai.owasp.org/top-10-for-agentic-applications-2026/
- OPA dry run and masked decision logs: https://www.openpolicyagent.org/docs/envoy ; https://www.openpolicyagent.org/docs/management-decision-logs
- STIX/TAXII: https://oasis-open.github.io/cti-documentation/
- OCSF: https://github.com/ocsf/
- OpenTelemetry GenAI: https://github.com/open-telemetry/semantic-conventions-genai
- AgentDojo: https://arxiv.org/abs/2406.13352
- Google semantic governance policies, Nov 2026: https://developers.googleblog.com/did-the-user-ask-for-this-securing-ai-agents-against-intent-hijacking-with-semantic-governance-policies/

These are inspirations and comparison targets, not proof of novelty or measured superiority. No new source code or runtime measurements in this strategy update.
