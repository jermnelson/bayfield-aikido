"""Render vertical kanji headings by wrapping each character in its own span.

Each `.kanji-vertical` element carries its text in a `data-kanji` attribute and
is left empty in the HTML. This module clones the `#kanji-char` <template> once
per character so the CSS flex column can space them evenly down the band.
"""

from js import document


def wrap_kanji(text):
    """Return a DocumentFragment with each character of `text` in a <span>."""
    template = document.getElementById("kanji-char")
    fragment = document.createDocumentFragment()
    for char in text:
        node = template.content.cloneNode(True)
        node.querySelector("span").textContent = char
        fragment.appendChild(node)
    return fragment


def mount():
    """Populate every empty .kanji-vertical heading from its data-kanji string."""
    headings = document.querySelectorAll(".kanji-vertical")
    for i in range(headings.length):
        heading = headings.item(i)
        heading.replaceChildren(wrap_kanji(heading.dataset.kanji))


mount()
