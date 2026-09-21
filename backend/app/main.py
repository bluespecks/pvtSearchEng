import os

import httpx
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PvtSearchEng API",
    description="Privacy-first search engine backend",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

SEARXNG_URL = os.getenv(
    "SEARXNG_URL",
    "http://localhost:8080",
)


def calculate_score(query, result):
    score = 0
    breakdown = {
        "phrase_title": 0,
        "phrase_description": 0,
        "word_title": 0,
        "word_description": 0,
    }

    query_words = query.lower().split()
    title = result["title"].lower()
    description = result["description"].lower()

    if query.lower() in title:
        score += 5
        breakdown["phrase_title"] = 5

    if query.lower() in description:
        score += 2
        breakdown["phrase_description"] = 2

    for word in query_words:
        if word in title:
            score += 3
            breakdown["word_title"] += 3

        if word in description:
            score += 1
            breakdown["word_description"] += 1

    return score, breakdown


@app.get("/")
async def root():
    return {
        "name": "PvtSearchEng API",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    debug: bool = False,
):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{SEARXNG_URL}/search",
                params={
                    "q": q,
                    "format": "json",
                },
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Search service unavailable",
        )

    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Search service unavailable",
        )

    results = []
    seen = {}

    for result in data.get("results", []):
        url = result.get("url", "")

        if not url:
            continue

        if url in seen:
            existing = seen[url]

            sources = set(existing["source"].split(", "))
            sources.update(result.get("engines", []))

            existing["source"] = ", ".join(
                sorted(source for source in sources if source)
            )

            continue

        normalized = {
            "title": result.get("title", ""),
            "url": url,
            "description": result.get("content", ""),
            "source": ", ".join(result.get("engines", [])),
            "searx_score": result.get("score", 0),
        }

        score, breakdown = calculate_score(q, normalized)

        normalized["score"] = score + normalized["searx_score"]
        normalized["ranking"] = breakdown

        seen[url] = normalized
        results.append(normalized)

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    if not debug:
        for result in results:
            result.pop("ranking", None)

    return {
        "query": q,
        "results": results,
    }
