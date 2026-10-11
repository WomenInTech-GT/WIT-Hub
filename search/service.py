from __future__ import annotations

DOCUMENTS = [
    {
        "id": "welcome",
        "title": "Welcome to WIT-Hub",
        "content": "WIT-Hub is a starter repo for building a content platform with a web frontend and a backend API.",
    },
    {
        "id": "backend",
        "title": "Backend API",
        "content": "The backend service exposes health and API routes for the platform and is built with FastAPI.",
    },
    {
        "id": "frontend",
        "title": "Frontend app",
        "content": "The frontend uses Vite and React to provide a modern user experience for browsing and exploring content.",
    },
]


def search_documents(query: str, limit: int = 5):
    needle = (query or "").strip().lower()
    if not needle:
        return DOCUMENTS[:limit]

    matches = []
    for doc in DOCUMENTS:
        haystack = f"{doc['title']} {doc['content']}".lower()
        if needle in haystack:
            matches.append(doc)

    return matches[:limit]


if __name__ == "__main__":
    print(search_documents("api"))
