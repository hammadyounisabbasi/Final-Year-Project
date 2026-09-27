"""Scoped retrieval for administrator timetable references.

The scheduler never reads a vector hit as a production record.  This module
stores extracted *text* with provenance and offers grounded, metadata-filtered
retrieval to the agent.  The embedding interface is deliberately independent
of the on-disk store so a hosted embedding provider or FAISS adapter can be
introduced without changing timetable planning.
"""
from __future__ import annotations

import hashlib
import math
import os
import re
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Protocol
from dotenv import load_dotenv


# Resolve the repository configuration independently of the backend process
# working directory. Externally supplied variables keep precedence.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(PROJECT_ROOT / '.env', override=False)


class EmbeddingProvider(Protocol):
    name: str
    def embed(self, text: str) -> list[float]: ...


class LocalHashEmbedding:
    """Deterministic local embedding for development with no model download."""
    name = 'local-hash-v1'
    dimensions = 256

    def embed(self, text: str) -> list[float]:
        values = [0.0] * self.dimensions
        tokens = re.findall(r"[a-z0-9][a-z0-9_-]{1,}", text.casefold())
        for token, count in Counter(tokens).items():
            digest = hashlib.blake2b(token.encode(), digest_size=4).digest()
            index = int.from_bytes(digest, 'big') % self.dimensions
            values[index] += float(count)
        length = math.sqrt(sum(v * v for v in values))
        return [v / length for v in values] if length else values


