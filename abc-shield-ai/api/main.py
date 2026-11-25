"""FastAPI application entrypoint for ABC Shield FinRegTech prototype.

Exposes the unified Task 9 StructuredAIResponse contract to backend (Vishal) and
frontend (Harshini) consumers with configurable CORS, health monitoring, and safe error handling.
Implements FastAPI lifespan management with SentenceTransformer startup warm-up.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from pathlib import Path
import sys

# Ensure project root is deterministically in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.routes.health import router as health_router
from api.routes.query import router as query_router, execute_query
from api.routes.compare import router as compare_router
from api.dependencies import get_grounded_generator
from rag.output.structured_response import StructuredAIResponse
from config.settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI application lifespan managing startup warm-up and graceful shutdown.

    Loads the SentenceTransformer model 'all-MiniLM-L6-v2' via EmbeddingManager during startup,
    executes a small warm-up embedding operation, verifies ChromaDB persistent vector store
    connectivity, and reuses the initialized singletons for subsequent requests.
    """
    logger.info("ABC Shield API lifespan startup: warming up SentenceTransformer model and RAG pipeline...")
    try:
        # 1. Initialize GroundedGenerator singleton (wires EmbeddingManager & ChromaVectorStore)
        gen = get_grounded_generator()

        # 2. Re-use existing EmbeddingManager to execute startup warm-up
        embedder = gen.retriever.embedding_manager
        warmup_text = "SentenceTransformer startup warm-up probe for ABC Shield regulatory RAG"
        warmup_vector = embedder.embed_text(warmup_text)
        dim = len(warmup_vector)

        logger.info(
            "SentenceTransformer warm-up complete: model='%s', dimension=%d (verified reuse ready)",
            embedder.model_name,
            dim,
        )

        # 3. Verify ChromaDB connectivity and vector store readiness
        store = gen.retriever.vector_store
        stats = store.get_collection_stats()
        vector_count = stats.get("total_vectors", 0)
        logger.info(
            "ChromaDB persistent store verified: collection='%s', vectors=%d at '%s'",
            store.collection_name,
            vector_count,
            store.persist_dir,
        )
    except Exception as exc:
        logger.exception("CRITICAL: Application lifespan startup warm-up failed: %s", exc)
        raise exc

    yield

    logger.info("ABC Shield API lifespan shutdown complete.")


# Initialize FastAPI application with comprehensive metadata and lifespan
app = FastAPI(
    title="ABC Shield FinRegTech API",
    description=(
        "Source-grounded regulatory intelligence and compliance engine for ABC Shield / FinRegTech ShipYard. "
        "Unifies semantic vector retrieval, grounded LLM generation, deterministic citations, evidence GAP handling, "
        "and conflict detection into a single stable REST API contract.\n\n"
        "**Legal Notice**: This system is a development prototype and provides source-grounded regulatory intelligence. "
        "It does not constitute formal legal advice. All current regulatory records are marked Candidate - Awaiting Approval."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
# Uses configured origins to allow frontend development without hardcoded wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(query_router)
app.include_router(compare_router)

# Register root-level fallback routes for Builder and Backend integration
app.add_api_route("/rag/analyze", execute_query, methods=["POST"], response_model=StructuredAIResponse, include_in_schema=False)
app.add_api_route("/analyze", execute_query, methods=["POST"], response_model=StructuredAIResponse, include_in_schema=False)


# Global unhandled exception handler ensuring no internal stack traces or secrets leak to clients
@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all exception handler preventing stack traces or filesystem paths from leaking."""
    logger.exception("Unhandled server exception processing path '%s': %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred. Please contact the administrator."
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
