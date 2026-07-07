from __future__ import annotations

import logging
from pathlib import Path

from gamevolt.logging._levels import register_custom_levels
from gamevolt.logging._logger import Logger
from spells.spell_tag import SpellTag
from spells.spell_tags import load_spell_tags
from spells.spell_type import SpellType


def _logger() -> Logger:
    register_custom_levels()
    logging.setLoggerClass(Logger)
    log = logging.getLogger("test.spell_tags")
    log.setLevel(logging.WARNING)
    return log  # type: ignore[return-value]


def test_every_spell_tagged() -> None:
    tags = load_spell_tags(_logger())
    expected = {s for s in SpellType if s is not SpellType.NONE}
    assert set(tags) == expected
    assert all(tags[spell] for spell in expected)


def test_primer_and_cdtr_are_exclusive() -> None:
    tags = load_spell_tags(_logger())
    for spell, spell_tags in tags.items():
        assert (SpellTag.PRIMER in spell_tags) != (SpellTag.CDTR in spell_tags), spell


def test_park_spells_are_primer() -> None:
    # The park curation is (currently) a Primer subset; a CDTR spell tagged park
    # would be a curation change, not a typo — revisit this if that happens.
    tags = load_spell_tags(_logger())
    for spell, spell_tags in tags.items():
        if SpellTag.PARK in spell_tags:
            assert SpellTag.PRIMER in spell_tags, spell


def test_cdtr_originals_tagged() -> None:
    tags = load_spell_tags(_logger())
    for spell in (
        SpellType.ARCUBOLTUS,
        SpellType.BARRAGIUM,
        SpellType.CONDUC_TERRIFICUS,
        SpellType.HELPUS_HANDIUS,
        SpellType.INSPIRIO,
        SpellType.PUCK_HURLING_CHARM,
        SpellType.TACO_TEMPESTAS,
    ):
        assert tags[spell] == frozenset({SpellTag.CDTR})


def test_missing_file_degrades_to_all_primer() -> None:
    tags = load_spell_tags(_logger(), Path("/nonexistent/spell_tags.yml"))
    assert all(spell_tags == frozenset({SpellTag.PRIMER}) for spell_tags in tags.values())
