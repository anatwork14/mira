# MIRA Hybrid GraphRAG — research and implementation

Status: retrieval prototype committed; not an integrated proxy or measured SOTA. The branch was documentation-only before this work. Local test execution of the committed files was blocked by network access in the editing environment. The synthetic tests are supplied, not claimed passing; real E5 and Qwen integration require a separate runtime smoke test.

## Why graphs, and when not to use them
Exact typed IDs are mandatory for domain/URL/advisory/policy matching. FTS5/BM25 and dense retrieval are efficient for single facts and paraphrases. A graph adds explicit, scoped relations for multi-hop evidence, mitigation, provenance, temporal update and impact analysis. It is not inherently more accurate. Graph associations are context only: no transitive maliciousness, no permission grant, no score update by similarity. Keep plain RAG as baseline, use graph expansion only when relationship context is useful.

Relevant literature: [Microsoft GraphRAG local search](https://microsoft.github.io/graphrag/query/local_search/), [DRIFT](https://microsoft.github.io/graphrag/query/drift_search/), [LightRAG](https://arxiv.org/abs/2410.05779), [HippoRAG 2 (ICML 2025)](https://proceedings.mlr.press/v267/gutierrez25a.html), [LinearRAG (ICLR 2026)](https://proceedings.iclr.cc/paper_files/paper/2026/hash/ee1955739b91db042e659b6f782a5e79-Abstract-Conference.html), [RAG vs GraphRAG](https://arxiv.org/abs/2502.11371), [GraphRAG-Bench](https://arxiv.org/abs/2506.05690), [Scaling study July 2026](https://arxiv.org/abs/2607.26497), [Lightfoot (Nov 2026 preprint)](https://arxiv.org/abs/2611.11010). Recent results are task-specific, not a universal leaderboard. MIRA borrows dual-level retrieval, associative expansion, relation provenance and deterministic low-cost ingestion; does not reproduce these full algorithms.

## Implementation
- mira/retrieval.py: SQLite evidence/entity/directed edge schema, FTS5 BM25, exact typed identifier match, optional dense cosine search (float32 normalized vectors, NumPy acceleration if installed), RRF (k=60), bounded directed graph expansion, scope/freshness/verification filters, atomic evidence replacement and revocation, knowledge version and bounded context cards.
- mira/embedding.py: optional local multilingual E5 small adapter, 384 dimensions, CPU, query/passsage prefixes, pre-downloaded directory required, caller supplies pinned revision. No cloud calls. PyTorch/SentenceTransformer is the initial adapter, not a measured optimized ONNX implementation. Only embed reviewed evidence and sanitized risk queries; never raw traffic.
- tests/test_retrieval.py: synthetic oracle vectors validate data plumbing, not semantic accuracy; exact, lexical, semantic, graph, hybrid, scope, expiry, revocation, budgets.

Search modes: exact, lexical, semantic, hybrid (exact + lexical + dense), graph (exact + directed expansion), hybrid_graph (all). Dense and lexical lists are fused with reciprocal rank fusion; exact matches have priority and a separate direct_matches list independent of top_k. Graph expansion uses bounded breadth-first traversal, not Personalized PageRank or LightRAG's actual algorithm. Graph path contains supporting evidence IDs. For exact key matching, normalize domain IDNA/lowercase and CVE uppercase; canonicalize exact URL, origin and package+version in proxy normalizer before passing keys. This is not a full URL normalizer or version-range matcher. Scope means visibility workspace, not domain. Evidence attached to graph entities is not necessarily a direct match. Scope filtering is a single-workspace prototype, not enterprise multi-tenant isolation (FTS corpus statistics are shared).

Use KnowledgeStore.ingest only from trusted reviewed ingestion, never direct LLM or traffic output. Scope '*' represents explicitly public evidence. Use exact_keys only for source-verified applicability of the typed identifier, entities for associations, edges for directed relation facts. Every edge is backed by its evidence record, removed on revocation/replacement and filtered for verification, observation time and expiry. Missing/stale/partial semantic status and graph_truncated are visible. No authorization is inferred from a search hit or absence of a hit. Exact output must still be interpreted by independent scope/action policy. On required lookup failure or budget exhaustion, hold according to policy, not fail open.

## API integration (next step)
A proxy calls search with sanitized risk query, exact keys from canonicalized traffic features, workspace scope, now and policy-selected mode. Deterministic checks run on every required flow, then exact lookup (separate from top_k), then optional hybrid_graph for ambiguous supported content. Feed context_cards to Qwen classifier with actual tokenizer budget (max_chars is only a character bound). Validate output evidence IDs including graph path IDs as applicable. Do not allow model-generated graph writes or policy changes. Dynamic trust reads directly verified scoped records only, not relevance scores. Version-aware cache can be added once proxy exists; expire by earliest relevant evidence expiry and invalidate on revisions. Keep mandatory checks synchronous; graph retrieval and semantic CPU work off event loop with bounded queue. No live mitmproxy integration exists yet on this branch.

## Run
From repository root: python -m unittest discover -s tests -v
Exact/lexical/graph need Python 3.10+ and SQLite FTS5. Optional dense backend requires sentence-transformers and torch; optionally numpy for faster scan. Install reviewed/pinned compatible versions in a clean environment; download intfloat/multilingual-e5-small at a verified commit once, then mount local read-only directory. No auto-download at runtime. Model revision string is caller metadata; verify actual artifact hash in deployment. For old records ingested without embeddings, re-ingest reviewed evidence with the same ID and local encoder (including original keys/edges), or use future migration tooling; partial_index status is not full coverage.

Example:
```python
from mira.retrieval import Evidence, KnowledgeStore, context_cards
from mira.embedding import LocalE5
# Optional: encoder = LocalE5("/models/e5-small", revision="actual-pinned-revision")
store = KnowledgeStore("mira-knowledge.db")
store.ingest(Evidence("E1", "*", "Synthetic verified phishing indicator",
                      "fixture", 100, 9999999999),
             exact_keys=["domain:demo.example"],
             edges=[("domain:demo.example","MATCHES","threat:phishing")])
result = store.search("credential harvesting", keys=["domain:demo.example"],
                      scope="local", mode="hybrid_graph")
print(context_cards(result))
store.close()
```
Without encoder, hybrid gracefully reports semantic_status unavailable, not a fake semantic search. Semantic-only returns no results when unavailable. The prototype dense search uses capped exact cosine scan (not ANN); budget overflow is visible rather than silently truncating corpus. 384 float32 dims = 1536 bytes/vector before SQLite overhead; 10k vectors ~15.36 MB. No per-flow embeddings. Optimize ONNX/int8 and ANN/sqlite-vec only after measuring.

## Evaluation
Compare exact, BM25, dense, BM25+dense RRF, graph-only, hybrid_graph under same evidence snapshot, top-k and token budget. Stratify exact IDs, paraphrase, 1-hop/2-hop mitigation, ambiguous benign and expired/revoked/conflicting evidence. Measure recall@k, precision@k, MRR/nDCG, graph path support, direct-match false positives, retrieval p50/p95, memory, DB bytes, indexing/update cost and downstream Qwen F1/false holds. A real semantic evaluation needs actual E5 weights; fixture vectors are NOT benchmark results. Test hard policy never changes with semantic similarity, provenance, workspace visibility, cache invalidation and graph expansion budgets. Publish failures. No claim of superiority or latency measured yet.
