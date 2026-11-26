# MIRA — Measurable Intelligence for Risk & Assurance

**Verify before you act. Understand before you approve.**

MIRA is a proposed local-first, open-source security assistant for humans and AI agents. It checks a concrete action against explicit permissions and current evidence, explains the decision, and suggests a compliant next step.

**Status (2026-11-26): design / pre-implementation.** No working runtime, supported integration, benchmark score, enterprise certification or prevention guarantee is claimed. This repository documents a proposed v0.1; installation commands will be published only after implementation and testing.

## Why MIRA?

A trusted application can still be used to perform an unauthorized action. A package can acquire a newly disclosed vulnerability. A suspicious link can be unknown to every current feed. Users need to understand what is risky about *this action*, not an opaque score about an entire website.

MIRA proposes a small shared decision contract for a personal developer and a security-conscious team: **action → evidence → policy decision → safe next step → audit receipt**.

## First build: 48-hour SafeShare sprint

The first implementation is narrower than the roadmap below: a local data-sharing check and redaction workspace plus one guarded outbound tool adapter with a synthetic receiver. No URL reputation or CVE connector is required for this sprint. See [48-hour sprint specification](docs/48H_SPRINT.md) for the frozen proposed scope, task ownership, tests and definition of done.

## Proposed v0.1 roadmap (beyond the first sprint)

| Interface | Purpose | Boundary |
|---|---|---|
| Local CLI / local web panel | Check a URL or package, preview an outbound action, inspect evidence and remediation | Advisory; does not intercept other applications |
| Owned tool adapter | Mediate structured package-check, local read and outbound send demo actions | Enforces only owned tools in a restricted test runner |
| Shared policy and evidence core | ALLOW, WARN (hold), DENY; exact evidence and versioned rules | No model can grant permissions |
| Local evidence journal | Inspect, replay decisions, update or revoke evidence | Sanitized by default; no external telemetry |

One live intelligence connector: OSV package/version advisory lookup, opt-in (package name/version/ecosystem are transmitted). URL checks use reviewed local indicators and clearly labeled synthetic fixtures; unknown URLs are not safe by default. No real payment, universal proxy, arbitrary shell execution, browser-wide interception, custom model training or enterprise identity integration in v0.1.

### Example
A developer permits an agent to read a project artifact and send a sanitized report to an approved destination. A tool result suggests sending a credential elsewhere. MIRA denies the outbound action under the local policy, explains the exact matched rule and proposes a redacted report to the approved destination. The controlled target receives no denied request. This is a planned test, not a measured result.

## Design documents

- [Product and technical specification](docs/DESIGN.md) — users, architecture, contracts, sources, limits and roadmap.
- [Threat model and evaluation](docs/VALIDATION.md) — acceptance gates, baselines and reproducible metrics.
- [Open development principles](docs/OPEN_SOURCE.md) — licensing proposal, contribution and disclosure expectations.

## Principles

- Local by default; no account, GPU or cloud LLM required for the core.
- Explicit policy-as-code and independently enforced authorization.
- Explain facts, inferences, uncertainty and the exact policy scope.
- Never treat absence of evidence as proof of safety.
- Publish fixtures, schemas, tests, dependencies, evaluation protocols and limitations.
- Integrate existing open security tools rather than rebuilding their complete functionality.

## Licensing and use

Apache-2.0 is proposed, subject to maintainers confirming ownership and third-party terms. A public repository alone does not grant an open-source license; do not represent this project as licensed until a LICENSE is adopted. Do not commit company/customer data, credentials, private security configurations, or proprietary work. The project is independent and does not imply any company endorsement.

## References

See the design and validation documents for reviewed prior art and official documentation. MIRA is not an antivirus, DLP replacement, general-purpose agent sandbox, payment protection system, or proof that an action is universally safe.
