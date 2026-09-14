import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.auth.password import hash_password


class JsonAuthStore:
    """
    A lightweight, JSON-based persistent store for user accounts.

    NOTE: This is a mock implementation designed for demonstration and
    prototyping. In a production environment, this should be replaced
    by a real database (e.g., PostgreSQL or MongoDB) to handle
    concurrency, indexing, and scalability.
    """
    def __init__(self, path: Path):
        self.path = path
        # RLock (Re-entrant Lock) ensures that multiple requests can't
        # modify the user data simultaneously, preventing race conditions
        # and data corruption.
        self._lock = threading.RLock()
        self.data = self._load()
        self._ensure_demo_user()

    def _load(self) -> dict[str, Any]:
        """Loads user data from the JSON file, providing a default structure if empty."""
        if not self.path.exists():
            return {"by_email": {}, "by_id": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return {"by_email": data.get("by_email", {}), "by_id": data.get("by_id", {})}
        except (OSError, json.JSONDecodeError):
            return {"by_email": {}, "by_id": {}}

    def _save(self) -> None:
        """
        Persists the in-memory user data to the JSON file using an atomic write.

        Atomic Write Pattern:
        1. Write the data to a temporary file (.tmp).
        2. Flush and sync the file to disk to ensure all bytes are written.
        3. Use os.replace to move the temp file to the final destination.

        This prevents data corruption: if the app crashes mid-write,
        the original file remains intact.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent, suffix=".tmp") as handle:
            json.dump(self.data, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, self.path)

    def _ensure_demo_user(self) -> None:
        """Creates a default 'guest' account to allow users to explore the app without signing up."""
        if self.get_by_id("guest_user") is None:
            with self._lock:
                self.data["by_id"]["guest_user"] = {
                    "user_id": "guest_user",
                    "email": "demo@movieverse.local",
                    "username": "Demo Viewer",
                    "is_demo": True,
                }
                self.data["by_email"]["demo@movieverse.local"] = self.data["by_id"]["guest_user"]
                self._save()

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        return self.data["by_email"].get(email.strip().lower())

    def get_by_id(self, user_id: str) -> dict[str, Any] | None:
        return self.data["by_id"].get(user_id)

    def create_user(self, email: str, username: str, password: str) -> dict[str, Any]:
        """Creates a new user account with a hashed password and unique ID."""
        normalized_email = email.strip().lower()
        if self.get_by_email(normalized_email):
            raise ValueError("An account with this email already exists")
        user = {
            "user_id": f"usr_{uuid.uuid4().hex[:12]}",
            "email": normalized_email,
            "username": username.strip(),
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
        }
        with self._lock:
            self.data["by_email"][normalized_email] = user
            self.data["by_id"][user["user_id"]] = user
            self._save()
        return user
