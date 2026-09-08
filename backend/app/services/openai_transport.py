import json
import urllib.request
from typing import Any, Protocol


class OpenAIChatTransport(Protocol):
    def create_chat_completion(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        timeout_seconds: int,
        max_completion_tokens: int | None = None,
    ) -> dict[str, Any]: ...


class UrllibOpenAIChatTransport:
    def create_chat_completion(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        timeout_seconds: int,
        max_completion_tokens: int | None = None,
    ) -> dict[str, Any]:
        url = f"{base_url.rstrip('/')}/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                **({"max_completion_tokens": max_completion_tokens}
                   if max_completion_tokens is not None else {}),
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))


