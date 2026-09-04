import os
import faiss
import numpy as np
from typing import List, Dict, Optional
from google import genai
from google.genai import types

from .models import Runbook

class Retriever:
    def __init__(self, runbooks_dir: str):
        self.runbooks_dir = runbooks_dir
        self.runbooks: List[Runbook] = []
        self.index = None
        self.embeddings = []
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self._load_runbooks()

    def _load_runbooks(self):
        if not os.path.exists(self.runbooks_dir):
            return
            
        for fname in os.listdir(self.runbooks_dir):
            if fname.endswith(".md"):
                with open(os.path.join(self.runbooks_dir, fname), "r") as f:
                    content = f.read()
                    
                rb_id = fname.replace(".md", "")
                title = content.split("\n")[0].replace("# ", "").strip() if content.startswith("#") else rb_id
                
                self.runbooks.append(Runbook(
                    runbook_id=rb_id,
                    title=title,
                    content=content
                ))

    def _get_embedding(self, text: str) -> List[float]:
        if not self.client:
            # Fallback for testing without API key
            return [0.0] * 768
            
        response = self.client.models.embed_content(
            model='gemini-embedding-001',
            contents=text,
        )
        return response.embeddings[0].values

    def build_index(self):
        """Precomputes embeddings and builds FAISS index."""
        if not self.runbooks:
            return
            
        if self.index is not None:
            return # Already built
            
        dimension = 768  # gemini-embedding-001 dimension
        self.index = faiss.IndexFlatL2(dimension)
        
        vectors = []
        for rb in self.runbooks:
            emb = self._get_embedding(rb.content)
            vectors.append(emb)
            
        # Add to FAISS
        self.index.add(np.array(vectors, dtype=np.float32))

    def retrieve(self, query: str, top_k: int = 1) -> Optional[Runbook]:
        if not self.runbooks:
            return None
            
        if self.index is None:
            self.build_index()
            
        query_emb = self._get_embedding(query)
        distances, indices = self.index.search(np.array([query_emb], dtype=np.float32), top_k)
        
        idx = indices[0][0]
        distance = distances[0][0]
        
        # distance threshold check (if L2 distance is too high, it might not be a good match)
        # However, for a small hackathon dataset, we'll return the top match and let Gemini decide
        if idx >= 0 and idx < len(self.runbooks):
            return self.runbooks[idx]
            
        return None
