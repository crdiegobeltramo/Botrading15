## 2026-03-29 - CORS Misconfiguration and Route Ordering in FastAPI
**Vulnerability:** Insecure CORS configuration with `allow_credentials=True` combined with wildcard origins (`allow_origins=["*"]`), and static files mounted at `"/"` before API endpoints.
**Learning:** Wildcard origins with credentials violate browser CORS security models, and mounting static files at `"/"` before API endpoints causes static handlers to intercept API routes.
**Prevention:** Always set `allow_credentials=False` when using wildcard CORS origins, and mount static UI routes after API endpoints in FastAPI.
