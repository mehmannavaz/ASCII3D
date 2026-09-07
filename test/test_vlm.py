"""Tests for the VLM artist (offline, with a fake transport)."""

import base64

import pytest

from ascii3d.examples import EXAMPLES
from ascii3d.vlm import (DEFAULT_BASE_URL, DEFAULT_MODEL, VLMArtist,
                         VLMConfigError, VLMResponseError, _extract_art)
CAT = EXAMPLES['vlm_cat']


def reply(text):
    """Build a fake OpenAI-style response."""
    return {'choices': [{'message': {'content': text}}]}


def artist_with(text):
    return VLMArtist(transport=lambda payload: reply(text))


class TestConfiguration:
    def test_defaults(self, monkeypatch):
        for var in ('ASCII3D_API_KEY', 'ASCII3D_API_BASE',
                    'ASCII3D_VLM_MODEL', 'ZAI_API_KEY'):
            monkeypatch.delenv(var, raising=False)
        artist = VLMArtist()
        assert artist.api_key is None
        assert artist.base_url == DEFAULT_BASE_URL
        assert artist.model == DEFAULT_MODEL

    def test_environment_overrides(self, monkeypatch):
        monkeypatch.setenv('ASCII3D_API_KEY', 'k-123')
        monkeypatch.setenv('ASCII3D_API_BASE', 'https://example.com/v1')
        monkeypatch.setenv('ASCII3D_VLM_MODEL', 'some-model')
        artist = VLMArtist()
        assert artist.api_key == 'k-123'
        assert artist.base_url == 'https://example.com/v1'
        assert artist.model == 'some-model'

    def test_missing_key_raises_a_helpful_error(self, monkeypatch):
        for var in ('ASCII3D_API_KEY', 'ZAI_API_KEY'):
            monkeypatch.delenv(var, raising=False)
        artist = VLMArtist()
        with pytest.raises(VLMConfigError, match='ASCII3D_API_KEY'):
            artist.generate('a cat')

    def test_bad_response_shape_raises(self):
        artist = VLMArtist(transport=lambda payload: {'nope': 1})
        with pytest.raises(VLMResponseError):
            artist.generate('a cat')


class TestGenerate:
    def test_fenced_answer_is_extracted(self):
        artist = artist_with(f'Sure!\n```\n{CAT}\n```\nHope you like it')
        assert artist.generate('a cat') == CAT.rstrip('\n')

    def test_unfenced_answer_still_works(self):
        artist = artist_with(CAT)
        assert artist.generate('a cat').strip()

    def test_generate_result_can_be_turned(self):
        art = artist_with(f'```\n{CAT}\n```')
        generated = art.generate('a cat')
        from ascii3d.engine import turn
        rendered = turn(generated, 'left', depth=2)
        assert rendered.strip()

    def test_empty_answer_is_rejected(self):
        artist = artist_with('```\n\n```')
        with pytest.raises(VLMResponseError, match='did not return'):
            artist.generate('a cat')

    def test_non_art_answer_is_rejected(self):
        artist = artist_with('x' * 500)
        with pytest.raises(VLMResponseError, match='not line art'):
            artist.generate('a cat')

    def test_payload_shape(self):
        seen = {}

        def transport(payload):
            seen.update(payload)
            return reply(f'```\n{CAT}\n```')

        VLMArtist(transport=transport).generate('a cat', rows=9,
                                                cols=33)
        assert seen['model'] == DEFAULT_MODEL
        assert seen['messages'][0]['role'] == 'system'
        assert '9 rows' in seen['messages'][0]['content']
        assert '33 columns' in seen['messages'][0]['content']


class TestDescribe:
    def test_describe_returns_the_answer(self):
        artist = artist_with('It is a cat sitting down.')
        assert artist.describe(CAT) == 'It is a cat sitting down.'

    def test_describe_includes_the_art(self):
        seen = {}

        def transport(payload):
            seen.update(payload)
            return reply('a cat')

        VLMArtist(transport=transport).describe(CAT, 'what animal?')
        user = seen['messages'][0]['content']
        assert 'what animal?' in user
        assert '|' in user  # the art travels along

    def test_describe_render_sends_a_real_image(self):
        seen = {}

        def transport(payload):
            seen.update(payload)
            return reply('The 3D effect works.')

        artist = VLMArtist(transport=transport)
        answer = artist.describe_render(CAT, direction='left')
        assert answer == 'The 3D effect works.'
        content = seen['messages'][0]['content']
        image_part = next(part for part in content
                          if part.get('type') == 'image_url')
        url = image_part['image_url']['url']
        assert url.startswith('data:image/png;base64,')
        payload = url.split(',', 1)[1]
        png = base64.b64decode(payload)
        assert png[:8] == b'\x89PNG\r\n\x1a\n'


class TestRefineAndPipelines:
    def test_refine_returns_the_new_art(self):
        better = ' ___\n|   |\n|_ _|'
        artist = artist_with(f'```\n{better}\n```')
        refined = artist.refine(CAT, 'make it smaller')
        assert refined == better

    def test_generate_and_turn(self):
        artist = artist_with(f'```\n{CAT}\n```')
        rendered = artist.generate_and_turn('a cat', direction='left')
        assert rendered.strip()

    def test_generate_and_spin(self):
        artist = artist_with(f'```\n{CAT}\n```')
        timeline = artist.generate_and_spin('a cat', steps=4)
        assert len(timeline) == 4
        widths = {max(len(line) for line in f.split('\n'))
                  for f in timeline}
        assert len(widths) == 1


class TestExtraction:
    def test_fenced_with_language_tag(self):
        assert _extract_art('```text\nab\n```') == 'ab'

    def test_blank_edges_are_dropped(self):
        assert _extract_art('```\n\nab\n\n```') == 'ab'

    def test_plain_text_passthrough(self):
        assert _extract_art('ab\ncd') == 'ab\ncd'
