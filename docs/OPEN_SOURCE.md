# Open-source governance and transparency

Status: proposed project governance. This public repository contains a design, not a released security product.

## License and ownership
Recommend Apache-2.0 for broad reuse and explicit patent terms, subject to maintainers confirming ownership and authority to license all material. A LICENSE file must be adopted before advertising the repository as open source; do not infer permission from public visibility. Check upstream dependency licenses, notices and advisory-data redistribution rights before bundling any third-party material. Publish dependency inventory/SBOM and attribution when code exists.

No company internal policies, names of private systems, customer or merchant data, production credentials, proprietary code, internal competition details, or unauthorized telemetry belong in public history. Use synthetic fixtures, clearly labeled. Review rights and scan history before public code release. No claimed endorsement or affiliation.

## Transparent development
Use GitHub issues for public design proposals, separate PRs for changes, a documented security-impact checklist, small reproducible tests, and maintainer review. Publish architecture decisions (why, alternatives, tradeoffs), versioned schemas and policy examples, evidence-source manifests, evaluation methodology, and actual results including failures. Report policy/knowledge versions, reason codes and execution status; avoid claims of universal safety, unvalidated trust scores or production readiness.

Contribution proposals should state intended behavior, supported boundary, test cases and privacy/security impact. Review changes to rule matching, approvals and executor separately from UI changes. No automatic policy changes from community reports. Unverified reports are untrusted; public threat information requires source attribution, scope, freshness and revocation mechanisms.

## Security reporting
Maintainers should enable GitHub private vulnerability reporting where available and document a monitored contact in SECURITY.md before shipping runnable code. Report suspected vulnerabilities privately; include reproducible synthetic test steps, affected version and impact, omit secrets/personal data. Do not promise a response SLA before ownership is established. Do not test systems without authorization. No real exploit or sensitive fixture is required to contribute.

## Release policy
Local-first defaults, no telemetry or external model calls by default, opt-in external vulnerability queries with visible payload disclosure, user-controlled retention/export. Explain the limits of local receipts and single-workspace identity. Publish changelog, checksums for release artifacts and validation reports after actual implementation; no fake badges or PASS. An enterprise deployment is not assumed to be authorized by use of the public project.
