from gamevolt.configuration.appsetting import appsetting


@appsetting
class ConfusionGuardSettings:
    """Rejects a cast when some *other* template (one not in the zone-active set) matches the
    drawn shape better than the chosen spell does. $1 absolute scores are forgiving — a perfect
    LUMOS still scores ~67% against REVELIO — so a loose match can clear the gate when its
    true shape isn't an active candidate. $1 is a 1-NN classifier: the discriminative signal is
    the *ranking*, not the absolute score. This guard restores that by scoring against every
    template and vetoing when the chosen spell is out-ranked by more than `margin`."""

    enabled: bool
    margin: float  # an out-of-set template must beat the chosen score by more than this (0..1) to veto
