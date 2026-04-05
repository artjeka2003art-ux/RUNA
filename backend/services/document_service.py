"""Document ingestion service for sphere documents.

Extracts text from PDF, DOCX, TXT files. Stores metadata + extracted text in Redis.
Documents are optional precision boosters for prediction — never required.
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from io import BytesIO

logger = logging.getLogger(__name__)

# Max extracted text per document (chars) — keeps prompts manageable
_MAX_EXTRACT_LENGTH = 5000
_SUPPORTED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}
_EXTENSION_MIMES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def detect_mime(filename: str) -> str | None:
    """Detect MIME from extension."""
    for ext, mime in _EXTENSION_MIMES.items():
        if filename.lower().endswith(ext):
            return mime
    return None


def extract_text(content: bytes, mime_type: str) -> tuple[str, str]:
    """Extract text from document bytes.

    Returns (extracted_text, status).
    Status: 'processed' | 'limited' | 'failed'
    """
    try:
        if mime_type == "text/plain":
            return _extract_txt(content)
        elif mime_type == "application/pdf":
            return _extract_pdf(content)
        elif "wordprocessingml" in mime_type:
            return _extract_docx(content)
        else:
            return "", "failed"
    except Exception as e:
        logger.warning("Document extraction failed: %s", e, exc_info=True)
        return "", "failed"


def _extract_txt(content: bytes) -> tuple[str, str]:
    for encoding in ("utf-8", "cp1251", "latin-1"):
        try:
            text = content.decode(encoding)
            return _clean(text), "processed"
        except UnicodeDecodeError:
            continue
    return "", "failed"


def _extract_pdf(content: bytes) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("pypdf not installed — PDF extraction unavailable")
        return "", "failed"

    reader = PdfReader(BytesIO(content))
    pages_text = []
    for page in reader.pages[:50]:  # limit to 50 pages
        text = page.extract_text() or ""
        if text.strip():
            pages_text.append(text)

    if not pages_text:
        return "", "limited"

    full = "\n\n".join(pages_text)
    return _clean(full), "processed"


def _extract_docx(content: bytes) -> tuple[str, str]:
    try:
        from docx import Document
    except ImportError:
        logger.warning("python-docx not installed — DOCX extraction unavailable")
        return "", "failed"

    doc = Document(BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    if not paragraphs:
        return "", "limited"

    full = "\n".join(paragraphs)
    return _clean(full), "processed"


def _clean(text: str) -> str:
    """Clean and truncate extracted text."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", " ", text)
    return text.strip()[:_MAX_EXTRACT_LENGTH]


class DocumentStore:
    """Redis-backed document metadata + extracted text store."""

    def __init__(self, session_store):
        self.redis = session_store.redis

    def _key(self, user_id: str, sphere_id: str) -> str:
        return f"runa:docs:{user_id}:{sphere_id}"

    async def save_document(
        self,
        user_id: str,
        sphere_id: str,
        filename: str,
        mime_type: str,
        extracted_text: str,
        status: str,
    ) -> dict:
        """Save document metadata and extracted text. Returns the doc record."""
        doc = {
            "id": str(uuid.uuid4()),
            "sphere_id": sphere_id,
            "filename": filename,
            "mime_type": mime_type,
            "extracted_text": extracted_text,
            "status": status,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

        key = self._key(user_id, sphere_id)
        raw = await self.redis.get(key)
        docs = json.loads(raw) if raw else []
        docs.append(doc)
        await self.redis.set(key, json.dumps(docs, ensure_ascii=False))
        return doc

    async def get_documents(self, user_id: str, sphere_id: str) -> list[dict]:
        """Get all documents for a sphere."""
        key = self._key(user_id, sphere_id)
        raw = await self.redis.get(key)
        return json.loads(raw) if raw else []

    async def get_documents_for_spheres(
        self, user_id: str, sphere_ids: list[str],
    ) -> dict[str, list[dict]]:
        """Get documents for multiple spheres. Returns {sphere_id: [docs]}."""
        result = {}
        for sid in sphere_ids:
            docs = await self.get_documents(user_id, sid)
            if docs:
                result[sid] = docs
        return result

    async def delete_document(self, user_id: str, sphere_id: str, doc_id: str) -> bool:
        """Delete a document by ID."""
        key = self._key(user_id, sphere_id)
        raw = await self.redis.get(key)
        if not raw:
            return False
        docs = json.loads(raw)
        updated = [d for d in docs if d["id"] != doc_id]
        if len(updated) == len(docs):
            return False
        await self.redis.set(key, json.dumps(updated, ensure_ascii=False))
        return True
