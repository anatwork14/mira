"""Optional local multilingual dense encoder. No downloads during runtime."""
from pathlib import Path


class LocalE5:
    def __init__(self, model_path, *, revision, threads=2):
        if not Path(model_path).is_dir() or not revision:
            raise ValueError("provide pre-downloaded model directory and pinned revision")
        from sentence_transformers import SentenceTransformer
        import torch
        torch.set_num_threads(threads)
        self.model_id="multilingual-e5-small@"+revision
        self.model=SentenceTransformer(str(model_path),device="cpu",local_files_only=True,trust_remote_code=False)
        self.model.max_seq_length=256

    def encode(self,text,*,query):
        prefix="query: " if query else "passage: "
        return self.model.encode(prefix+text,normalize_embeddings=True,show_progress_bar=False).tolist()
