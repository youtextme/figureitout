"""Vision — local multimodal analysis + screenshot understanding."""

from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path

from figureitout.config import local_base_url, use_mock, vision_model


def _encode_image(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return mime, data


def analyze_image(path: str, question: str = "Describe this image in detail.") -> str:
    """Analyze an image with the configured vision model (local-first)."""
    img = Path(path).expanduser().resolve()
    if not img.exists():
        raise FileNotFoundError(img)
    if use_mock():
        return f"[mock-vision] {img.name}: {question} — image present ({img.stat().st_size} bytes)."

    mime, b64 = _encode_image(img)
    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=local_base_url(),
            api_key=os.environ.get("OPENAI_API_KEY", "local-no-key"),
        )
        resp = client.chat.completions.create(
            model=vision_model(),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        # Fallback: metadata-only description so the runner never stalls.
        return (
            f"[vision-fallback] Could not invoke vision model ({exc}). "
            f"File={img} size={img.stat().st_size} question={question}"
        )
