# Sentinel Security Journal

## 2025-05-18 - Permissive CORS and Information Leakage in Web Interface
**Vulnerability:** Overly permissive CORS configuration with `allow_origins=["*"]` and `allow_credentials=True`, combined with unhandled exceptions leaking raw error strings to API responses (`detail=str(e)`).
**Learning:** Combining wildcard CORS origins with `allow_credentials=True` violates web security standards and browsers block cross-origin requests. Unhandled exceptions in FastAPI endpoints leak sensitive internal execution details, API responses, or system paths.
**Prevention:** Configure CORS with `allow_credentials=False` for wildcard origins, log exceptions internally with server-side logging, and return sanitized generic error messages to clients.
