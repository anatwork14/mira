import unittest
from mira.retrieval import Evidence, KnowledgeStore, context_cards

NOW=1000

class FixtureEncoder:
    model_id="fixture-only-v1"
    def encode(self,text,*,query):
        # Synthetic vector oracle for wiring tests, NOT a real semantic model.
        return [1,0] if any(x in text.lower() for x in ("credential","password","secret")) else [0,1]

class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.s=KnowledgeStore(embedder=FixtureEncoder())
        def ev(i,text,scope="*",expiry=2000,verified=True):
            return Evidence(i,scope,text,"synthetic",1,expiry,verified)
        self.s.ingest(ev("a","Credential exposure"),exact_keys=["domain:bad.example"],
                      edges=[("domain:bad.example","MATCHES","threat:campaign")])
        self.s.ingest(ev("b","Rotate keys and revoke access"),
                      edges=[("threat:campaign","MITIGATED_BY","mitigation:rotate")])
        self.s.ingest(ev("c","Password disclosure prevention"),entities=["mitigation:rotate"])
        self.s.ingest(ev("d","Credential private scope",scope="other"),exact_keys=["domain:bad.example"])
        self.s.ingest(ev("e","Credential expired",expiry=999),exact_keys=["domain:bad.example"])
        self.s.ingest(ev("f","Credential unverified",verified=False),exact_keys=["domain:bad.example"])
    def tearDown(self):
        self.s.close()
    def q(self,mode,**kwargs):
        return self.s.search(scope="demo",mode=mode,now=NOW,**kwargs)
    def test_exact_scope_and_expiry(self):
        r=self.q("exact",keys=["domain:BAD.EXAMPLE."])
        self.assertEqual([h["id"] for h in r["hits"]],["a"])
        self.assertEqual(r["direct_matches"],[{"id":"a","keys":["domain:bad.example"]}])
        self.assertFalse(self.q("exact",keys=["domain:notbad.example"])["hits"])
    def test_lexical(self):
        self.assertEqual(self.q("lexical",query="rotate")["hits"][0]["id"],"b")
        self.q("lexical",query='") OR *')
    def test_semantic_fixture(self):
        ids=[x["id"] for x in self.q("semantic",query="secret",min_cosine=.5)["hits"]]
        self.assertEqual(ids,["a","c"])
    def test_graph_multihop_provenance(self):
        r=self.q("graph",keys=["domain:bad.example"])
        hits={h["id"]:h for h in r["hits"]}
        self.assertEqual(set(hits),{"a","b","c"})
        self.assertEqual(len(hits["c"]["graph_path"]),2)
        self.assertEqual(hits["c"]["exact_keys"],[])
        self.assertNotIn("d",hits)
    def test_hybrid_exact_priority(self):
        r=self.q("hybrid_graph",keys=["domain:bad.example"],query="password",top_k=1)
        self.assertEqual(r["hits"][0]["id"],"a")
        self.assertTrue(context_cards(r))
    def test_revocation_and_replacement(self):
        before=self.q("graph",keys=["domain:bad.example"])
        self.s.revoke("b")
        r=self.q("graph",keys=["domain:bad.example"])
        self.assertGreater(r["version"],before["version"])
        self.assertNotIn("c",[h["id"] for h in r["hits"]])
        self.s.ingest(Evidence("a","*","new fact","synthetic",1,2000))
        self.assertFalse(self.q("exact",keys=["domain:bad.example"])["hits"])
    def test_budget_and_missing_encoder(self):
        self.assertTrue(self.q("graph",keys=["domain:bad.example"],max_nodes=1)["graph_truncated"])
        self.s.embedder=None
        self.assertEqual(self.q("semantic",query="secret")["semantic_status"],"unavailable")
        self.assertTrue(self.q("hybrid",query="credential")["hits"])
    def test_future_evidence(self):
        self.s.ingest(Evidence("future","*","future","synthetic",1500,2000),exact_keys=["domain:bad.example"])
        self.assertNotIn("future",[h["id"] for h in self.q("exact",keys=["domain:bad.example"])["hits"]])

if __name__=="__main__":
    unittest.main()
