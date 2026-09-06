"""ASCII art generated and analysed by a vision language model.

ASCII3D can talk to any **OpenAI-compatible** chat completions API
(the default points at the Z.ai endpoint).  Two directions are
supported:

* **generation** -- describe an art in words, the model answers with
  an ASCII drawing (:meth:`VLMArtist.generate`), which can then be
  turned and spun with the rest of the engine;
* **analysis** -- show the model an art (as text) or a rendered 3D
  frame (as a PNG image, true vision) and ask it what it sees
  (:meth:`VLMArtist.describe`, :meth:`VLMArtist.describe_render`).

Configuration (environment variables or constructor arguments):

======================  ===========================================
``ASCII3D_API_KEY``     the API key (required for real calls)
``ASCII3D_API_BASE``    default ``https://api.z.ai/api/paas/v4``
``ASCII3D_VLM_MODEL``   default ``glm-4.5v``
======================  ===========================================

Example:
    >>> import os
    >>> from ascii3d.vlm import VLMArtist
    >>> artist = VLMArtist(api_key=os.environ['ASCII3D_API_KEY'])
    >>> art = artist.generate('a small house')     # doctest: +SKIP
    >>> print(art)                                 # doctest: +SKIP
    >>> print(artist.describe_render(art))         # doctest: +SKIP
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request

__all__ = ['VLMArtist', 'VLMError', 'VLMConfigError', 'VLMResponseError']

DEFAULT_BASE_URL = 'https://api.z.ai/api/paas/v4'
DEFAULT_MODEL = 'glm-4.5v'

# Characters the model is told to use -- the stroke alphabet the
# engine understands plus classic shading characters.
_ART_ALPHABET = (
    r"space _ | / \ ( ) [ ] { } < > . ' ` \" ~ "
    r'- = + * # @ o O 0 8 : ; ^ v w x z')


class VLMError(RuntimeError):
    """Base class for VLM failures."""


class VLMConfigError(VLMError):
    """Raised when no API key is configured."""


class VLMResponseError(VLMError):
    """Raised when the API answers something unexpected."""


class VLMArtist:
    """An ASCII artist backed by a vision language model.

    Args:
        api_key: API key; falls back to ``ASCII3D_API_KEY`` then
            ``ZAI_API_KEY``.
        base_url: OpenAI-compatible API base; falls back to
            ``ASCII3D_API_BASE`` then the Z.ai endpoint.
        model: Model name; falls back to ``ASCII3D_VLM_MODEL`` then
            ``glm-4.5v``.
        timeout: Request timeout in seconds.
        transport: Optional callable ``(payload: dict) -> dict``
            replacing the HTTP call entirely -- used for tests and
            offline experiments.
    """

    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None, model: str | None = None,
                 timeout: float = 90.0, transport=None):
        self.api_key = (api_key
                        or os.environ.get('ASCII3D_API_KEY')
                        or os.environ.get('ZAI_API_KEY'))
        self.base_url = (base_url
                         or os.environ.get('ASCII3D_API_BASE')
                         or DEFAULT_BASE_URL).rstrip('/')
        self.model = (model
                      or os.environ.get('ASCII3D_VLM_MODEL')
                      or DEFAULT_MODEL)
        self.timeout = timeout
        self._transport = transport

    # ------------------------------------------------------------------
    # transport
    # ------------------------------------------------------------------
    def _chat(self, messages: list[dict], temperature: float = 0.7,
              max_tokens: int = 2048) -> str:
        """Run one chat completion and return the answer text.

        Args:
            messages: OpenAI-style message list.
            temperature: Sampling temperature.
            max_tokens: Response length cap.

        Returns:
            The assistant message content.

        Raises:
            VLMConfigError: No API key and no custom transport.
            VLMResponseError: HTTP or parsing failure.
        """
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        if self._transport is not None:
            body = self._transport(payload)
        else:
            if not self.api_key:
                raise VLMConfigError(
                    'no API key: set ASCII3D_API_KEY (or pass '
                    'api_key=...) to use the VLM features')
            body = self._http(payload)
        try:
            return body['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError) as exc:
            raise VLMResponseError(
                f'unexpected response shape: {str(body)[:200]}') from exc

    def _http(self, payload: dict) -> dict:
        """POST *payload* to the chat completions endpoint."""
        url = f'{self.base_url}/chat/completions'
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(
            url, data=data, method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            })
        try:
            with urllib.request.urlopen(request,
                                        timeout=self.timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:300].decode('utf-8', 'replace')
            raise VLMResponseError(
                f'HTTP {exc.code} from {self.base_url}: {detail}'
            ) from exc
        except urllib.error.URLError as exc:
            raise VLMResponseError(
                f'cannot reach {self.base_url}: {exc.reason}') from exc

    # ------------------------------------------------------------------
    # generation
    # ------------------------------------------------------------------
    def generate(self, prompt: str, rows: int = 12, cols: int = 40,
                 temperature: float = 0.8) -> str:
        """Generate an ASCII art from a text *prompt*.

        The art is returned normalized (no code fences, no trailing
        blanks) and can be fed straight into :func:`ascii3d.turn`,
        :func:`ascii3d.routes.route` or
        :func:`ascii3d.rotation.frames`.

        Args:
            prompt: What to draw, e.g. ``'a small house with a
                chimney'``.
            rows: Maximum number of art rows.
            cols: Maximum number of art columns.
            temperature: Sampling temperature (higher = bolder).

        Returns:
            The ASCII art as a string.

        Raises:
            VLMResponseError: If the answer contains no usable art.
        """
        system = (
            'You are an ASCII artist. You reply with EXACTLY one '
            'fenced code block and nothing else. The block contains '
            f'line art of at most {rows} rows and {cols} columns, '
            'built from these characters only: '
            f'{_ART_ALPHABET}. '
            'Prefer clean outlines made of _ | / \\ ( ) over dense '
            'shading; leave a margin of one space around the drawing.'
        )
        content = self._chat(
            [{'role': 'system', 'content': system},
             {'role': 'user', 'content': prompt}],
            temperature=temperature)
        art = _extract_art(content)
        if not art or not art.strip():
            raise VLMResponseError('the model did not return any art')
        if max(len(line) for line in art.split('\n')) > 4 * cols:
            raise VLMResponseError(
                'the model returned something that is not line art '
                f'(a line wider than {4 * cols} columns)')
        return art

    # ------------------------------------------------------------------
    # analysis
    # ------------------------------------------------------------------
    def describe(self, art: str, question: str | None = None) -> str:
        """Ask the model to describe an ASCII *art* (text only).

        Args:
            art: The ASCII art as a plain string.
            question: Optional focus, e.g. ``'what animal is this?''``.

        Returns:
            The model's answer.
        """
        ask = question or 'Describe this ASCII art in two sentences.'
        content = self._chat(
            [{'role': 'user',
              'content': f'{ask}\n\n```\n{art}\n```'}],
            temperature=0.3, max_tokens=512)
        return content.strip()

    def describe_render(self, art: str, direction: str = 'left',
                        depth: int | None = None,
                        question: str | None = None) -> str:
        """Render *art* in 3D and let the **vision** model look at it.

        The art is rendered through :func:`ascii3d.routes.route`,
        drawn to a PNG image (needs Pillow) and sent to the model as
        an actual image, so the VLM judges the 3D effect, not just
        the characters.

        Args:
            art: The ASCII art as a plain string.
            direction: One of the nine routes (``'left'``,
                ``'leftup'``, ...).
            depth: Depth of the 3D box (``None`` = auto).
            question: Optional focus for the description.

        Returns:
            The model's answer.

        Raises:
            ImportError: If Pillow is not installed.
        """
        from .raster import text_to_png_bytes
        from .routes import route
        frame = route(art, direction, depth=depth)
        png = text_to_png_bytes(frame, font_size=18)
        image_url = ('data:image/png;base64,'
                     + base64.b64encode(png).decode('ascii'))
        ask = question or (
            'This is an ASCII art rendered to look 3D. Does the 3D '
            'effect work? Describe the geometry you see in two '
            'sentences.')
        content = self._chat(
            [{'role': 'user', 'content': [
                {'type': 'text', 'text': ask},
                {'type': 'image_url', 'image_url': {'url': image_url}},
            ]}],
            temperature=0.3, max_tokens=512)
        return content.strip()

    def refine(self, art: str, instruction: str,
               temperature: float = 0.6) -> str:
        """Ask the model to redraw *art* following *instruction*.

        Args:
            art: The current ASCII art.
            instruction: What to change, e.g. ``'make it taller'``.
            temperature: Sampling temperature.

        Returns:
            The new ASCII art.

        Raises:
            VLMResponseError: If the answer contains no usable art.
        """
        system = (
            'You are an ASCII artist. You reply with EXACTLY one '
            'fenced code block containing the redrawn art and '
            'nothing else, using only these characters: '
            f'{_ART_ALPHABET}.')
        content = self._chat(
            [{'role': 'system', 'content': system},
             {'role': 'user',
              'content': f'Redraw this art: {instruction}\n\n```\n'
                         f'{art}\n```'}],
            temperature=temperature)
        new_art = _extract_art(content)
        if not new_art or not new_art.strip():
            raise VLMResponseError('the model did not return any art')
        return new_art

    # ------------------------------------------------------------------
    # pipeline helpers
    # ------------------------------------------------------------------
    def generate_and_turn(self, prompt: str, direction: str = 'left',
                          rows: int = 12, cols: int = 40,
                          depth: int | None = None) -> str:
        """Generate an art from *prompt* and turn it to *direction*.

        A one-call pipeline: VLM draws it, the 3D engine turns it.

        Args:
            prompt: What to draw.
            direction: One of the nine routes.
            rows: Maximum art rows for the generation.
            cols: Maximum art columns.
            depth: Depth of the 3D box (``None`` = auto).

        Returns:
            The turned ASCII art.
        """
        from .routes import route
        art = self.generate(prompt, rows=rows, cols=cols)
        return route(art, direction, depth=depth)

    def generate_and_spin(self, prompt: str, steps: int = 24,
                          rows: int = 12, cols: int = 40,
                          pitch: float = 20.0,
                          depth: int | None = None) -> list[str]:
        """Generate an art from *prompt* and spin it 360 degrees.

        Args:
            prompt: What to draw.
            steps: Number of rotation frames.
            rows: Maximum art rows for the generation.
            cols: Maximum art columns.
            pitch: Camera elevation of the turntable.
            depth: Depth of the 3D box (``None`` = auto).

        Returns:
            The rotation frames (all the same canvas size).
        """
        from .rotation import frames
        art = self.generate(prompt, rows=rows, cols=cols)
        return frames(art, steps=steps, pitch=pitch, depth=depth)


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
_FENCE_RE = re.compile(r'```[a-zA-Z0-9_-]*\s*\n(.*?)```', re.DOTALL)


def _extract_art(text: str) -> str:
    """Pull the art out of a model answer.

    Prefers a fenced code block, falls back to the whole text; the
    result is dedented, right-trimmed and empty lines at the edges
    are dropped.

    Args:
        text: The raw model answer.

    Returns:
        The extracted art.
    """
    match = _FENCE_RE.search(text)
    raw = match.group(1) if match else text
    lines = [line.rstrip() for line in raw.split('\n')]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return '\n'.join(lines)
