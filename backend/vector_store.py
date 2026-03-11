import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

import psycopg
from psycopg.rows import dict_row


class PgVectorStore:
    """Thin wrapper around pgvector for mentor/user embedding storage."""

    def __init__(self, dsn: Optional[str], dimension: int) -> None:
        self.dsn = dsn
        self.dimension = dimension
        self._conn: Optional[psycopg.Connection] = None

    def _require_configured(self) -> None:
        if not self.dsn:
            raise RuntimeError("Postgres DSN is not configured (set PG_DSN).")

    def _connect(self) -> psycopg.Connection:
        self._require_configured()
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(self.dsn, autocommit=True, row_factory=dict_row)
        return self._conn

    def ensure_schema(self) -> None:
        """Create extension, tables, and indexes if they don't exist."""
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS mentor_embeddings (
                    mentor_id TEXT PRIMARY KEY,
                    profile JSONB,
                    embedding vector({self.dimension}),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS need_embeddings (
                    need_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    context JSONB,
                    embedding vector({self.dimension}),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mentor_ratings (
                    id BIGSERIAL PRIMARY KEY,
                    mentor_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mentor_weights (
                    mentor_id TEXT PRIMARY KEY,
                    weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
                    sample_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_mentor_embeddings_vector
                ON mentor_embeddings
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

    def _to_vector_literal(self, embedding: Sequence[float]) -> str:
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Embedding has length {len(embedding)} but expected {self.dimension}."
            )
        return "[" + ",".join(f"{float(x):.8f}" for x in embedding) + "]"

    def upsert_mentor_embedding(
        self, mentor_id: str, embedding: Sequence[float], profile: Optional[Dict[str, Any]]
    ) -> None:
        conn = self._connect()
        vector_literal = self._to_vector_literal(embedding)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mentor_embeddings (mentor_id, profile, embedding, updated_at)
                VALUES (%s, %s::jsonb, %s::vector, NOW())
                ON CONFLICT (mentor_id) DO UPDATE SET
                    profile = EXCLUDED.profile,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                (mentor_id, json.dumps(profile) if profile is not None else None, vector_literal),
            )

    def upsert_need_embedding(
        self,
        need_id: str,
        user_id: str,
        embedding: Sequence[float],
        context: Optional[Dict[str, Any]],
    ) -> None:
        conn = self._connect()
        vector_literal = self._to_vector_literal(embedding)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO need_embeddings (need_id, user_id, context, embedding, updated_at)
                VALUES (%s, %s, %s::jsonb, %s::vector, NOW())
                ON CONFLICT (need_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    context = EXCLUDED.context,
                    embedding = EXCLUDED.embedding,
                    updated_at = NOW()
                """,
                (need_id, user_id, json.dumps(context) if context is not None else None, vector_literal),
            )

    def fetch_similar_mentors(
        self, embedding: Sequence[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        conn = self._connect()
        vector_literal = self._to_vector_literal(embedding)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.mentor_id,
                    m.profile,
                    COALESCE(w.weight, 1.0) AS weight,
                    1 - (m.embedding <=> %s::vector) AS base_similarity,
                    (1 - (m.embedding <=> %s::vector)) * COALESCE(w.weight, 1.0) AS weighted_similarity
                FROM mentor_embeddings m
                LEFT JOIN mentor_weights w ON w.mentor_id = m.mentor_id
                ORDER BY weighted_similarity DESC
                LIMIT %s
                """,
                (vector_literal, vector_literal, top_k),
            )
            rows = cur.fetchall()
            return [
                {
                    "mentor_id": row["mentor_id"],
                    "profile": row.get("profile"),
                    "weight": float(row.get("weight") or 1.0),
                    "base_similarity": float(row.get("base_similarity") or 0.0),
                    "weighted_similarity": float(row.get("weighted_similarity") or 0.0),
                }
                for row in rows
            ]

    def record_rating(self, user_id: str, mentor_id: str, rating: int) -> None:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5.")

        conn = self._connect()
        normalized = rating / 5.0

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO mentor_ratings (mentor_id, user_id, rating, created_at)
                VALUES (%s, %s, %s, NOW())
                """,
                (mentor_id, user_id, rating),
            )

            # Exponential moving average with light smoothing
            cur.execute(
                """
                INSERT INTO mentor_weights (mentor_id, weight, sample_count, updated_at)
                VALUES (%s, %s, 1, NOW())
                ON CONFLICT (mentor_id) DO UPDATE SET
                    weight = GREATEST(0.2, LEAST(2.0, 0.8 * mentor_weights.weight + 0.2 * EXCLUDED.weight)),
                    sample_count = mentor_weights.sample_count + 1,
                    updated_at = NOW()
                """,
                (mentor_id, normalized),
            )

    def get_weight(self, mentor_id: str) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT weight, sample_count, updated_at
                FROM mentor_weights
                WHERE mentor_id = %s
                """,
                (mentor_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "weight": float(row.get("weight") or 1.0),
                "sample_count": int(row.get("sample_count") or 0),
                "updated_at": row.get("updated_at"),
            }

    def close(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

