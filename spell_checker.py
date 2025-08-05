class SpellChecker:
    def __init__(self) -> None:
        self.index = 0

    def identify(self, directions: list[str]) -> str | None:
        spell = self.index % 3

        if spell == 0 and self.check_silencio(directions):
            self.index += 1
            return "silencio"

        if spell == 1 and self.check_incendio(directions):
            self.index += 1
            return "incendio"

        # if spell == 2 and self.check_slugulus_erecto:
        #     self.index += 1
        #     return "slugulus_erecto"

        if spell == 2 and self.check_locomotor(directions):
            self.index += 1
            return "locomotor"

        if len(directions) > 5:
            directions = directions[-5:]

    def check_silencio(self, directions: list[str]) -> bool:
        if len(directions) < 2:
            return False

        d1 = directions[-2]
        d2 = directions[-1]

        e1 = self._is_expected(d1, ["down", "down-left", "down"])
        e2 = self._is_expected(d2, ["down", "down-left", "down-right"])

        return e1 and e2

    def check_incendio(self, directions: list[str]) -> bool:
        if len(directions) < 3:
            return False

        d1 = directions[-3]
        d2 = directions[-2]
        d3 = directions[-1]

        e1 = self._is_expected(d1, ["up", "right", "up-right"])
        e2 = self._is_expected(d2, ["down", "right", "down-right"])
        e3 = self._is_expected(d3, ["left", "up", "up-left"])

        return e1 and e2 and e3

    def check_locomotor(self, directions: list[str]) -> bool:
        if len(directions) < 3:
            return False

        d1 = directions[-3]
        d2 = directions[-2]
        d3 = directions[-1]

        e1 = self._is_expected(d1, ["up", "up-left", "up-right"])
        e2 = self._is_expected(d2, ["down", "left", "down-left"])
        e3 = self._is_expected(d3, ["right", "up-right", "down-right"])

        return e1 and e2 and e3

    def check_slugulus_erecto(self, directions: list[str]) -> bool:
        if len(directions) < 4:
            return False

        d1 = directions[-4]
        d2 = directions[-3]
        d3 = directions[-2]
        d4 = directions[-1]

        e1 = self._is_expected(d1, ["down", "down-left"])
        e2 = self._is_expected(d2, ["down-left", "left"])
        e3 = self._is_expected(d3, ["up", "up-right"])
        e4 = self._is_expected(d4, ["up-right", "right"])

        return e1 and e2 and e3 and e4

    def _is_expected(self, actual: str, expected: list[str]) -> bool:
        return actual in expected
