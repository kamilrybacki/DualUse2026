"""Round-trip tests for the SITOR-B generator with a minimal *test-only* FSK demodulator
(known bit timing, no clock recovery — this is not a decoder for the product; fldigi is)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from tools import gen_sitorb, sitorb


def demod_bits(
    audio: np.ndarray, p: sitorb.FskParams, n_bits: int, lead_s: float = 0.5
) -> list[int]:
    """Per-bit tone correlation at the known bit boundaries (test helper)."""
    spb = p.samples_per_bit
    start = int(lead_s * p.sample_rate)
    t = np.arange(int(round(spb))) / p.sample_rate
    mark = np.exp(2j * np.pi * p.mark_hz * t)
    space = np.exp(2j * np.pi * p.space_hz * t)
    bits = []
    for i in range(n_bits):
        a = start + int(round(i * spb))
        seg = audio[a : a + len(t)]
        if len(seg) < len(t):
            break
        bits.append(1 if abs(np.dot(seg, mark)) > abs(np.dot(seg, space)) else 0)
    return bits


def bits_to_codes(bits: list[int]) -> list[int]:
    return [
        sum(bit << b for b, bit in enumerate(bits[i : i + 7])) for i in range(0, len(bits) - 6, 7)
    ]


def fec_decode(slots: list[int], phasing_pairs: int) -> list[int]:
    """DX with RX fallback (5 slots later); both invalid → -1. Mirrors the decoder's rule."""
    start = 2 * phasing_pairs
    out = []
    for dx in range(start, len(slots) - 5, 2):
        a, b = slots[dx], slots[dx + 5]
        if a == sitorb.CODE_REP and b == sitorb.CODE_REP:
            break  # idle tail
        if sitorb.is_valid_code(a):
            out.append(a)
        elif sitorb.is_valid_code(b):
            out.append(b)
        else:
            out.append(-1)
    return out


def test_code_table_is_four_of_seven() -> None:
    for code in list(sitorb.LTRS_TO_CODE.values()) + list(sitorb.FIGS_TO_CODE.values()):
        assert sitorb.is_valid_code(code), code
    for special in (sitorb.CODE_LTRS, sitorb.CODE_FIGS, sitorb.CODE_ALPHA, sitorb.CODE_REP):
        assert sitorb.is_valid_code(special)
    assert sitorb.LTRS_TO_CODE["A"] == 0x47 and sitorb.FIGS_TO_CODE["1"] == 0x2E
    assert sitorb.CODE_SPACE == 0x5C and sitorb.CODE_CR == 0x78 and sitorb.CODE_LF == 0x6C


def test_text_codes_round_trip_with_shifts() -> None:
    text = "ZCZC IA47\n57-18.2N 011-56.5E UNLIT.\nNNNN"
    codes = sitorb.text_to_codes(text)
    assert sitorb.CODE_FIGS in codes and sitorb.CODE_LTRS in codes
    assert sitorb.codes_to_text(codes) == text


def test_frame_layout_matches_jnx_reference() -> None:
    # "NAUTICAL" → rep alpha rep alpha N alpha A alpha U N T A I U C T A I L C ...
    slots = sitorb.frame(sitorb.text_to_codes("NAUTICAL"), phasing_pairs=2, tail_pairs=0)
    want = [sitorb.LTRS_TO_CODE[c] if c.isalpha() else c for c in "NAUTICAL"]
    n, a, u, t, i, c, el = (sitorb.LTRS_TO_CODE[x] for x in "NAUTICL")
    rep, alpha = sitorb.CODE_REP, sitorb.CODE_ALPHA
    assert slots[:16] == [rep, alpha, rep, alpha, n, alpha, a, alpha, u, n, t, a, i, u, c, t]
    assert slots[16:22] == [a, i, el, c, rep, a]  # after the last DX the RX copies drain
    assert len(want) == 8


def test_audio_round_trip_clean() -> None:
    text = "ZCZC IA47\nSWEDISH NAV WARNING 312\nKATTEGAT. BUOY 57-18.2N 011-56.5E UNLIT.\nNNNN"
    p = sitorb.FskParams(sample_rate=8000, center_hz=1000.0)
    audio, meta = sitorb.generate(text, p, phasing_pairs=4)
    assert meta["killed"] == [] and meta["expected_text"] == text
    bits = demod_bits(audio, p, meta["slots"] * 7)
    codes = fec_decode(bits_to_codes(bits), phasing_pairs=4)
    assert sitorb.codes_to_text(codes) == text


