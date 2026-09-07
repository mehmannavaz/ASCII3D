# VLM arts: ASCII generated and judged by a vision model

ASCII3D can talk to any **OpenAI-compatible** chat completions API
(the default points at the Z.ai endpoint) and use it in both
directions:

* **generation** -- describe a drawing in words, the model answers
  with ASCII line art, and the engine turns and spins it like any
  other art;
* **analysis** -- show the model an art as text, or a *rendered 3D
  frame* as a real PNG image, and ask it what it sees.

The module is `ascii3d.vlm` and its main character is
`VLMArtist`.

## Configuration

| Environment variable | Meaning | Default |
|---------------------|---------|---------|
| `ASCII3D_API_KEY` | the API key | *(none -- required)* |
| `ASCII3D_API_BASE` | OpenAI-compatible base URL | `https://api.z.ai/api/paas/v4` |
| `ASCII3D_VLM_MODEL` | model name | `glm-4.5v` |

All three can also be passed to the `VLMArtist` constructor.

## Generating art

```python
from ascii3d.vlm import VLMArtist

artist = VLMArtist()  # reads ASCII3D_API_KEY
cat = artist.generate('a sitting cat, side view, clean outline')
print(cat)
```
```
         _
       _/ \_
     _/     \_
    /         \
   |  o     o  |
   |    \_/    |
   |     |     |
    \   / \   /
     \_/   \_/
      |     |
      |     |
      |_____|
```

The generated art is a first-class citizen -- turn it, route it,
spin it:

```python
print(artist.generate_and_turn('a small house', 'left'))
timeline = artist.generate_and_spin('a rocket', steps=24)
```

(These four drawings ship as the `vlm_cat`, `vlm_house`,
`vlm_rocket` and `vlm_robot` examples -- they were produced by a
vision model with exactly this prompt.)

## Letting the model look at your art

Text mode:

```python
print(artist.describe(cat, question='what animal is this?'))
```

Vision mode -- the art is rendered through a route, drawn to a PNG
and sent as an actual image, so the model judges the 3D effect:

```python
print(artist.describe_render(cat, direction='leftup'))
# 'Yes, the 3D effect works. The image depicts a cube in isometric
#  perspective, showing the top, front-left, and front-right faces...'
```

## Command line

```shell
ascii3d --vlm "a dragon" -t leftup   # generate, then render
ascii3d --vlm "a dragon" --raw       # print the raw art
ascii3d -e vlm_cat --vlm-describe    # text critique
ascii3d -e vlm_cat --vlm-vision      # image critique of the render
```

## Offline / testing

`VLMArtist(transport=...)` replaces the HTTP call with any
`payload -> response` callable, which is how the test suite exercises
the whole pipeline without a key.
