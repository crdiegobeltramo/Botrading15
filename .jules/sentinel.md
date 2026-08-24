## 2025-05-18 - Permissive CORS Configuration with Wildcard Origins
**Vulnerability:** `app.py` configured CORS middleware with `allow_origins=["*"]` and `allow_credentials=True`.
**Learning:** Browsers and CORS security specifications reject wildcard origins when credentials are allowed, and allowing wildcard credentials creates risks of sensitive credential exposure across origins.
**Prevention:** Always set `allow_credentials=False` when using wildcard origins `allow_origins=["*"]`, or restrict `allow_origins` to explicit trusted domains when credentials are required.
