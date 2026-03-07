# encoding: utf-8
# Memory Layer（v1）
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence
import hashlib
import json
import math
import re
import time

try:
    import redis
except Exception:  # pragma: no cover - 允许在无 redis 环境下回退到内存模式
    redis = None


EntityExtractor = Callable[[str], Sequence[Dict[str, Any]]]

ENTITY_ALIAS_MATCH_WEIGHT = 0.35
ENTITY_TOKEN_OVERLAP_WEIGHT = 0.20
ENTITY_RECENCY_WEIGHT = 0.15
ENTITY_CONFIDENCE_WEIGHT = 0.15
ENTITY_STABILITY_WEIGHT = 0.10
ENTITY_SOURCE_DIVERSITY_WEIGHT = 0.05

DEFAULT_STABLE_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

_LOW_SIGNAL_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "model",
    "paper",
    "method",
    "system",
    "agent",
    "score",
    "query",
    "answer",
    "问题",
    "方法",
    "模型",
    "系统",
    "实验",
    "结果",
}


@dataclass
class MemoryItem:
    content: str
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRecord:
    entity_id: str
    canonical_name: str
    entity_type: str = "unknown"
    aliases: List[str] = field(default_factory=list)
    confidence: float = 0.5
    occurrence_count: int = 0
    stable_occurrence_count: int = 0
    last_seen: float = field(default_factory=time.time)
    source_counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRecallHit:
    entity_id: str
    canonical_name: str
    score: float
    breakdown: Dict[str, float] = field(default_factory=dict)


