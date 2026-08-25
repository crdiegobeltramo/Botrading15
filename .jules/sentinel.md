## 2026-03-01 - Sanitización de excepciones y resolución dinámica de rutas estáticas
**Vulnerability:** Revelación de información sensible (stack traces/detalles de error internos) a clientes de la API a través de los mensajes de excepción en endpoints de FastAPI (`detail=str(e)`).
**Learning:** Retornar `str(e)` directamente en las excepciones HTTP exponía detalles internos de la aplicación o credenciales en caso de fallas de conexión o bibliotecas.
**Prevention:** Sanitizar siempre las respuestas de error hacia los clientes con mensajes genéricos seguros y registrar las excepciones detalladas en el servidor utilizando `logger.error(..., exc_info=True)`.