def test_audio_round_trip_with_noise_and_fec() -> None:
    text = "ZCZC JA05\nFIRING EXERCISE 12 SEP 1000 UTC TO 1600 UTC.\nNNNN"
    p = sitorb.FskParams(sample_rate=8000, center_hz=1000.0)
    audio, meta = sitorb.generate(
        text, p, error_rate=0.15, error_mode="random", snr_db=15, seed=3, phasing_pairs=4
    )
    bits = demod_bits(audio, p, meta["slots"] * 7)
    decoded = sitorb.codes_to_text(fec_decode(bits_to_codes(bits), 4))
    # single-slot bit flips are mostly repaired by the RX copy: few stars, text readable
    assert decoded.count("*") <= 0.05 * len(text)
    assert "FIRING EXERCISE" in decoded


def test_burst_errors_produce_stars_at_expected_rate() -> None:
    text = (
        "ZCZC HB13\nGALE WARNING 118 BOTHNIAN SEA SOUTHWEST 8 INCREASING 9 ROUGH SEA\n" * 4
    ) + "NNNN"
    p = sitorb.FskParams(sample_rate=8000, center_hz=1000.0)
    audio, meta = sitorb.generate(
        text, p, error_rate=0.1, error_mode="burst", seed=1, phasing_pairs=4
    )
    n_killed = len(meta["killed"])
    assert 0.05 * meta["chars"] < n_killed < 0.16 * meta["chars"]
    bits = demod_bits(audio, p, meta["slots"] * 7)
    codes = fec_decode(bits_to_codes(bits), 4)
    assert codes.count(-1) == n_killed  # every burst-killed character is unrecoverable
    decoded = sitorb.codes_to_text(codes)
    # stars appear only where shift codes were not the victim; count is within reason
    assert 0 < decoded.count("*") <= n_killed
    assert abs(meta["expected_star_rate"] - n_killed / meta["chars"]) < 1e-4


def test_cli_writes_wav_and_meta(tmp_path: Path) -> None:
    out = tmp_path / "t.wav"
    rc = gen_sitorb.main(
        ["--fixture", "08_navtex_en_gale_warning", "--out", str(out), "--error-rate", "0.05"]
    )
    assert rc == 0 and out.exists()
    meta = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert meta["chars"] > 100 and meta["duration_s"] > 10
    import wave

    with wave.open(str(out)) as w:
        assert w.getframerate() == 8000 and w.getnchannels() == 1


def test_kiwi_iq_path_round_trips_through_iq_to_audio(tmp_path: Path) -> None:
    """Synthetic KiwiSDR IQ wav (kiwi chunks interleaved) → iq_to_audio → test demod → text."""
    from tools.fldigi import iq_to_audio as i2a

    text = "ZCZC UA11\nTALLINN RADIO NAV WARNING 44\nGULF OF FINLAND. BUOY UNLIT.\nNNNN"
    p = sitorb.FskParams(sample_rate=12000)
    iq, meta = sitorb.generate(text, p, phasing_pairs=4, iq=True)
    assert iq.dtype == np.complex64
    wav = tmp_path / "navtex_U_20260907_1920.wav"
    sitorb.write_kiwi_iq_wav(wav, 12000, iq)
    rate, iq_back = i2a.read_iq_wav(wav)
    assert rate == 12000 and abs(len(iq_back) - len(iq)) < 4
    audio = i2a.iq_to_audio(iq_back, rate, audio_center=1000.0)
    pa = sitorb.FskParams(sample_rate=12000, center_hz=1000.0)
    bits = demod_bits(audio, pa, meta["slots"] * 7)
    decoded = sitorb.codes_to_text(fec_decode(bits_to_codes(bits), 4))
    assert decoded == text
    # the stdlib wave module sees only the first 'data' chunk (that is why iq_to_audio exists)
    import wave

    with wave.open(str(wav), "rb") as w:
        assert w.getnframes() < len(iq) / 4


@pytest.mark.parametrize("mode", ["burst", "random"])
def test_corrupt_is_deterministic(mode: str) -> None:
    slots = sitorb.frame(sitorb.text_to_codes("HELLO WORLD"), phasing_pairs=2)
    a, ka = sitorb.corrupt(slots, 0.3, seed=7, mode=mode, phasing_pairs=2)
    b, kb = sitorb.corrupt(slots, 0.3, seed=7, mode=mode, phasing_pairs=2)
    assert a == b and ka == kb
