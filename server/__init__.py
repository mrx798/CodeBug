"""Server package — re-exports from app module."""
from server.app import app, main

__all__ = ["app", "main"]
