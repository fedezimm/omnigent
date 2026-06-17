"""E2E test: markdown file attachment.

Verifies the full pipeline: file upload → input_file content block →
content resolution (MIME type from filename) → LLM receives the file
and produces a response. Runs against the mock LLM server.

The ``list_files`` and ``download_file`` tool tests that were here
previously require spec-level ``tools.builtins`` declarations which
the omnigent single-file YAML format does not support. They remain
in the real-LLM e2e suite (``tests/e2e/test_file_tools.py`` on the
``e2e.yml`` workflow with ``--llm-api-key``).

Usage::

    pytest tests/e2e/test_file_tools.py -v
"""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import pytest

from tests.e2e.conftest import (
    configure_mock_llm,
    create_runner_bound_session,
    poll_session_until_terminal,
    register_inline_agent,
    reset_mock_llm,
    send_user_message_to_session,
)


def _extract_all_text(body: dict[str, Any]) -> str:
    """Concatenate all assistant text blocks from a terminal response."""
    parts: list[str] = []
    for item in body.get("output", []):
        if item.get("type") == "message":
            for block in item.get("content", []):
                text = block.get("text")
                if text:
                    parts.append(text)
    return "\n".join(parts)


def test_markdown_file_attachment(
    http_client: httpx.Client,
    live_runner_id: str,
    using_mock_llm: bool,
    mock_llm_server_url: str | None,
) -> None:
    """
    Uploading and attaching a .md file works end-to-end.

    Verifies the full pipeline: file upload → input_file content
    block → content resolution (MIME type from filename) → LLM
    receives and responds.
    """
    if not using_mock_llm:
        pytest.skip("mock-only test")
    model = f"mock-md-{uuid.uuid4().hex[:6]}"

    reset_mock_llm(mock_llm_server_url)
    agent_name = register_inline_agent(
        http_client,
        name=f"md-{uuid.uuid4().hex[:6]}",
        harness="openai-agents",
        model=model,
        profile="",
        prompt="You are a document analyst.",
        mock_llm_base_url=(f"{mock_llm_server_url}/v1" if mock_llm_server_url else None),
    )
    configure_mock_llm(
        mock_llm_server_url,
        [{"text": "Ship feature, write tests, update docs by Friday."}],
        key=model,
    )

    session_id = create_runner_bound_session(
        http_client, agent_name=agent_name, runner_id=live_runner_id
    )

    md_content = (
        b"# Project Plan\n\n## Goals\n\n- Ship the feature by Friday\n- Write tests\n- Update docs"
    )
    upload_resp = http_client.post(
        f"/v1/sessions/{session_id}/resources/files",
        files={"file": ("plan.md", md_content, "text/markdown")},
    )
    upload_resp.raise_for_status()
    file_id = upload_resp.json()["id"]

    rid = send_user_message_to_session(
        http_client,
        session_id=session_id,
        content=[
            {
                "type": "input_text",
                "text": "Summarize this document in one sentence.",
            },
            {"type": "input_file", "file_id": file_id, "filename": "plan.md"},
        ],
    )
    body = poll_session_until_terminal(
        http_client, session_id=session_id, response_id=rid, timeout=60
    )

    assert body["status"] == "completed", (
        f"Status: {body['status']!r}. Error: {body.get('error')}. Output: {body.get('output', [])}"
    )
    text = _extract_all_text(body)
    assert text.strip(), f"Agent produced no text. Output: {body.get('output', [])}"
