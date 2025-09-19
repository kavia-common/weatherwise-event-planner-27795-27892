"""
PUBLIC_INTERFACE
Entrypoint script to start the FastAPI server with uvicorn.

This module reads HOST and PORT from environment variables via Settings and starts uvicorn
binding to those values. Defaults: HOST=0.0.0.0, PORT=3001.

Usage:
    python -m src.api.run
or:
    uvicorn src.api.main:app --host 0.0.0.0 --port 3001  # equivalent behavior

Environment variables (configured in .env):
    - HOST: Bind address (default: 0.0.0.0)
    - PORT: Bind port (default: 3001)
"""

import logging
import os
import sys

import uvicorn

from src.core.config import get_settings

logger = logging.getLogger("uvicorn.error")


def _parse_port(port_str: str) -> int:
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError("Port out of range")
        return port
    except Exception as exc:
        raise ValueError(f"Invalid PORT value: {port_str!r}") from exc


def main() -> None:
    """
    PUBLIC_INTERFACE
    Start the Uvicorn server using app at src.api.main:app.

    Respects HOST and PORT from settings (.env). Fallbacks to 0.0.0.0:3001.
    """
    settings = get_settings()
    host = os.getenv("HOST", settings.HOST) or "0.0.0.0"
    port_str = os.getenv("PORT", str(settings.PORT)) or "3001"

    try:
        port = _parse_port(port_str)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(2)

    logger.info("Starting WeatherWise Events API on %s:%s", host, port)
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG,
        log_level="info",
        # Enable HTTP/1.1 server with websockets; uvloop may be present in requirements.
        # No workers specified; rely on container orchestration if needed.
    )


if __name__ == "__main__":
    main()
