"""MIRA retrieval core. Evidence discovery only; never grants authorization."""
from __future__ import annotations

import math
import re
import sqlite3
import struct
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Protocol

MODES = {"exact", "lexical", "semantic", "hybrid", "graph", "hybrid_graph"}
RELATIONS = {"MATCHES", "AFFECTS", "DESCRIBED_BY", "MITIGATED_BY", "RESTRICTED_BY", "RELATED_TO"}
GLOBAL = "*"


class Embedder(Protocol):
    model_id: str
    def encode(self, text: str, *, query: bool) -> list[float]: ...


@dataclass(frozen=True)
class Evidence:
    id: str
    scope: str
    text: str
    source: str
    observed_at: int
    expires_at: int
    verified: bool = True


def normalize_key(key: str) -> str:
    """Typed, exact identifiers. Caller must canonicalize URL/package identities."""
    kind, sep, value = key.partition(":")
    if not sep or kind not in {"domain", "url", "cve", "package", "policy", "indicator", "threat", "mitigation"} or not value:
        raise ValueError("expected typed identifier")
    if kind == "domain":
        value = value.rstrip(".").encode("idna").decode("ascii").lower()
    if kind == "cve":
        value = value.upper()
        if not re.fullmatch(r"CVE-\d{4}-\d{4,}", value):
            raise ValueError("invalid CVE identifier")
    return kind + ":" + value


def unit(values):
    values = [float(x) for x in values]
    if not values or len(values) > 4096 or not all(math.isfinite(x) for x in values):
        raise ValueError("invalid embedding")
    norm = math.sqrt(sum(x*x for x in values))
    if not norm or not math.isfinite(norm):
        raise ValueError("invalid embedding norm")
    return [x/norm for x in values]


def pack(values):
    return struct.pack("<" + "f"*len(values), *values)


