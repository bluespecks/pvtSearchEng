import httpx
from fastapi import FastAPI, Query

app = FastAPI(
    title="PvtSearchEng API",
    description="Privacy-first search engine backend",
    version="0.1.0",
)

SEARXNG_URL = "http://localhost:8080"


def calculate_score(query, result):
    score = 0

    query_words = query.lower().split()
    title = result["title"].lower()
    description = result["description"].lower()

    if query.lower() in title:
        score += 5

    if query.lower() in description:
        score += 2

    for word in query_words:
        if word in title:
            score += 3

        if word in description:
            score += 1

    return score


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
async def search(q: str = Query(..., min_length=1)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": q,
                "format": "json",
            },
        )

    response.raise_for_status()

    data = response.json()

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

        normalized["score"] = (
            calculate_score(q, normalized)
            + normalized["searx_score"]
        )

        seen[url] = normalized
        results.append(normalized)

    results.sort(
        key=lambda result: result["score"],
        reverse=True,
    )

    return {
        "query": q,
        "results": results,
    }
