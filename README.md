# MIRA — Measurable Intelligence for Risk & Assurance

**Verify before you act. Measure trust continuously.**

MIRA is a proposed local-first intelligent HTTP(S) security proxy for humans and AI agents. It inspects supported requests and responses, uses a lightweight local model with graph-retrieved evidence for selective semantic analysis, applies independent policy, maintains dynamic destination trust profiles, and reports privacy-preserving traffic statistics.

**Status (2026-11-26): design plus standalone retrieval prototype.** No working runtime, measured performance, enterprise certification, all-device interception or universal prevention claim.

## First build: proxy-first 48-hour sprint

The active design is [PROXY_FIRST_48H.md](docs/PROXY_FIRST_48H.md). It supersedes the previous SafeShare-only sprint.

| Component | Proposed implementation |
|---|---|
| Networking | mitmproxy forward proxy + Python addon |
| Demo | Docker isolated client, proxy, local model and synthetic HTTP(S) target |
| AI | Qwen3.5-0.8B, llama.cpp quantized GGUF, bounded structured prompts |
| GraphRAG | SQLite exact + BM25 + optional dense cosine + RRF + bounded graph traversal (prototype committed) |
| Dynamic Trust | Public heuristic, scope, evidence coverage, freshness, overrides |
| Policy | Deterministic request/response enforcement; model cannot grant permissions |
| Storage | SQLite, bounded caches, sanitized flow metadata and aggregates |
| UI | Local dashboard for decisions, trust, traffic and resource measurements |

All supported HTTP(S) traffic in the isolated demo must traverse the proxy. Actual host-wide coverage requires platform-specific routing and enforcement; encrypted/pinned or unsupported traffic may not be inspectable. TLS interception requires authorized client trust of a demo CA. Never install a CA on the host automatically, bypass pinning, or intercept others' traffic without authorization.

## Planned demo

A clean request succeeds. A synthetic credential upload to a prohibited destination is blocked before the target receives it. A suspicious response is withheld from the client (upstream effects are not undone). A reviewed evidence update changes the destination trust status and subsequent policy decision. The dashboard records sanitized receipts for both directions. This is a planned scenario, not a test result.

## Retrieval prototype

See [Hybrid GraphRAG research and API](docs/HYBRID_GRAPHRAG.md) and [implementation](mira/retrieval.py). Six search modes, optional local multilingual E5, evidence validity and graph provenance. Eight synthetic unit tests passed on byte-identical retrieval and test files; actual embedding model, Qwen and proxy integration not yet verified.

## Design documents

- [Active 48-hour proxy-first specification](docs/PROXY_FIRST_48H.md): topology, bidirectional pipeline, model/prompt, GraphRAG, trust, storage, acceptance gates.
- [Earlier product and technical specification](docs/DESIGN.md): historical design; not the active sprint scope.
- [Earlier SafeShare sprint](docs/48H_SPRINT.md): superseded by proxy-first scope.
- [Validation principles](docs/VALIDATION.md): earlier broader evaluation plan; active sprint gates are in proxy-first spec.
- [Open development principles](docs/OPEN_SOURCE.md): licensing proposal, contribution and disclosure expectations.

## Principles

- Local inference, no cloud model or external telemetry required.
- No raw request/response bodies, credentials, cookies or private prompts in persistent logs.
- Distinguish observed, inspected, forwarded, blocked and delivered flows.
- Explicit policy-as-code; a high trust score never overrides hard rules.
- Publish model/version, prompt, rules, trust formula, sources, fixtures, tests, results and limitations.
- Integrate established open tools instead of reimplementing networking and inference.

## Licensing and use

Apache-2.0 proposed pending maintainer ownership and third-party terms review. Public visibility alone is not an open-source license. No company/customer data, private configurations, real credentials or unauthorized monitoring. Independent project; no company endorsement. MIRA is not a production DLP, antivirus, universal firewall or guarantee of safety.
