from __future__ import annotations

from enum import StrEnum


class GestureType(StrEnum):
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

    # =========================================
    # 16-point compass directions
    # =========================================
    LINE_N = "LINE_N"
    LINE_E = "LINE_E"
    LINE_S = "LINE_S"
    LINE_W = "LINE_W"

    LINE_NE = "LINE_NE"
    LINE_SE = "LINE_SE"
    LINE_SW = "LINE_SW"
    LINE_NW = "LINE_NW"

    LINE_NNE = "LINE_NNE"
    LINE_ENE = "LINE_ENE"
    LINE_ESE = "LINE_ESE"
    LINE_SSE = "LINE_SSE"
    LINE_SSW = "LINE_SSW"
    LINE_WSW = "LINE_WSW"
    LINE_WNW = "LINE_WNW"
    LINE_NNW = "LINE_NNW"

    # =========================================
    # Arcs 180
    # =========================================
    ARC_180_CW_START_N = "ARC_180_CW_START_N"
    ARC_180_CW_START_E = "ARC_180_CW_START_E"
    ARC_180_CW_START_S = "ARC_180_CW_START_S"
    ARC_180_CW_START_W = "ARC_180_CW_START_W"

    ARC_180_CCW_START_N = "ARC_180_CCW_START_N"
    ARC_180_CCW_START_E = "ARC_180_CCW_START_E"
    ARC_180_CCW_START_S = "ARC_180_CCW_START_S"
    ARC_180_CCW_START_W = "ARC_180_CCW_START_W"

    # =========================================
    # Arcs 270
    # =========================================
    ARC_270_CW_START_N = "ARC_270_CW_START_N"
    ARC_270_CW_START_E = "ARC_270_CW_START_E"
    ARC_270_CW_START_S = "ARC_270_CW_START_S"
    ARC_270_CW_START_W = "ARC_270_CW_START_W"

    ARC_270_CCW_START_N = "ARC_270_CCW_START_N"
    ARC_270_CCW_START_E = "ARC_270_CCW_START_E"
    ARC_270_CCW_START_S = "ARC_270_CCW_START_S"
    ARC_270_CCW_START_W = "ARC_270_CCW_START_W"

    # =========================================
    # Arcs 360
    # =========================================
    ARC_360_CW_START_N = "ARC_360_CW_START_N"
    ARC_360_CW_START_E = "ARC_360_CW_START_E"
    ARC_360_CW_START_S = "ARC_360_CW_START_S"
    ARC_360_CW_START_W = "ARC_360_CW_START_W"

    ARC_360_CCW_START_N = "ARC_360_CCW_START_N"
    ARC_360_CCW_START_E = "ARC_360_CCW_START_E"
    ARC_360_CCW_START_S = "ARC_360_CCW_START_S"
    ARC_360_CCW_START_W = "ARC_360_CCW_START_W"

    # =========================================
    # Arcs 450
    # =========================================
    ARC_450_CW_START_N = "ARC_450_CW_START_N"
    ARC_450_CW_START_E = "ARC_450_CW_START_E"
    ARC_450_CW_START_S = "ARC_450_CW_START_S"
    ARC_450_CW_START_W = "ARC_450_CW_START_W"

    ARC_450_CCW_START_N = "ARC_450_CCW_START_N"
    ARC_450_CCW_START_E = "ARC_450_CCW_START_E"
    ARC_450_CCW_START_S = "ARC_450_CCW_START_S"
    ARC_450_CCW_START_W = "ARC_450_CCW_START_W"

    # =========================================
    # Sine 360 waves
    # =========================================
    WAVE_SINE_360_N = "WAVE_SINE_360_N"
    WAVE_SINE_360_E = "WAVE_SINE_360_E"
    WAVE_SINE_360_S = "WAVE_SINE_360_S"
    WAVE_SINE_360_W = "WAVE_SINE_360_W"
    WAVE_NEGATIVE_SINE_360_N = "WAVE_NEGATIVE_SINE_360_N"
    WAVE_NEGATIVE_SINE_360_E = "WAVE_NEGATIVE_SINE_360_E"
    WAVE_NEGATIVE_SINE_360_S = "WAVE_NEGATIVE_SINE_360_S"
    WAVE_NEGATIVE_SINE_360_W = "WAVE_NEGATIVE_SINE_360_W"

    # =========================================
    # Sine 540 waves
    # =========================================
    WAVE_SINE_540_N = "WAVE_SINE_540_N"
    WAVE_SINE_540_E = "WAVE_SINE_540_E"
    WAVE_SINE_540_S = "WAVE_SINE_540_S"
    WAVE_SINE_540_W = "WAVE_SINE_540_W"
    WAVE_NEGATIVE_SINE_540_N = "WAVE_NEGATIVE_SINE_540_N"
    WAVE_NEGATIVE_SINE_540_E = "WAVE_NEGATIVE_SINE_540_E"
    WAVE_NEGATIVE_SINE_540_S = "WAVE_NEGATIVE_SINE_540_S"
    WAVE_NEGATIVE_SINE_540_W = "WAVE_NEGATIVE_SINE_540_W"

    # =========================================
    # Crooks
    # =========================================
    CROOK_N_CW = "CROOK_N_CW"
    CROOK_E_CW = "CROOK_E_CW"
    CROOK_S_CW = "CROOK_S_CW"
    CROOK_W_CW = "CROOK_W_CW"
    CROOK_N_CCW = "CROOK_N_CCW"
    CROOK_E_CCW = "CROOK_E_CCW"
    CROOK_S_CCW = "CROOK_S_CCW"
    CROOK_W_CCW = "CROOK_W_CCW"

    INVERSE_CROOK_N_CW = "INVERSE_CROOK_N_CW"
    INVERSE_CROOK_E_CW = "INVERSE_CROOK_E_CW"
    INVERSE_CROOK_S_CW = "INVERSE_CROOK_S_CW"
    INVERSE_CROOK_W_CW = "INVERSE_CROOK_W_CW"
    INVERSE_CROOK_N_CCW = "INVERSE_CROOK_N_CCW"
    INVERSE_CROOK_E_CCW = "INVERSE_CROOK_E_CCW"
    INVERSE_CROOK_S_CCW = "INVERSE_CROOK_S_CCW"
    INVERSE_CROOK_W_CCW = "INVERSE_CROOK_W_CCW"

    # =========================================
    # Crooks
    # =========================================
    HOOK_N_CW = "HOOK_N_CW"
    HOOK_E_CW = "HOOK_E_CW"
    HOOK_S_CW = "HOOK_S_CW"
    HOOK_W_CW = "HOOK_W_CW"
    HOOK_N_CCW = "HOOK_N_CCW"
    HOOK_E_CCW = "HOOK_E_CCW"
    HOOK_S_CCW = "HOOK_S_CCW"
    HOOK_W_CCW = "HOOK_W_CCW"

    INVERSE_HOOK_N_CW = "INVERSE_HOOK_N_CW"
    INVERSE_HOOK_E_CW = "INVERSE_HOOK_E_CW"
    INVERSE_HOOK_S_CW = "INVERSE_HOOK_S_CW"
    INVERSE_HOOK_W_CW = "INVERSE_HOOK_W_CW"
    INVERSE_HOOK_N_CCW = "INVERSE_HOOK_N_CCW"
    INVERSE_HOOK_E_CCW = "INVERSE_HOOK_E_CCW"
    INVERSE_HOOK_S_CCW = "INVERSE_HOOK_S_CCW"
    INVERSE_HOOK_W_CCW = "INVERSE_HOOK_W_CCW"

    # =========================================
    # Utils
    # =========================================
    def is_arc(self) -> bool:
        return self.value.startswith("ARC_")

    def is_line(self) -> bool:
        return self.value.startswith("LINE_")

    def is_wave(self) -> bool:
        return self.value.startswith("WAVE_")

    def is_crook(self) -> bool:
        return self.value.startswith("CROOK_")

    def is_inverse_crook(self) -> bool:
        return self.value.startswith("INVERSE_CROOK_")
