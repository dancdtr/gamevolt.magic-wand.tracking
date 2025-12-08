from typing import Callable

from spells.library.alohomora import alohomora
from spells.library.aparecium import aparecium
from spells.library.arresto_momentum import arresto_momentum
from spells.library.cantis import cantis
from spells.library.colloportus import colloportus
from spells.library.colovaria import colovaria
from spells.library.densaeguo import densaeguo
from spells.library.engorgio import engorgio
from spells.library.expecto_patronum import expecto_patronum
from spells.library.flipendo import flipendo
from spells.library.herbivicius import herbivicius
from spells.library.horn_tongue import horn_tongue
from spells.library.immobulus import immobulus
from spells.library.incendio import incendio
from spells.library.inflatus import inflatus
from spells.library.locomotor import locomotor
from spells.library.lumos_maxima import lumos_maxima
from spells.library.meteolojinx import meteolojinx
from spells.library.nebulus import nebulus
from spells.library.none_spell import none_spell
from spells.library.pepper_breath import pepper_breath
from spells.library.piertotum_locomotor import piertotum_locomotor
from spells.library.reparo import reparo
from spells.library.revelio import revelio
from spells.library.rictumsempra import rictumsempra
from spells.library.silencio import silencio
from spells.library.slugulus_erecto import slugulus_erecto
from spells.library.switching import switching
from spells.library.ventus import ventus
from spells.library.vera_verto import vera_verto
from spells.library.wingardium_leviosa import wingardium_leviosa
from spells.spell_definition import SpellDefinition
from spells.spell_type import SpellType

_SPELL_PROVIDERS: dict[SpellType, Callable[[], SpellDefinition]] = {
    SpellType.NONE: none_spell,
    SpellType.ALOHOMORA: alohomora,
    SpellType.APARECIUM: aparecium,
    SpellType.ARRESTO_MOMENTUM: arresto_momentum,
    SpellType.CANTIS: cantis,
    SpellType.COLLOPORTUS: colloportus,
    SpellType.COLOVARIA: colovaria,
    SpellType.DENSAUGEO: densaeguo,
    SpellType.ENGORGIO: engorgio,
    SpellType.EXPECTO_PATRONUM: expecto_patronum,
    SpellType.FLIPENDO: flipendo,
    SpellType.HERBIVICIUS: herbivicius,
    SpellType.HORN_TONGUE: horn_tongue,
    SpellType.IMMOBULUS: immobulus,
    SpellType.INCENDIO: incendio,
    SpellType.INFLATUS: inflatus,
    SpellType.LOCOMOTOR: locomotor,
    SpellType.LUMOS_MAXIMA: lumos_maxima,
    SpellType.METEOLOJINX: meteolojinx,
    SpellType.NEBULUS: nebulus,
    SpellType.PEPPER_BREATH: pepper_breath,
    SpellType.PIERTOTUM_LOCOMOTOR: piertotum_locomotor,
    SpellType.REPARO: reparo,
    SpellType.REVELIO: revelio,
    SpellType.RICTUMSEMPRA: rictumsempra,
    SpellType.SILENCIO: silencio,
    SpellType.SLUGULUS_ERECTO: slugulus_erecto,
    SpellType.SWITCHING: switching,
    SpellType.VENTUS: ventus,
    SpellType.VERA_VERTO: vera_verto,
    SpellType.WINGARDIUM_LEVIOSA: wingardium_leviosa,
}


class SpellDefinitionFactory:
    def create_spells(self, spell_types: list[SpellType]) -> list[SpellDefinition]:
        return [self.create_spell(spell_type) for spell_type in spell_types]

    def create_spell(self, spell_type: SpellType) -> SpellDefinition:
        provider = _SPELL_PROVIDERS.get(spell_type, None)

        if not provider:
            raise ValueError(f"No spell definition for type: '{spell_type.name}'!")

        return provider()
