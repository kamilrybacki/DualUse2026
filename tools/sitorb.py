"""CCIR 476 / SITOR-B (NAVTEX) encoder primitives — test-signal generation only.

Code table, special codes, bit order and the phasing/interleave layout follow fldigi's
navtex decoder (src/navtex/navtex.cxx, GPL — only the *tables* are reproduced here, as
data) so that generated audio decodes in the fldigi rig. Reference: ITU-R M.476/M.625 and
the baltic-lab.com SITOR-B test-signal article.

Layout of a Mode B (FEC) transmission, one 7-bit character per 70 ms slot at 100 Bd:

    slot:   0    1     2    3     4    5     6    7     8    9    10   11 ...
            REP  ALPHA REP  ALPHA DX1  ALPHA DX2  ALPHA DX3  RX1  DX4  RX2 ...

Even slots carry the direct (DX) character, odd slots the repeat (RX) of the character
sent 5 slots (350 ms) earlier; ALPHA fills RX slots that have no repeat yet. Bits are
transmitted least-significant first; a 1 bit is the mark tone (centre + 85 Hz).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

import numpy as np

BAUD = 100.0
SHIFT_HZ = 170.0
BITS_PER_CHAR = 7

CODE_LTRS = 0x5A
CODE_FIGS = 0x36
CODE_ALPHA = 0x0F  # phasing signal in RX slots
CODE_REP = 0x66  # phasing signal in DX slots
CODE_SPACE = 0x5C
CODE_CR = 0x78
CODE_LF = 0x6C

# code → character, letters shift (index = 7-bit code, bit 0 sent first). '_' = unused.
_LTRS = (
    "________________"
    "_______J___F_CK_"
    "_______W___Y_PQ_"
    "_____G___MX_V___"
    "_______A___S_IU_"
    "___D_RE__N__ ___"
    "___Z_L___H__\n___"
    "_OB_T___\r_______"
)
_FIGS = (
    "________________"
    "_______'___!_:(_"
    "_______2___6_01_"
    "_____&___./_;___"
    "_______-___\x07_87_"
    "___$_43__,__ ___"
    '___"_)___#__\n___'
    "_9?_5___\r_______"
)
assert len(_LTRS) == 128 and len(_FIGS) == 128

LTRS_TO_CODE: dict[str, int] = {c: i for i, c in enumerate(_LTRS) if c != "_"}
FIGS_TO_CODE: dict[str, int] = {c: i for i, c in enumerate(_FIGS) if c != "_"}
CODE_TO_LTRS: dict[int, str] = {i: c for i, c in enumerate(_LTRS) if c != "_"}
CODE_TO_FIGS: dict[int, str] = {i: c for i, c in enumerate(_FIGS) if c != "_"}


def is_valid_code(code: int) -> bool:
    """CCIR 476: exactly four 1 bits (marks) in seven."""
    return 0 <= code < 128 and bin(code).count("1") == 4


def text_to_codes(text: str) -> list[int]:
    """Text → CCIR 476 codes with LTRS/FIGS shifting. Unsupported chars are dropped."""
    codes: list[int] = []
    figs = False
    for ch in text.upper().replace("\r\n", "\n"):
        if ch == "\n":
            codes += [CODE_CR, CODE_LF]
            continue
        if ch == " ":
            codes.append(CODE_SPACE)
            continue
        if ch in LTRS_TO_CODE and ch not in ("\r", "\n"):
            if figs:
                codes.append(CODE_LTRS)
                figs = False
            codes.append(LTRS_TO_CODE[ch])
        elif ch in FIGS_TO_CODE:
            if not figs:
                codes.append(CODE_FIGS)
                figs = True
            codes.append(FIGS_TO_CODE[ch])
        # else: silently dropped (e.g. Polish diacritics — NAVTEX is ASCII)
    return codes


def codes_to_text(codes: list[int]) -> str:
    """Inverse of text_to_codes for valid codes; invalid codes become '*'."""
    out: list[str] = []
    figs = False
    for c in codes:
        if c == CODE_LTRS:
            figs = False
        elif c == CODE_FIGS:
            figs = True
        elif c in (CODE_ALPHA, CODE_REP):
            continue
        elif not is_valid_code(c):
            out.append("*")
        else:
            table = CODE_TO_FIGS if figs else CODE_TO_LTRS
            ch = table.get(c)
            if ch == "\r":
                continue
            out.append(ch if ch is not None else "*")
    return "".join(out)


def frame(codes: list[int], phasing_pairs: int = 14, tail_pairs: int = 6) -> list[int]:
    """Interleave DX/RX with the 5-slot repeat delay; phasing before, idle after."""
    slots: list[int] = []
    for _ in range(phasing_pairs):
        slots += [CODE_REP, CODE_ALPHA]
    start = len(slots)
    n = len(codes)
    total = start + 2 * n + 5 + 2 * tail_pairs  # room for the last RX and the idle tail
    out = [None] * total
    for i, code in enumerate(codes):
        dx = start + 2 * i
        out[dx] = code
        out[dx + 5] = code
    for i in range(start, total):
        if out[i] is None:
            out[i] = CODE_REP if i % 2 == 0 else CODE_ALPHA
    return slots + out[start:]


def corrupt(
    slots: list[int],
    error_rate: float,
    seed: int = 0,
    mode: str = "burst",
    phasing_pairs: int = 14,
) -> tuple[list[int], list[int]]:
    """Inject decode failures. Returns (slots, indices of message characters killed).

    ``burst``: for each message character, with probability ``error_rate`` corrupt BOTH its
    DX and RX copy (a fade longer than 350 ms) — the decoder must print '*'.
    ``random``: flip bits in individual slots with probability ``error_rate`` each; the FEC
    recovers most of them, so the observed '*' rate is roughly error_rate².
    """
    rng = random.Random(seed)
    slots = list(slots)
    killed: list[int] = []
    start = 2 * phasing_pairs
    n_chars = (len(slots) - start - 5) // 2

    def smash(code: int) -> int:
        # flip two bits so the result cannot be a valid 4-of-7 code fixed by one flip
        bits = rng.sample(range(BITS_PER_CHAR), 2)
        for b in bits:
            code ^= 1 << b
        if is_valid_code(code):
            code ^= 1 << rng.randrange(BITS_PER_CHAR)
        return code

    if mode == "burst":
        for i in range(n_chars):
            if rng.random() < error_rate:
                dx = start + 2 * i
                slots[dx] = smash(slots[dx])
                slots[dx + 5] = smash(slots[dx + 5])
                killed.append(i)
    elif mode == "random":
        for j in range(start, len(slots)):
            if rng.random() < error_rate:
                slots[j] ^= 1 << rng.randrange(BITS_PER_CHAR)
    else:
        raise ValueError(mode)
    return slots, killed


def slots_to_bits(slots: list[int]) -> list[int]:
    return [(code >> b) & 1 for code in slots for b in range(BITS_PER_CHAR)]


@dataclass(frozen=True)
class FskParams:
    sample_rate: int = 8000
    center_hz: float = 1000.0
    shift_hz: float = SHIFT_HZ
    baud: float = BAUD
    amplitude: float = 0.6

    @property
    def mark_hz(self) -> float:
        return self.center_hz + self.shift_hz / 2

    @property
    def space_hz(self) -> float:
        return self.center_hz - self.shift_hz / 2

    @property
    def samples_per_bit(self) -> float:
        return self.sample_rate / self.baud


def modulate(bits: list[int], p: FskParams, lead_s: float = 0.5, tail_s: float = 0.5) -> np.ndarray:
    """Continuous-phase FSK at 100 Bd: 1 → mark tone, 0 → space tone."""
    spb = p.samples_per_bit
    n_bits = len(bits)
    total = int(round(n_bits * spb))
    freqs = np.empty(total, dtype=np.float64)
    for i, bit in enumerate(bits):
        a, b = int(round(i * spb)), int(round((i + 1) * spb))
        freqs[a:b] = p.mark_hz if bit else p.space_hz
    phase = 2 * math.pi * np.cumsum(freqs) / p.sample_rate
    sig = p.amplitude * np.sin(phase)
    lead = np.zeros(int(lead_s * p.sample_rate))
    tail = np.zeros(int(tail_s * p.sample_rate))
    return np.concatenate([lead, sig, tail]).astype(np.float32)


def add_noise(sig: np.ndarray, snr_db: float | None, seed: int = 0) -> np.ndarray:
    if snr_db is None:
        return sig
    rng = np.random.default_rng(seed)
    p_sig = float(np.mean(sig**2)) or 1e-9
    p_noise = p_sig / (10 ** (snr_db / 10))
    noisy = sig + rng.normal(0.0, math.sqrt(p_noise), size=sig.shape)
    peak = float(np.max(np.abs(noisy))) or 1.0
    return (noisy / max(peak, 1.0)).astype(np.float32)


def modulate_iq(
    bits: list[int], p: FskParams, lead_s: float = 0.5, tail_s: float = 0.5
) -> np.ndarray:
    """Complex baseband FSK as a KiwiSDR IQ recording centred on the carrier would show it:
    mark at +shift/2, space at −shift/2 around 0 Hz (``p.center_hz`` is ignored)."""
    spb = p.samples_per_bit
    total = int(round(len(bits) * spb))
    freqs = np.empty(total, dtype=np.float64)
    for i, bit in enumerate(bits):
        a, b = int(round(i * spb)), int(round((i + 1) * spb))
        freqs[a:b] = p.shift_hz / 2 if bit else -p.shift_hz / 2
    phase = 2 * math.pi * np.cumsum(freqs) / p.sample_rate
    sig = p.amplitude * np.exp(1j * phase)
    lead = np.zeros(int(lead_s * p.sample_rate), dtype=np.complex64)
    tail = np.zeros(int(tail_s * p.sample_rate), dtype=np.complex64)
    return np.concatenate([lead, sig.astype(np.complex64), tail])


def write_kiwi_iq_wav(path, rate: int, iq: np.ndarray, block: int = 512, gps_sec: int = 0) -> None:
    """Write a wav in KiwiSDR's IQ layout: 'fmt ' then repeated ('kiwi' GNSS stamp, 'data')
    chunk pairs — the layout kiwirecorder --kiwi-wav produces and plain readers choke on."""
    import struct

    pcm = np.empty(2 * len(iq), dtype="<i2")
    pcm[0::2] = np.clip(np.real(iq) * 32767, -32768, 32767)
    pcm[1::2] = np.clip(np.imag(iq) * 32767, -32768, 32767)
    body = bytearray()
    body += b"WAVE"
    body += b"fmt " + struct.pack("<I", 16) + struct.pack("<HHIIHH", 1, 2, rate, rate * 4, 4, 16)
    for i in range(0, len(iq), block):
        chunk = pcm[2 * i : 2 * (i + block)].tobytes()
        stamp = struct.pack("<BBII", 3, 0, gps_sec + i // rate, int((i % rate) / rate * 1e9))
        body += b"kiwi" + struct.pack("<I", len(stamp)) + stamp
        body += b"data" + struct.pack("<I", len(chunk)) + chunk
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(body)) + bytes(body))


def generate(
    text: str,
    params: FskParams | None = None,
    error_rate: float = 0.0,
    error_mode: str = "burst",
    snr_db: float | None = None,
    seed: int = 0,
    phasing_pairs: int = 14,
    iq: bool = False,
) -> tuple[np.ndarray, dict]:
    """Text → audio samples (float32 mono, or complex64 baseband with ``iq=True``) +
    metadata (killed char indices, expected text)."""
    params = params or FskParams()
    codes = text_to_codes(text)
    slots = frame(codes, phasing_pairs=phasing_pairs)
    killed: list[int] = []
    if error_rate > 0:
        slots, killed = corrupt(slots, error_rate, seed, error_mode, phasing_pairs)
    bits = slots_to_bits(slots)
    if iq:
        audio = modulate_iq(bits, params)
        if snr_db is not None:
            rng = np.random.default_rng(seed)
            p_noise = float(np.mean(np.abs(audio) ** 2)) / (10 ** (snr_db / 10))
            noise = rng.normal(0, math.sqrt(p_noise / 2), (len(audio), 2)).astype(np.float32)
            audio = (audio + noise[:, 0] + 1j * noise[:, 1]).astype(np.complex64)
    else:
        audio = add_noise(modulate(bits, params), snr_db, seed)
    expected = codes_to_text(codes)
    meta = {
        "chars": len(codes),
        "slots": len(slots),
        "duration_s": round(len(audio) / params.sample_rate, 2),
        "killed": killed,
        "expected_star_rate": round(len(killed) / max(1, len(codes)), 4),
        "expected_text": expected,
    }
    return audio, meta