def cosine(blob, vector):
    if len(blob) != 4*len(vector):
        raise ValueError("embedding dimension mismatch")
    return sum(a*b for a,b in zip(struct.unpack("<" + "f"*len(vector), blob), vector))


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS evidence(
 id TEXT PRIMARY KEY, scope TEXT NOT NULL, text TEXT NOT NULL, source TEXT NOT NULL,
 observed_at INTEGER NOT NULL, expires_at INTEGER NOT NULL, verified INTEGER NOT NULL,
 model_id TEXT, vector BLOB
);
CREATE INDEX IF NOT EXISTS ev_scope ON evidence(scope,verified,expires_at);
CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(id UNINDEXED,text,tokenize='unicode61');
CREATE TABLE IF NOT EXISTS entity(
 key TEXT NOT NULL, evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
 exact INTEGER NOT NULL, PRIMARY KEY(key,evidence_id)
);
CREATE INDEX IF NOT EXISTS entity_ev ON entity(evidence_id);
CREATE TABLE IF NOT EXISTS edge(
 src TEXT NOT NULL, dst TEXT NOT NULL, relation TEXT NOT NULL,
 evidence_id TEXT NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
 PRIMARY KEY(src,dst,relation,evidence_id)
);
CREATE INDEX IF NOT EXISTS edge_ev ON edge(evidence_id);
CREATE TABLE IF NOT EXISTS revision(id INTEGER PRIMARY KEY CHECK(id=1),version INTEGER NOT NULL);
INSERT OR IGNORE INTO revision VALUES(1,0);
"""


class KnowledgeStore:
    """Single-workspace SQLite store; use a single writer, separate reader connections."""

    def __init__(self, path=":memory:", embedder: Embedder | None = None):
        self.db = sqlite3.connect(path, timeout=3)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(SCHEMA)
        self.embedder = embedder

    def close(self):
        self.db.close()

    def ingest(self, ev: Evidence, *, exact_keys=(), entities=(), edges=()):
        """Trusted/reviewed ingestion only. Replace one evidence record atomically."""
        if not ev.id or not ev.scope or not ev.source or not ev.text or len(ev.text)>8192 or ev.observed_at>=ev.expires_at:
            raise ValueError("invalid evidence")
        exact = {normalize_key(k) for k in exact_keys}
        attached = {normalize_key(k) for k in entities} | exact
        relations = []
        for src, rel, dst in edges:
            if rel not in RELATIONS:
                raise ValueError("unsupported relation")
            src, dst = normalize_key(src), normalize_key(dst)
            relations.append((src,dst,rel,ev.id))
            attached.update((src,dst))
        if len(attached)>64 or len(relations)>64:
            raise ValueError("evidence graph budget exceeded")
        vector = pack(unit(self.embedder.encode(ev.text, query=False))) if self.embedder else None
        with self.db:
            self.db.execute("DELETE FROM evidence_fts WHERE id=?", (ev.id,))
            self.db.execute("DELETE FROM evidence WHERE id=?", (ev.id,))
            self.db.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?)",
                            (ev.id,ev.scope,ev.text,ev.source,ev.observed_at,ev.expires_at,int(ev.verified),
                             self.embedder.model_id if self.embedder else None,vector))
            self.db.execute("INSERT INTO evidence_fts VALUES(?,?)",(ev.id,ev.text))
            self.db.executemany("INSERT INTO entity VALUES(?,?,?)",
                                [(k,ev.id,int(k in exact)) for k in sorted(attached)])
            self.db.executemany("INSERT OR IGNORE INTO edge VALUES(?,?,?,?)",relations)
            self.db.execute("UPDATE revision SET version=version+1 WHERE id=1")

    def revoke(self, evidence_id):
        with self.db:
            self.db.execute("DELETE FROM evidence_fts WHERE id=?", (evidence_id,))
            self.db.execute("DELETE FROM evidence WHERE id=?", (evidence_id,))
            self.db.execute("UPDATE revision SET version=version+1 WHERE id=1")

    def search(self, query="", *, keys=(), scope, mode="hybrid_graph", top_k=5,
               now=None, hops=2, max_nodes=20, max_vector_rows=10000, min_cosine=0.0):
        """Read-only retrieval. Graph associations and similarity are not verified target matches."""
        if mode not in MODES or not scope or scope==GLOBAL or not 1<=top_k<=50 or not 0<=hops<=2 or not 1<=max_nodes<=100 or not 1<=max_vector_rows<=100000 or not -1<=min_cosine<=1:
            raise ValueError("invalid search settings")
        if len(query)>4096:
            raise ValueError("query exceeds budget")
        keys = sorted({normalize_key(k) for k in keys})
        if len(keys)>32:
            raise ValueError("too many keys")
        now = int(time.time()) if now is None else int(now)
        use_dense = mode in {"semantic","hybrid","hybrid_graph"}
        dense_status = "not_requested"
        vector = None
        if use_dense:
            if not query.strip():
                dense_status = "empty_query"
            elif not self.embedder:
                dense_status = "unavailable"
            else:
                try:
                    vector = unit(self.embedder.encode(query,query=True))
                    dense_status = "ready"
                except Exception:
                    dense_status = "unavailable"
        if mode=="semantic" and dense_status!="ready":
            return {"hits":[],"direct_matches":[],"semantic_status":dense_status,"graph_truncated":False,"version":None}
        with self.db:
            self.db.execute("BEGIN")
            return self._search(query,keys,scope,mode,top_k,now,hops,max_nodes,max_vector_rows,min_cosine,vector,dense_status)

    def _search(self, query, keys, scope, mode, top_k, now, hops, max_nodes, max_vector_rows, min_cosine, vector, dense_status):
        db=self.db
        version=db.execute("SELECT version FROM revision WHERE id=1").fetchone()[0]
        valid="e.verified=1 AND e.observed_at<=? AND e.expires_at>? AND e.scope IN (?, '*')"
        args=(now,now,scope)
        exact=[]
        matched=defaultdict(set)
        channels=defaultdict(set)
        ranks=defaultdict(float)
        paths=defaultdict(list)
        for key in keys:
            rows=db.execute("SELECT e.id FROM entity n JOIN evidence e ON e.id=n.evidence_id WHERE n.key=? AND n.exact=1 AND "+valid+" ORDER BY e.id LIMIT 101",(key,*args)).fetchall()
            if len(rows)>100:
                raise RuntimeError("exact match budget exceeded")
            for row in rows:
                eid=row[0]
                matched[eid].add(key)
                if eid not in exact:
                    exact.append(eid)
        if mode not in {"lexical","semantic"}:
            for eid in exact:
                channels[eid].add("exact")
        def fuse(ids,name):
            for rank,eid in enumerate(ids,1):
                channels[eid].add(name)
                ranks[eid]+=1/(60+rank)
        limit=max(20,top_k*4)
        if mode in {"lexical","hybrid","hybrid_graph"}:
            terms=re.findall(r"[^\W_]+",query.lower(),re.UNICODE)[:32]
            if terms:
                expression=" OR ".join('"'+t+'"' for t in dict.fromkeys(terms))
                rows=db.execute("SELECT e.id FROM evidence_fts JOIN evidence e ON e.id=evidence_fts.id WHERE evidence_fts MATCH ? AND "+valid+" ORDER BY bm25(evidence_fts),e.id LIMIT ?",(expression,*args,limit))
                fuse([r[0] for r in rows],"lexical")
        if vector is not None:
            rows=db.execute("SELECT e.id,e.vector FROM evidence e WHERE "+valid+" AND e.model_id=? AND e.vector IS NOT NULL LIMIT ?",(*args,self.embedder.model_id,max_vector_rows+1)).fetchall()
            if len(rows)>max_vector_rows:
                dense_status="budget_exceeded"
            elif not rows:
                dense_status="index_empty"
            else:
                try:
                    try:
                        import numpy as np
                    except ImportError:
                        np=None
                    if np is not None:
                        if any(len(r["vector"])!=4*len(vector) for r in rows):
                            raise ValueError("embedding dimension mismatch")
                        matrix=np.frombuffer(b"".join(r["vector"] for r in rows),dtype="<f4").reshape(len(rows),len(vector))
                        scores=matrix @ np.asarray(vector,dtype=np.float32)
                        scored=[(float(score),r["id"]) for score,r in zip(scores,rows)]
                    else:
                        scored=[(cosine(r["vector"],vector),r["id"]) for r in rows]
                    scored.sort(key=lambda x:(-x[0],x[1]))
                    fuse([eid for score,eid in scored if score>=min_cosine][:limit],"semantic")
                    total=db.execute("SELECT COUNT(*) FROM evidence e WHERE "+valid,args).fetchone()[0]
                    dense_status="ready" if total==len(rows) else "partial_index"
                except ValueError:
                    dense_status="index_incompatible"
        truncated=False
        if mode in {"graph","hybrid_graph"}:
            seeds=list(keys)
            for eid in sorted(ranks,key=lambda x:(-ranks[x],x))[:5]:
                for row in db.execute("SELECT key FROM entity WHERE evidence_id=? ORDER BY key LIMIT 5",(eid,)):
                    if row[0] not in seeds:
                        seeds.append(row[0])
            seen=set(seeds[:max_nodes])
            truncated=len(seeds)>max_nodes
            queue=deque((k,[]) for k in seeds[:max_nodes])
            while queue:
                node,path=queue.popleft()
                attached=db.execute("SELECT e.id FROM entity n JOIN evidence e ON e.id=n.evidence_id WHERE n.key=? AND "+valid+" ORDER BY e.id LIMIT 21",(node,*args)).fetchall()
                truncated|=len(attached)>20
                for row in attached[:20]:
                    eid=row[0]
                    channels[eid].add("graph")
                    if path and not paths[eid]:
                        paths[eid]=path
                    ranks[eid]=max(ranks[eid],0.008/(1+len(path)))
                if len(path)>=hops:
                    continue
                adj=db.execute("SELECT x.src,x.dst,x.relation,x.evidence_id FROM edge x JOIN evidence e ON e.id=x.evidence_id WHERE x.src=? AND "+valid+" ORDER BY x.dst,x.relation,x.evidence_id LIMIT 21",(node,*args)).fetchall()
                truncated|=len(adj)>20
                for row in adj[:20]:
                    nxt=row["dst"]
                    if nxt in seen:
                        continue
                    if len(seen)>=max_nodes:
                        truncated=True
                        continue
                    seen.add(nxt)
                    queue.append((nxt,path+[dict(row)]))
        ordered=sorted(channels,key=lambda eid:(0 if "exact" in channels[eid] else 1,-ranks[eid],eid))
        hits=[]
        for eid in ordered[:top_k]:
            ev=db.execute("SELECT id,scope,text,source,observed_at,expires_at FROM evidence WHERE id=?",(eid,)).fetchone()
            hits.append({**dict(ev),"channels":sorted(channels[eid]),"exact_keys":sorted(matched[eid]) if "exact" in channels[eid] else [],
                         "graph_path":paths[eid],"rank_score":ranks[eid]})
        # Exact matches are returned separately and never silently truncated by top_k.
        direct=[{"id":eid,"keys":sorted(matched[eid])} for eid in exact] if mode not in {"lexical","semantic"} else []
        return {"hits":hits,"direct_matches":direct,"semantic_status":dense_status,"graph_truncated":bool(truncated),"version":version}


def context_cards(result, *, max_chars=1200):
    """Bounded evidence context; caller must enforce actual Qwen token budget."""
    import json
    cards=[]
    for hit in result["hits"]:
        card={"id":hit["id"],"scope":hit["scope"],"fact":hit["text"],"source":hit["source"],
              "channels":hit["channels"],"exact_keys":hit["exact_keys"],"path":hit["graph_path"]}
        candidate=json.dumps(cards+[card],ensure_ascii=False,separators=(",",":"))
        if len(candidate)<=max_chars:
            cards.append(card)
    return cards
