"""Genie Conversations API client.

A small, defensive wrapper around the Databricks Genie REST API. Keeping this
in its own module (instead of inline in app.py) is what keeps the UI readable.

Credentials are resolved by the Databricks SDK automatically: env vars
(DATABRICKS_HOST / DATABRICKS_TOKEN) locally, or the injected service principal
when running as a Databricks App.

Structure inspired by viveknz/vic-powerline-bushfire-genie (adapted).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from databricks.sdk import WorkspaceClient

log = logging.getLogger("cosmos.genie")

TERMINAL_OK = {"COMPLETED"}
TERMINAL_FAIL = {"FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}

# Friendly labels shown while polling, so the wait feels like progress.
STATUS_LABELS = {
    "SUBMITTED": "Sending your question",
    "FETCHING_METADATA": "Reading table metadata",
    "FILTERING_CONTEXT": "Working out which tables are relevant",
    "ASKING_AI": "Thinking",
    "PENDING_WAREHOUSE": "Waiting for the SQL warehouse",
    "EXECUTING_QUERY": "Running the query",
    "COMPLETED": "Done",
    "FAILED": "Failed",
    "CANCELLED": "Cancelled",
}


class GenieError(RuntimeError):
    """Genie returned a failure status or an unusable response."""


@dataclass
class GenieTurn:
    """One question and its answer."""

    conversation_id: str
    message_id: str
    question: str
    status: str
    text: Optional[str] = None          # prose answer
    follow_up: Optional[str] = None     # a clarifying question Genie asked back
    sql: Optional[str] = None
    sql_description: Optional[str] = None
    attachment_id: Optional[str] = None
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    error: Optional[str] = None
    elapsed_seconds: float = 0.0

    @property
    def has_data(self) -> bool:
        return bool(self.columns and self.rows)


class GenieClient:
    """Thin wrapper over the Genie Conversations API."""

    def __init__(
        self,
        space_id: str,
        workspace_client: Optional[WorkspaceClient] = None,
        poll_interval: float = 1.5,
        timeout_seconds: float = 180.0,
        max_rows: int = 500,
    ) -> None:
        if not space_id:
            raise ValueError("space_id is required")
        self.space_id = space_id
        self.poll_interval = poll_interval
        self.timeout_seconds = timeout_seconds
        self.max_rows = max_rows
        self._w = workspace_client or WorkspaceClient()

    # -- HTTP -----------------------------------------------------------
    def _do(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        try:
            resp = self._w.api_client.do(method, path, body=body)
        except Exception as exc:  # surface the real cause
            log.exception("API call failed: %s %s", method, path)
            raise GenieError(f"Databricks API call failed: {exc}") from exc
        return resp if isinstance(resp, dict) else {}

    # -- Public ---------------------------------------------------------
    def ask(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        on_status: Optional[Callable[[str, str], None]] = None,
    ) -> GenieTurn:
        """Ask a question and wait for the answer.

        Passing conversation_id continues an existing thread, which is what
        makes follow-ups ('just the top three') work.
        """
        question = (question or "").strip()
        if not question:
            raise ValueError("question must not be empty")

        started = time.monotonic()

        if conversation_id:
            path = (f"/api/2.0/genie/spaces/{self.space_id}"
                    f"/conversations/{conversation_id}/messages")
            payload = self._do("POST", path, {"content": question})
            message = payload if "id" in payload else payload.get("message", {})
            cid = conversation_id
        else:
            path = f"/api/2.0/genie/spaces/{self.space_id}/start-conversation"
            payload = self._do("POST", path, {"content": question})
            message = payload.get("message", {})
            cid = payload.get("conversation", {}).get("id")

        mid = message.get("id") or message.get("message_id")
        if not (cid and mid):
            raise GenieError(f"No conversation/message id returned. Keys: {sorted(payload)}")

        final = self._poll(cid, mid, on_status)
        turn = self._build_turn(cid, mid, question, final)
        turn.elapsed_seconds = round(time.monotonic() - started, 1)
        return turn

    # -- Polling --------------------------------------------------------
    def _poll(self, cid: str, mid: str, on_status) -> dict:
        path = (f"/api/2.0/genie/spaces/{self.space_id}"
                f"/conversations/{cid}/messages/{mid}")
        deadline = time.monotonic() + self.timeout_seconds
        last = None
        while time.monotonic() < deadline:
            payload = self._do("GET", path)
            status = payload.get("status", "UNKNOWN")
            if status != last:
                if on_status:
                    on_status(status, STATUS_LABELS.get(status, status.replace("_", " ").title()))
                last = status
            if status in TERMINAL_OK or status in TERMINAL_FAIL:
                return payload
            time.sleep(self.poll_interval)
        raise GenieError(f"Genie did not finish within {self.timeout_seconds:.0f}s (last: {last})")

    # -- Parsing --------------------------------------------------------
    def _build_turn(self, cid: str, mid: str, question: str, payload: dict) -> GenieTurn:
        status = payload.get("status", "UNKNOWN")
        turn = GenieTurn(conversation_id=cid, message_id=mid, question=question, status=status)

        if status in TERMINAL_FAIL:
            err = payload.get("error") or {}
            turn.error = err.get("error") or err.get("message") or status
            return turn

        for att in payload.get("attachments") or []:
            self._read_attachment(att, turn)

        if turn.attachment_id:
            try:
                self._fetch_result(turn)
            except GenieError as exc:
                # A missing result is not fatal; still show the prose answer.
                log.warning("Could not fetch query result: %s", exc)

        if not turn.text and not turn.follow_up and not turn.has_data:
            turn.error = turn.error or "Genie returned an empty response."
        return turn

    @staticmethod
    def _read_attachment(att: dict, turn: GenieTurn) -> None:
        # A completed message can carry both a clarifying question and the
        # answer. The 'purpose' field separates them.
        text = att.get("text")
        if isinstance(text, dict) and text.get("content"):
            if text.get("purpose") == "FOLLOW_UP_QUESTION":
                turn.follow_up = text["content"]
            else:
                turn.text = text["content"]

        query = att.get("query")
        if isinstance(query, dict):
            turn.sql = query.get("query") or turn.sql
            turn.sql_description = query.get("description") or turn.sql_description
            turn.attachment_id = att.get("attachment_id") or turn.attachment_id

    def _fetch_result(self, turn: GenieTurn) -> None:
        path = (f"/api/2.0/genie/spaces/{self.space_id}"
                f"/conversations/{turn.conversation_id}"
                f"/messages/{turn.message_id}"
                f"/attachments/{turn.attachment_id}/query-result")
        payload = self._do("GET", path)
        stmt = payload.get("statement_response") or {}
        manifest = stmt.get("manifest") or {}
        schema = manifest.get("schema") or {}
        turn.columns = [c.get("name", f"col_{i}") for i, c in enumerate(schema.get("columns") or [])]
        turn.truncated = bool(manifest.get("truncated"))
        turn.rows = self._extract_rows(stmt.get("result") or {}, self.max_rows)
        turn.row_count = manifest.get("total_row_count") or len(turn.rows)

    @staticmethod
    def _extract_rows(result: dict, max_rows: int) -> list[list[Any]]:
        # IMPORTANT: the API returns one of two shapes. `data_array` is
        # documented; `data_typed_array` is what it often actually sends, with
        # each value wrapped as {"str": "..."}. Handle BOTH or you silently get
        # zero rows. (This is the bug in the original inline code.)
        if result.get("data_array"):
            return [list(r) for r in result["data_array"][:max_rows]]
        typed = result.get("data_typed_array") or []
        rows = []
        for entry in typed[:max_rows]:
            values = entry.get("values") or []
            rows.append([v.get("str") if isinstance(v, dict) else v for v in values])
        return rows


def rows_to_records(turn: GenieTurn) -> list[dict[str, Any]]:
    """columns + rows -> list of dicts, for building a DataFrame."""
    return [dict(zip(turn.columns, row)) for row in turn.rows]
