"""Localised console messages (es, ca, en, gl, eu). Every key exists in every language (enforced by a test)."""
from __future__ import annotations

from .texts_ca import TEXTS as CA
from .texts_en import TEXTS as EN
from .texts_es import TEXTS as ES
from .texts_eu import TEXTS as EU
from .texts_gl import TEXTS as GL

LANGUAGES = ("es", "ca", "en", "gl", "eu")
DEFAULT_LANGUAGE = "es"
MESSAGES: dict[str, dict[str, str]] = {"es": ES, "ca": CA, "en": EN, "gl": GL, "eu": EU}


def tr(lang: str, key: str, **kw: object) -> str:
    table = MESSAGES.get(lang, ES)
    return table[key].format(**kw)
