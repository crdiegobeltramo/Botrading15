## 2025-03-01 - CORS Wildcard Credentials Misconfiguration
**Vulnerability:** Permissive CORS configuration with `allow_origins=["*"]` combined with `allow_credentials=True`.
**Learning:** Combining wildcard origins with credentialed requests introduces security risks and is rejected by modern browser security standards.
**Prevention:** Always set `allow_credentials=False` when using wildcard CORS origins or restrict `allow_origins` to explicit trusted domains when credentials are required.
