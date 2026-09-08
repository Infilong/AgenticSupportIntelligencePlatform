"""Explicit model download plus an actual CPU inference smoke test; not a RAG quality gate."""

import json
import os
import sys
from dataclasses import asdict

from app.providers.local_embeddings import LocalEmbeddings


def main():
    provider = LocalEmbeddings(
        cache_dir=os.environ.get("ASI_EMBEDDING_CACHE"), allow_download="--offline" not in sys.argv
    )
    result = provider.encode_batch(
        [
            "Refund requests must be submitted within fourteen days of purchase.",
            "返金申請は購入から14日以内に提出してください。",
            "退款申请必须在购买后十四天内提交。",
        ]
    )
    query = provider.encode_batch(["What is the refund deadline?"], "query")
    metadata = asdict(result)
    vectors = metadata.pop("vectors")
    norms = [sum(value * value for value in vector) ** 0.5 for vector in vectors]
    scores = [sum(a * b for a, b in zip(vector, query.vectors[0], strict=True)) for vector in vectors]
    if len(vectors) != 3 or any(abs(norm - 1) > 0.001 for norm in norms):
        raise ValueError("Unexpected embedding shape or normalization")
    print(
        json.dumps(
            {
                "status": "real_cpu_inference_passed",
                **metadata,
                "languages": ["en", "ja", "zh"],
                "cosine_scores": scores,
                "quality_gate": "not_evaluated",
                "query_duration_ms": query.duration_ms,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