class MemoryLayer:
    def __init__(
        self,
        max_short: int = 50,
        use_redis: bool = False,
        redis_url: Optional[str] = None,
        session_id: str = "default",
        llm_entity_extractor: Optional[EntityExtractor] = None,
        stable_confidence_threshold: float = DEFAULT_STABLE_CONFIDENCE_THRESHOLD,
    ):
        self.max_short = max_short
        self.session_id = session_id
        self.short_term: List[MemoryItem] = []
        self.long_term: List[MemoryItem] = []

        self.entity_store: Dict[str, EntityRecord] = {}
        self.alias_to_entity: Dict[str, str] = {}
        self.entity_observation_log: List[Dict[str, Any]] = []
        self._stable_observation_keys: Dict[str, set[str]] = {}

        self.llm_entity_extractor = llm_entity_extractor
        self.stable_confidence_threshold = stable_confidence_threshold

        self.redis_client = self._build_redis_client(redis_url) if use_redis else None

    def write(
        self,
        content: str,
        scope: str = "short",
        source: str = "unknown",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        item_metadata = dict(metadata or {})
        item = MemoryItem(
            content=content,
            source=source,
            tags=list(tags or []),
            metadata=item_metadata,
        )

        if scope == "long":
            self.long_term.append(item)
        else:
            self.short_term.append(item)
            if len(self.short_term) > self.max_short:
                self.short_term.pop(0)

        if item.metadata.get("extract_entities", True):
            content_hash = self._sha1(content)
            extracted = self.extract_entities(content)
            item.metadata["extracted_entities"] = [e["canonical_name"] for e in extracted]
            for entity in extracted:
                self.observe_entity(
                    canonical_name=entity["canonical_name"],
                    aliases=entity.get("aliases"),
                    entity_type=entity.get("entity_type", "unknown"),
                    source=source,
                    confidence=float(entity.get("confidence", 0.65)),
                    metadata={
                        "content_hash": content_hash,
                        "scope": scope,
                        **dict(entity.get("metadata", {})),
                    },
                )

        self._persist_memory_item(item=item, scope=scope)
        return item

    def recall(self, query: str, top_k: int = 5, scope: str = "all") -> List[MemoryItem]:
        candidates: List[MemoryItem] = []
        if scope in ("short", "all"):
            candidates.extend(self.short_term)
        if scope in ("long", "all"):
            candidates.extend(self.long_term)

        query_norm = self._normalize_text(query)
        query_tokens = set(self._tokenize(query))
        now_ts = time.time()
        scored: List[tuple[float, MemoryItem]] = []

        for item in candidates:
            content_norm = self._normalize_text(item.content)
            exact_match = 1.0 if query_norm and query_norm in content_norm else 0.0
            token_overlap = self._jaccard(query_tokens, set(self._tokenize(item.content)))
            tag_overlap = self._jaccard(query_tokens, set(self._tokenize(" ".join(item.tags))))
            recency_score = self._decay(now_ts - item.timestamp, half_life_seconds=3600.0)
            score = 0.45 * exact_match + 0.35 * token_overlap + 0.10 * tag_overlap + 0.10 * recency_score
            if exact_match > 0 or token_overlap > 0 or tag_overlap > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:top_k]]

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}

        for candidate in self._extract_entities_rule_based(text):
            self._merge_entity_candidate(merged, candidate)

        if self.llm_entity_extractor:
            try:
                llm_candidates = self.llm_entity_extractor(text) or []
            except Exception:
                llm_candidates = []
            for candidate in llm_candidates:
                self._merge_entity_candidate(merged, dict(candidate))

        return list(merged.values())

    def observe_entity(
        self,
        canonical_name: str,
        aliases: Optional[Sequence[str]] = None,
        entity_type: str = "unknown",
        source: str = "unknown",
        confidence: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[EntityRecord]:
        if not self._looks_like_entity(canonical_name):
            return None

        metadata = dict(metadata or {})
        now_ts = time.time()
        normalized_canonical = self._normalize_alias(canonical_name)
        entity_id = self._entity_id(normalized_canonical)
        record = self.entity_store.get(entity_id)

        if record is None:
            record = EntityRecord(
                entity_id=entity_id,
                canonical_name=canonical_name.strip(),
                entity_type=entity_type or "unknown",
                aliases=[],
                confidence=max(0.0, min(confidence, 1.0)),
            )
            self.entity_store[entity_id] = record
            self._stable_observation_keys[entity_id] = set()
        else:
            record.confidence = round((0.7 * record.confidence) + (0.3 * max(0.0, min(confidence, 1.0))), 4)
            if record.entity_type == "unknown" and entity_type and entity_type != "unknown":
                record.entity_type = entity_type

        record.occurrence_count += 1
        record.last_seen = now_ts

        source_key = self._normalize_text(source) or "unknown"
        record.source_counts[source_key] = record.source_counts.get(source_key, 0) + 1

        alias_pool = set(record.aliases)
        alias_pool.add(record.canonical_name)
        for alias in aliases or []:
            if self._looks_like_entity(alias):
                alias_pool.add(alias.strip())
        record.aliases = sorted(alias_pool)

        if metadata:
            record.metadata.update(metadata)

        content_hash = str(metadata.get("content_hash", "")) if metadata else ""
        observation_key = f"{source_key}:{content_hash or self._sha1(canonical_name)}"
        if confidence >= self.stable_confidence_threshold and observation_key not in self._stable_observation_keys[entity_id]:
            record.stable_occurrence_count += 1
            self._stable_observation_keys[entity_id].add(observation_key)

        observation = {
            "entity_id": entity_id,
            "canonical_name": record.canonical_name,
            "source": source_key,
            "timestamp": now_ts,
            "confidence": round(max(0.0, min(confidence, 1.0)), 4),
            "content_hash": content_hash,
            "stable_occurrence_count": record.stable_occurrence_count,
        }
        self.entity_observation_log.append(observation)

        for alias in record.aliases:
            self.alias_to_entity[self._normalize_alias(alias)] = entity_id

        self._persist_entity_record(record)
        self._persist_observation(observation)
        return record

    def recall_entities(self, query: str, top_k: int = 5) -> List[EntityRecallHit]:
        query_norm = self._normalize_text(query)
        collapsed_query = self._normalize_alias(query)
        query_tokens = set(self._tokenize(query))
        now_ts = time.time()
        hits: List[EntityRecallHit] = []

        for record in self.entity_store.values():
            alias_match = self._alias_match_score(record, query_norm, collapsed_query)
            token_overlap = self._entity_token_overlap(record, query_tokens)

            if alias_match == 0.0 and token_overlap == 0.0:
                continue

            recency_score = self._decay(now_ts - record.last_seen, half_life_seconds=86400.0)
            confidence_score = max(0.0, min(record.confidence, 1.0))
            stability_score = min(record.stable_occurrence_count / 3.0, 1.0)
            source_diversity_score = min(len(record.source_counts) / 3.0, 1.0)

            final_score = (
                ENTITY_ALIAS_MATCH_WEIGHT * alias_match
                + ENTITY_TOKEN_OVERLAP_WEIGHT * token_overlap
                + ENTITY_RECENCY_WEIGHT * recency_score
                + ENTITY_CONFIDENCE_WEIGHT * confidence_score
                + ENTITY_STABILITY_WEIGHT * stability_score
                + ENTITY_SOURCE_DIVERSITY_WEIGHT * source_diversity_score
            )

            hits.append(
                EntityRecallHit(
                    entity_id=record.entity_id,
                    canonical_name=record.canonical_name,
                    score=round(final_score, 4),
                    breakdown={
                        "alias_match": round(alias_match, 4),
                        "token_overlap": round(token_overlap, 4),
                        "recency_score": round(recency_score, 4),
                        "confidence_score": round(confidence_score, 4),
                        "stability_score": round(stability_score, 4),
                        "source_diversity_score": round(source_diversity_score, 4),
                    },
                )
            )

        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:top_k]

    def get_entity(self, key: str) -> Optional[EntityRecord]:
        if key in self.entity_store:
            return self.entity_store[key]
        entity_id = self.alias_to_entity.get(self._normalize_alias(key))
        if entity_id:
            return self.entity_store.get(entity_id)
        return None

    def memory_snapshot(self) -> Dict[str, Any]:
        return {
            "short_term_size": len(self.short_term),
            "long_term_size": len(self.long_term),
            "entity_count": len(self.entity_store),
            "entity_observation_count": len(self.entity_observation_log),
            "redis_enabled": self.redis_client is not None,
        }

    def clear_short(self) -> None:
        self.short_term.clear()
        if self.redis_client:
            self.redis_client.delete(self._redis_key("short"))

    def clear_long(self) -> None:
        self.long_term.clear()
        if self.redis_client:
            self.redis_client.delete(self._redis_key("long"))

    def _build_redis_client(self, redis_url: Optional[str]) -> Any:
        if redis is None:
            return None
        try:
            client = redis.Redis.from_url(redis_url or DEFAULT_REDIS_URL, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def _persist_memory_item(self, item: MemoryItem, scope: str) -> None:
        if not self.redis_client:
            return
        payload = self._to_json(asdict(item))
        if scope == "long":
            self.redis_client.lpush(self._redis_key("long"), payload)
        else:
            self.redis_client.lpush(self._redis_key("short"), payload)
            self.redis_client.ltrim(self._redis_key("short"), 0, max(self.max_short - 1, 0))

    def _persist_entity_record(self, record: EntityRecord) -> None:
        if not self.redis_client:
            return
        self.redis_client.set(self._redis_key(f"entity:{record.entity_id}"), self._to_json(asdict(record)))
        for alias in record.aliases:
            self.redis_client.hset(self._redis_key("entity_alias"), self._normalize_alias(alias), record.entity_id)

    def _persist_observation(self, observation: Dict[str, Any]) -> None:
        if not self.redis_client:
            return
        self.redis_client.rpush(self._redis_key("entity_observation"), self._to_json(observation))

    def _extract_entities_rule_based(self, text: str) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        seen_norms: set[str] = set()

        for candidate in self._extract_alias_pairs(text):
            norm_name = self._normalize_alias(candidate["canonical_name"])
            if norm_name and norm_name not in seen_norms:
                candidates.append(candidate)
                seen_norms.add(norm_name)

        for token in re.findall(r"\b[A-Za-z][A-Za-z0-9.\-]{1,40}\b", text):
            if not self._looks_like_entity(token):
                continue
            norm_token = self._normalize_alias(token)
            if norm_token in seen_norms:
                continue
            candidates.append(
                {
                    "canonical_name": token,
                    "aliases": [token],
                    "entity_type": self._infer_entity_type(token),
                    "confidence": 0.68,
                    "metadata": {"extractor": "rule"},
                }
            )
            seen_norms.add(norm_token)

        return candidates

    def _extract_alias_pairs(self, text: str) -> List[Dict[str, Any]]:
        candidates: List[Dict[str, Any]] = []
        patterns = [
            r"([A-Za-z][A-Za-z0-9\-\s]{3,80}?)\s*[\(（]([A-Za-z][A-Za-z0-9.\-]{1,24})[\)）]",
            r"([A-Za-z][A-Za-z0-9.\-]{1,24})\s*[\(（]([A-Za-z][A-Za-z0-9\-\s]{3,80}?)[\)）]",
        ]

        for pattern in patterns:
            for left, right in re.findall(pattern, text):
                left = left.strip()
                right = right.strip()
                if not self._looks_like_entity(left) or not self._looks_like_entity(right):
                    continue
                canonical_name, alias_name = self._pick_canonical_and_alias(left, right)
                candidates.append(
                    {
                        "canonical_name": canonical_name,
                        "aliases": [canonical_name, alias_name],
                        "entity_type": self._infer_entity_type(canonical_name),
                        "confidence": 0.9,
                        "metadata": {"extractor": "alias_pair"},
                    }
                )

        return candidates

    def _merge_entity_candidate(self, merged: Dict[str, Dict[str, Any]], candidate: Dict[str, Any]) -> None:
        canonical_name = str(candidate.get("canonical_name") or candidate.get("name") or "").strip()
        if not self._looks_like_entity(canonical_name):
            return

        norm_name = self._normalize_alias(canonical_name)
        aliases = [canonical_name]
        for alias in candidate.get("aliases", []) or []:
            if self._looks_like_entity(str(alias)):
                aliases.append(str(alias).strip())

        clean_aliases = sorted({alias for alias in aliases if self._looks_like_entity(alias)})
        confidence = max(0.0, min(float(candidate.get("confidence", 0.65)), 1.0))
        entity_type = str(candidate.get("entity_type") or self._infer_entity_type(canonical_name))
        metadata = dict(candidate.get("metadata", {}))

        if norm_name not in merged:
            merged[norm_name] = {
                "canonical_name": canonical_name,
                "aliases": clean_aliases,
                "entity_type": entity_type,
                "confidence": confidence,
                "metadata": metadata,
            }
            return

        merged_candidate = merged[norm_name]
        merged_candidate["aliases"] = sorted(set(merged_candidate["aliases"]) | set(clean_aliases))
        merged_candidate["confidence"] = round(max(float(merged_candidate["confidence"]), confidence), 4)
        if merged_candidate["entity_type"] == "unknown" and entity_type != "unknown":
            merged_candidate["entity_type"] = entity_type
        if metadata:
            merged_candidate["metadata"].update(metadata)

    def _alias_match_score(self, record: EntityRecord, query_norm: str, collapsed_query: str) -> float:
        best_score = 0.0
        for alias in [record.canonical_name] + list(record.aliases):
            alias_norm = self._normalize_alias(alias)
            if not alias_norm:
                continue
            if alias_norm == collapsed_query:
                return 1.0
            if alias_norm in collapsed_query:
                best_score = max(best_score, 0.95 if alias == record.canonical_name else 0.9)
        return best_score

    def _entity_token_overlap(self, record: EntityRecord, query_tokens: set[str]) -> float:
        entity_tokens = set(self._tokenize(" ".join([record.canonical_name] + record.aliases)))
        return self._jaccard(query_tokens, entity_tokens)

    def _pick_canonical_and_alias(self, left: str, right: str) -> tuple[str, str]:
        left_upper_ratio = self._upper_ratio(left)
        right_upper_ratio = self._upper_ratio(right)

        if right_upper_ratio >= left_upper_ratio and len(right) <= len(left):
            return right, left
        return left, right

    def _infer_entity_type(self, text: str) -> str:
        lower_text = text.lower()
        if any(token in lower_text for token in ("bert", "gpt", "llama", "qwen", "reranker", "embedding", "m3e")):
            return "model"
        if any(token in lower_text for token in ("squad", "glue", "qa", "dataset", "bench")):
            return "dataset"
        if any(token in lower_text for token in ("nsp", "mlm", "rag", "grpo", "lora", "mcp")):
            return "method"
        return "unknown"

    def _looks_like_entity(self, text: str) -> bool:
        clean = text.strip()
        if len(clean) < 2:
            return False
        if clean.lower() in _LOW_SIGNAL_TOKENS:
            return False
        if re.fullmatch(r"\d+", clean):
            return False
        if re.fullmatch(r"[a-z]{1,3}", clean):
            return False
        if re.search(r"[A-Z0-9.\-]", clean):
            return True
        if re.fullmatch(r"[\u4e00-\u9fff]{2,12}", clean):
            return True
        return False

    def _tokenize(self, text: str) -> List[str]:
        raw_tokens = re.findall(r"[A-Za-z0-9.\-]+|[\u4e00-\u9fff]{2,}", text.lower())
        return [token for token in raw_tokens if token and token not in _LOW_SIGNAL_TOKENS]

    def _normalize_text(self, text: str) -> str:
        compact = re.sub(r"\s+", " ", text.strip().lower())
        return compact

    def _normalize_alias(self, text: str) -> str:
        lowered = text.strip().lower()
        lowered = re.sub(r"[\"'“”‘’`]", "", lowered)
        lowered = re.sub(r"[\s_:/\\,;，。、《》<>（）()\[\]{}]+", "", lowered)
        return lowered

    def _entity_id(self, normalized_name: str) -> str:
        return f"ent_{self._sha1(normalized_name)[:12]}"

    def _sha1(self, text: str) -> str:
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    def _jaccard(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        intersection = len(left & right)
        union = len(left | right)
        if union == 0:
            return 0.0
        return intersection / union

    def _decay(self, age_seconds: float, half_life_seconds: float) -> float:
        if age_seconds <= 0:
            return 1.0
        return math.exp(-math.log(2) * age_seconds / max(half_life_seconds, 1.0))

    def _upper_ratio(self, text: str) -> float:
        letters = [char for char in text if char.isalpha()]
        if not letters:
            return 0.0
        upper_count = sum(1 for char in letters if char.isupper())
        return upper_count / len(letters)

    def _redis_key(self, suffix: str) -> str:
        return f"memory:v1:{self.session_id}:{suffix}"

    def _to_json(self, payload: Dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, default=str)