def embedding_provider() -> EmbeddingProvider:
    # Configuration is an interface contract.  A non-local provider may be
    # installed later; local retrieval remains available and deterministic.
    configured = os.getenv('TIMETABLE_EMBEDDING_PROVIDER', 'local-hash').casefold()
    model = os.getenv('TIMETABLE_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    return _provider_for(configured, model)


class SentenceTransformerEmbedding:
    """Optional local semantic model; loaded only when explicitly configured."""
    name = 'sentence-transformers'
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        started = time.perf_counter()
        self.model_name = model_name
        # The installed runtime is CPU-only. Specify it to avoid device probing.
        # Timetable chat must not stall while a model registry is unavailable.
        # Administrators may pre-cache a semantic model; otherwise the caller
        # immediately falls back to the deterministic local hash provider.
        self.model = SentenceTransformer(model_name, device='cpu', local_files_only=True)
        logging.getLogger(__name__).info('Loaded timetable embedding model %s on CPU in %.3fs', model_name, time.perf_counter() - started)
    def embed(self, text: str) -> list[float]:
        started = time.perf_counter()
        vector = self.model.encode(text, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False).tolist()
        logging.getLogger(__name__).debug('Embedded timetable text with %s in %.3fs', self.model_name, time.perf_counter() - started)
        return vector


@lru_cache(maxsize=4)
def _provider_for(configured: str, model: str) -> EmbeddingProvider:
    """One lazily initialized provider per process/configuration pair."""
    if configured in ('sentence-transformers', 'sentence_transformers', 'semantic', 'local-semantic'):
        try:
            return SentenceTransformerEmbedding(model)
        except (ImportError, OSError, RuntimeError) as error:
            logging.getLogger(__name__).warning('Semantic timetable embeddings unavailable (%s); using local hash fallback.', error)
    return LocalHashEmbedding()


def _chunks(text: str, size: int = 900, overlap: int = 140):
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = text.rfind('\n', start + size // 2, end)
            if boundary > start: end = boundary
        value = text[start:end].strip()
        if value: yield value
        if end >= len(text): break
        start = max(end - overlap, start + 1)


def _score(query: list[float], value: list[float]) -> float:
    return sum(a * b for a, b in zip(query, value))


def index_document(state: dict, text: str, metadata: dict) -> tuple[dict, list[dict]]:
    """Add a deduplicated reference to conversation-scoped knowledge."""
    provider = embedding_provider()
    source_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
    knowledge = dict(state.get('knowledge_index') or {})
    documents = list(knowledge.get('documents') or [])
    if any(doc.get('hash') == source_hash for doc in documents):
        return state, []
    source = {
        'id': source_hash[:16], 'hash': source_hash,
        'filename': metadata.get('filename') or 'chat-reference.txt',
        'source_type': metadata.get('source_type') or 'text',
        'session_id': metadata.get('session_id'),
        'document_category': metadata.get('document_category') or 'timetable-reference',
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    chunks = list(knowledge.get('chunks') or [])
    created = []
    for number, content in enumerate(_chunks(text), 1):
        record = {'id': f"{source['id']}:{number}", 'source_id': source['id'], 'chunk': number,
                  'text': content, 'embedding': provider.embed(content), 'metadata': source}
        chunks.append(record)
        created.append({'id': record['id'], 'filename': source['filename'], 'chunk': number})
    knowledge.update(provider=provider.name, documents=documents + [source], chunks=chunks[-500:])
    knowledge['structured'] = normalize_relationships(knowledge.get('structured') or {}, text, source)
    state = dict(state); state['knowledge_index'] = knowledge
    return state, created


def canonical(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', value.casefold()).strip()


def _fact(value: dict, source: dict, confidence: float = 1.0):
    return {**value, 'confidence': confidence, 'provenance': {
        'source_file': source['filename'], 'source_type': source['source_type'],
        'source_id': source['id'], 'timestamp': source['timestamp']}}


def _add(items: list, item: dict, keys: tuple[str, ...]):
    if not any(all(existing.get(key) == item.get(key) for key in keys) for existing in items): items.append(item)


def normalize_relationships(structured: dict, text: str, source: dict) -> dict:
    """Extract explicit reusable timetable facts from any extracted text.

    This is deliberately relationship-oriented: it handles narrative blocks and
    ordinary spreadsheet rows, and never asserts a relation without source text.
    """
    data = {key: list(value) for key, value in structured.items()} if structured else {}
    for key in ('teachers','courses','rooms','departments','semesters','sections','teacher_course_assignments',
                'teacher_availability','teacher_soft_preferences','course_characteristics','course_room_preferences',
                'room_capabilities','scheduling_constraints'):
        data.setdefault(key, [])
    department = None; semester = None; current_teacher = None
    lines = [line.strip(' \t•-') for line in text.splitlines() if line.strip()]
    for row, line in enumerate(lines, 1):
        evidence = {**source, 'row': row}
        match = re.search(r'\bdepartment\s*:\s*(.+)', line, re.I)
        if match:
            department = match[1].strip(); _add(data['departments'], _fact({'name': department}, evidence), ('name',)); continue
        match = re.search(r'\bsemester\s*:?\s*(\d+)', line, re.I)
        if match:
            semester = int(match[1]); _add(data['semesters'], _fact({'number': semester}, evidence), ('number',)); continue
        teacher = re.fullmatch(r'((?:Dr|Prof|Mr|Ms|Mrs)\.?\s+[A-Za-z][A-Za-z .\'-]+)\s*:?', line, re.I)
        if teacher:
            current_teacher = teacher[1].strip(); _add(data['teachers'], _fact({'name': current_teacher, 'key': canonical(current_teacher)}, evidence), ('key',)); continue
        table = [part.strip() for part in line.split('|')]
        if len(table) >= 2 and re.match(r'^(?:Dr|Prof|Mr|Ms|Mrs)\.?\s+', table[0], re.I):
            current_teacher = table[0]
            _add(data['teachers'], _fact({'name': current_teacher, 'key': canonical(current_teacher)}, evidence), ('key',))
            for course in re.split(r'[,;/]', table[1]):
                if course.strip(): _add(data['teacher_course_assignments'], _fact({'teacher': current_teacher, 'course': course.strip(), 'course_key': canonical(course)}, evidence), ('teacher','course_key'))
            if len(table) > 2: line = f'{current_teacher} available {table[2]}'
            if len(table) > 3: line += f'; {table[3]}'
        course = re.match(r'([A-Za-z]{2,}[ -]?\d[\w-]*)\s*[-—–:]?\s*(.+?)\s+(\d+)\s*(?:CH|credit hours?)\b', line, re.I)
        if course:
            item = {'code': course[1], 'name': course[2].strip(' -—–'), 'key': canonical(course[2]), 'credit_hours': int(course[3]), 'department': department, 'semester': semester}
            _add(data['courses'], _fact(item, evidence), ('code',)); continue
        teaches = re.search(r'\bteaches?\s+(.+)', line, re.I)
        if current_teacher and teaches:
            for course_name in re.split(r'[,;/]|\band\b', teaches[1], flags=re.I):
                if course_name.strip(): _add(data['teacher_course_assignments'], _fact({'teacher': current_teacher, 'course': course_name.strip(), 'course_key': canonical(course_name)}, evidence), ('teacher','course_key'))
        availability = re.search(r'\bavailable\s+(.+)', line, re.I)
        if current_teacher and availability:
            fragment = availability[1]
            days = re.findall(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', fragment, re.I)
            range_match = re.search(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(?:to|through|[-–])\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', fragment, re.I)
            ordered = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            if range_match:
                a,b = range_match[1].title(), range_match[2].title(); days = ordered[ordered.index(a):ordered.index(b)+1]
            if days: _add(data['teacher_availability'], _fact({'teacher': current_teacher, 'days': [day.title() for day in days]}, evidence), ('teacher',))
        preference = re.search(r'\bprefer(?:s|red)?\s+(?:morning|earlier(?:\s+in\s+the\s+day)?)', line, re.I)
        if current_teacher and preference:
            _add(data['teacher_soft_preferences'], _fact({'teacher': current_teacher, 'preference_type': 'preferred_time_range', 'value': 'morning', 'priority': 'soft'}, evidence), ('teacher','preference_type'))
        if re.search(r'\b(?:practical|computing[- ]heavy)\s+courses?\s+(?:should\s+)?prefer\s+labs?\b', line, re.I):
            _add(data['course_room_preferences'], _fact({'condition': 'computing_heavy_or_practical', 'preferred_room_capability': 'lab', 'priority': 'soft'}, evidence), ('condition','preferred_room_capability'))
        if re.search(r'\b(?:must|never)\s+(?:overlap|conflict)\b|shared teachers?\s+must\s+never\s+overlap', line, re.I):
            _add(data['scheduling_constraints'], _fact({'rule': 'shared_teacher_no_overlap', 'priority': 'hard'}, evidence), ('rule',))
        room = re.fullmatch(r'([A-Za-z][A-Za-z0-9 &-]*(?:Lab|Room\s*\d+))', line, re.I)
        if room:
            name = room[1]; _add(data['rooms'], _fact({'name': name, 'key': canonical(name)}, evidence), ('key',))
            capabilities = ['lab'] if re.search(r'\blab\b', name, re.I) else ['classroom']
            _add(data['room_capabilities'], _fact({'room': name, 'capabilities': capabilities, 'heuristic': True}, evidence, .75), ('room',))
    return data


def resolve_teacher(structured: dict, reference: str) -> dict | None:
    key = canonical(reference)
    matches = [teacher for teacher in structured.get('teachers', []) if teacher['key'] == key or key in teacher['key'].split()]
    return matches[0] if len(matches) == 1 else None


def relationship_answer(structured: dict, query: str) -> dict | None:
    """Answer relationship questions from normalized facts rather than chunks."""
    teachers = structured.get('teachers', []); assignments = structured.get('teacher_course_assignments', [])
    query_key = canonical(query)
    named = next((teacher for teacher in teachers if teacher['key'] in query_key or any(part in query_key.split() for part in teacher['key'].split() if len(part) > 3)), None)
    ai_aliases = {course['key'] for course in structured.get('courses', []) if ''.join(part[0] for part in course['key'].split() if part) in query_key.split()}
    if named and re.search(r'\b(?:which|what).*(?:course|related)\b', query, re.I):
        courses = [item['course'] for item in assignments if canonical(item['teacher']) == named['key']]
        return {'kind':'teacher_courses','teacher':named['name'],'courses':courses,'provenance':[item['provenance'] for item in assignments if canonical(item['teacher']) == named['key']]}
    if re.search(r'\b(?:who|which teacher)\b', query, re.I) and (ai_aliases or 'ai related' in query.casefold()):
        scored = [(sum(item['course_key'] in ai_aliases or 'artificial intelligence' in item['course_key'] for item in assignments if canonical(item['teacher']) == teacher['key']), teacher) for teacher in teachers]
        score, teacher = max(scored, default=(0,None), key=lambda item:item[0])
        if score: return {'kind':'ai_teacher','teacher':teacher['name'],'count':score,'provenance':[item['provenance'] for item in assignments if canonical(item['teacher']) == teacher['key']]}
    return None


def retrieve(state: dict, query: str, filters: dict | None = None, top_k: int = 6) -> list[dict]:
    """Return only relevant, deduplicated chunks with source provenance."""
    knowledge = state.get('knowledge_index') or {}
    chunks = knowledge.get('chunks') or []
    if not query.strip() or not chunks: return []
    filters = {k: str(v).casefold() for k, v in (filters or {}).items() if v not in (None, '')}
    provider = embedding_provider(); query_embedding = provider.embed(query)
    seen, ranked = set(), []
    for record in chunks:
        metadata = record.get('metadata', {})
        if any(str(metadata.get(key, '')).casefold() != value for key, value in filters.items()): continue
        text_key = re.sub(r'\s+', ' ', record.get('text', '').casefold())
        if text_key in seen: continue
        seen.add(text_key)
        score = _score(query_embedding, record.get('embedding', []))
        if score > 0:
            ranked.append((score, record))
    return [dict(id=record['id'], text=record['text'], score=round(score, 4),
                 source={k: record['metadata'].get(k) for k in ('filename','source_type','document_category','timestamp')})
            for score, record in sorted(ranked, key=lambda item: item[0], reverse=True)[:top_k]]
