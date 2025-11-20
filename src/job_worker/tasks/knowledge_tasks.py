"""Knowledge base ingestion tasks

Background tasks for processing document uploads and maintaining the knowledge base.
"""

import logging
from typing import Dict, Any

from job_worker.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True, name="job_worker.tasks.knowledge_tasks.ingest_document")
def ingest_document(
    self,
    document_id: str,
    content: str,
    title: str,
    document_type: str,
    category: str = None,
    tags: list = None,
    source_url: str = None,
    description: str = None,
) -> Dict[str, Any]:
    """
    Process document upload and generate embeddings for ChromaDB storage.

    Args:
        document_id: Unique document identifier
        content: Document text content
        title: Document title
        document_type: Type (playbook, troubleshooting_guide, reference, how_to)
        category: Optional category
        tags: Optional list of tags
        source_url: Optional source URL
        description: Optional description

    Returns:
        Task result with status and document_id
    """
    logger.info(f"Starting document ingestion: {document_id}")

    try:
        # Import here to avoid circular dependencies
        from knowledge_service.core.knowledge.ingestion import KnowledgeIngester

        ingester = KnowledgeIngester()

        # Process document
        result = ingester.ingest_document(
            document_id=document_id,
            content=content,
            title=title,
            document_type=document_type,
            category=category,
            tags=tags or [],
            source_url=source_url,
            description=description,
        )

        logger.info(f"Document ingestion completed: {document_id}")
        return {
            "status": "completed",
            "document_id": document_id,
            "chunks_created": result.get("chunks_created", 0),
        }

    except Exception as e:
        logger.error(f"Document ingestion failed: {document_id} - {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries), max_retries=3)


@app.task(name="job_worker.tasks.knowledge_tasks.update_embeddings")
def update_embeddings(collection_name: str) -> Dict[str, Any]:
    """
    Rebuild embeddings for a knowledge base collection.

    Args:
        collection_name: ChromaDB collection to update

    Returns:
        Task result with count of updated embeddings
    """
    logger.info(f"Updating embeddings for collection: {collection_name}")

    try:
        from knowledge_service.infrastructure.knowledge.runbook_kb import RunbookKB

        kb = RunbookKB()
        # Logic to rebuild embeddings would go here
        # This is a placeholder for the actual implementation

        logger.info(f"Embeddings updated for collection: {collection_name}")
        return {
            "status": "completed",
            "collection_name": collection_name,
        }

    except Exception as e:
        logger.error(f"Embedding update failed: {collection_name} - {str(e)}")
        raise
