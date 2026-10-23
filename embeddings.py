"""Embedding generator for regulatory chunks and queries.

Uses sentence-transformers locally with a configurable model (default: all-MiniLM-L6-v2).
No external API calls are made.
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages local dense embedding generation using sentence-transformers."""

    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

    _shared_models = {}

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = self._shared_models.get(model_name)

    def _get_model(self):
        """Lazy load the sentence-transformers model with process-level caching."""
        if self._model is None:
            if self.model_name in self._shared_models:
                self._model = self._shared_models[self.model_name]
                return self._model
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence-transformers model: %s", self.model_name)
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
                self._shared_models[self.model_name] = self._model
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is not installed. Please install with `pip install sentence-transformers`."
                ) from e
        return self._model

    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        model = self._get_model()
        if hasattr(model, "get_embedding_dimension"):
            dim = model.get_embedding_dimension()
        elif hasattr(model, "get_sentence_embedding_dimension"):
            dim = model.get_sentence_embedding_dimension()
        else:
            dim = None

        if dim is None:
            # Fallback test inference
            sample_emb = self.embed_text("test")
            return len(sample_emb)
        return int(dim)

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text string."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty or whitespace-only text.")
        model = self._get_model()
        embedding = model.encode(text.strip(), convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for a batch of text strings."""
        if not texts:
            return []
        cleaned_texts = [t.strip() if t and t.strip() else " " for t in texts]
        model = self._get_model()
        embeddings = model.encode(
            cleaned_texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return [emb.tolist() for emb in embeddings]
