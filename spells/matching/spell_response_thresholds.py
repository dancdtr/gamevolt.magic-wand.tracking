from dataclasses import dataclass

from spells.spell_response_type import SpellResponseType


@dataclass
class SpellResponseThresholds:
    responses: dict[SpellResponseType, int]
    # eg:
    # OK : 50
    # GOOD: 60
    # BETTER: 75
    # BEST: 90

    def get_response_type(self, spell_cast_rating: float) -> SpellResponseType:
        best_match = SpellResponseType.FAIL
        best_threshold = float("-inf")
        for response_type, threshold in self.responses.items():
            if spell_cast_rating >= threshold and threshold > best_threshold:
                best_match = response_type
                best_threshold = threshold
        return best_match
