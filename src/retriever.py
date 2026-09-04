import os
import faiss
import numpy as np
import logging
from typing import List, Optional
from google import genai

from .models import Runbook

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, runbooks_dir: str):
        self.runbooks_dir = runbooks_dir
        self.runbooks: List[Runbook] = []
        self.index = None
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

        self._load_runbooks()

    def _load_runbooks(self):
        if not os.path.exists(self.runbooks_dir):
            return

        for fname in sorted(os.listdir(self.runbooks_dir)):  # sorted for determinism
            if fname.endswith(".md"):
                with open(os.path.join(self.runbooks_dir, fname), "r") as f:
                    content = f.read()

                rb_id = fname.replace(".md", "")
                title = (
                    content.split("\n")[0].replace("# ", "").strip()
                    if content.startswith("#")
                    else rb_id
                )

                self.runbooks.append(
                    Runbook(runbook_id=rb_id, title=title, content=content)
                )

    def _get_embedding(self, text: str) -> List[float]:
        """
        Return a plain Python list of floats.

        If no API key is present (e.g. test environment) we return an empty list
        so the caller knows not to use the value for a real FAISS index.  A non-empty
        fallback with a *fixed* dimension was the original source of the mismatch.
        """
        if not self.client:
            # No API key — signal 'no real embedding available'
            return []

        response = self.client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
        )
        # Explicitly convert the protobuf container to a plain Python list of floats
        # so that np.array() produces a clean 2-D float32 matrix, not an object array.
        return list(response.embeddings[0].values)

    def build_index(self):
        """
        Embed every runbook and build a fresh FAISS index.

        The FAISS index dimension is set from the *actual* embedding dimension
        returned by the first successful Gemini call — never hardcoded.

        If there is no API key the index is left as None so that retrieve()
        can return None gracefully instead of crashing.
        """
        if not self.runbooks:
            return

        # Always rebuild — callers explicitly call build_index() when they
        # want a fresh index (e.g. after a dimension mismatch is detected).
        self.index = None

        vectors: List[List[float]] = []
        for rb in self.runbooks:
            emb = self._get_embedding(rb.content)
            if not emb:
                # No API key or empty response — cannot build a real index
                print("[Retriever] No embedding returned — skipping index build (no API key?)")
                return
            vectors.append(emb)

        # ── Diagnostic logging (safe — no keys or content) ──────────────────
        dim = len(vectors[0])
        n_vecs = len(vectors)
        print(f"[Retriever] embedding dimension returned : {dim}")
        print(f"[Retriever] number of vectors            : {n_vecs}")
        # ────────────────────────────────────────────────────────────────────

        # Validate: every vector must have exactly the same dimension
        bad = [i for i, v in enumerate(vectors) if len(v) != dim]
        if bad:
            raise RuntimeError(
                f"[Retriever] Inconsistent embedding dimensions at positions {bad}. "
                f"Expected {dim}, got {[len(vectors[i]) for i in bad]}."
            )

        # Build a brand-new FAISS index using the real dimension
        self.index = faiss.IndexFlatL2(dim)
        print(f"[Retriever] FAISS index dimension        : {self.index.d}")

        # Convert to a proper 2-D float32 numpy matrix row-by-row to be safe
        matrix = np.array(vectors, dtype=np.float32)   # shape (n_vecs, dim)
        assert matrix.shape == (n_vecs, dim), (
            f"[Retriever] numpy matrix shape {matrix.shape} != ({n_vecs}, {dim})"
        )
        self.index.add(matrix)

    def retrieve(self, query: str, top_k: int = 1) -> Optional[Runbook]:
        if not self.runbooks:
            return None

        # Build the index on first use if not already built
        if self.index is None:
            self.build_index()

        # If still None (no API key / no embeddings), return None gracefully
        if self.index is None:
            return self.runbooks[0] if self.runbooks else None

        query_emb = self._get_embedding(query)
        if not query_emb:
            # No API key — fall back to first runbook
            return self.runbooks[0] if self.runbooks else None

        query_list = list(query_emb)   # ensure plain list

        # ── Dimension guard: rebuild if Gemini's dimension changed ───────────
        if len(query_list) != self.index.d:
            print(
                f"[Retriever] Query embedding dim ({len(query_list)}) != "
                f"index dim ({self.index.d}). Rebuilding index."
            )
            self.build_index()
            if self.index is None:
                return self.runbooks[0] if self.runbooks else None
        # ─────────────────────────────────────────────────────────────────────

        query_matrix = np.array([query_list], dtype=np.float32)   # shape (1, dim)
        distances, indices = self.index.search(query_matrix, top_k)

        idx = int(indices[0][0])
        if 0 <= idx < len(self.runbooks):
            return self.runbooks[idx]

        return None
