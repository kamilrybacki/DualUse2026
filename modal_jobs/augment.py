"""VHF channel augmentation — pure numpy/scipy, unit-testable offline (used by W2 tts.py).

Simulates a narrow-band FM marine radio path: 300–3400 Hz band-pass, additive noise,
clipping, squelch tail bursts, dropouts, resampling to 8 kHz.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

try:
    from scipy.signal import butter, resample_poly, sosfiltfilt
except ImportError:  # pragma: no cover — scipy is in the "audio" extra
    butter = resample_poly = sosfiltfilt = None


@dataclass(frozen=True)
class AugmentParams:
    snr_db: float = 15.0
    clip_level: float = 0.9  # 1.0 = no clipping
    dropout_rate: float = 0.0  # dropouts per second
    dropout_ms: float = 120.0
    squelch_tail: bool = True
    band: tuple[float, float] = (300.0, 3400.0)
    out_rate: int = 8000
    seed: int = 0


def bandpass(x: np.ndarray, rate: int, band: tuple[float, float]) -> np.ndarray:
    if sosfiltfilt is None:
        raise RuntimeError("scipy required: uv sync --extra audio")
    lo, hi = band
    sos = butter(
        4, [lo / (rate / 2), min(hi, rate / 2 - 1) / (rate / 2)], btype="band", output="sos"
    )
    return sosfiltfilt(sos, x).astype(np.float32)


def add_noise(x: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    p = float(np.mean(x**2)) or 1e-9
    n = rng.normal(0.0, math.sqrt(p / 10 ** (snr_db / 10)), size=x.shape)
    # pinkish tint: one-pole low-pass on the noise
    for i in range(1, len(n)):
        n[i] = 0.6 * n[i - 1] + 0.4 * n[i]
    return (x + n).astype(np.float32)


def clip(x: np.ndarray, level: float) -> np.ndarray:
    if level >= 1.0:
        return x
    peak = float(np.max(np.abs(x))) or 1.0
    return np.clip(x / peak, -level, level).astype(np.float32)


def dropouts(
    x: np.ndarray, rate: int, per_second: float, ms: float, rng: np.random.Generator
) -> np.ndarray:
    if per_second <= 0:
        return x
    y = x.copy()
    n = int(per_second * len(x) / rate)
    w = int(ms / 1000 * rate)
    for _ in range(n):
        a = rng.integers(0, max(1, len(x) - w))
        y[a : a + w] = 0.0
    return y


def squelch_tail(
    x: np.ndarray, rate: int, rng: np.random.Generator, ms: float = 60.0
) -> np.ndarray:
    """White-noise burst at the end of the transmission (receiver squelch closing)."""
    w = int(ms / 1000 * rate)
    burst = rng.normal(0.0, 0.3, size=w).astype(np.float32)
    return np.concatenate([x, burst])


def resample(x: np.ndarray, rate: int, out_rate: int) -> np.ndarray:
    if rate == out_rate:
        return x
    if resample_poly is None:
        raise RuntimeError("scipy required: uv sync --extra audio")
    g = math.gcd(rate, out_rate)
    return resample_poly(x, out_rate // g, rate // g).astype(np.float32)


def augment(x: np.ndarray, rate: int, p: AugmentParams) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(p.seed)
    y = x.astype(np.float32)
    y = bandpass(y, rate, p.band)
    y = dropouts(y, rate, p.dropout_rate, p.dropout_ms, rng)
    y = add_noise(y, p.snr_db, rng)
    y = clip(y, p.clip_level)
    if p.squelch_tail:
        y = squelch_tail(y, rate, rng)
    y = resample(y, rate, p.out_rate)
    peak = float(np.max(np.abs(y))) or 1.0
    return (y / peak * 0.9).astype(np.float32), p.out_rate


PRESETS: dict[str, AugmentParams] = {
    "clean": AugmentParams(snr_db=30, clip_level=1.0, dropout_rate=0.0, squelch_tail=False),
    "typical": AugmentParams(snr_db=15, clip_level=0.9, dropout_rate=0.1),
    "harsh": AugmentParams(snr_db=6, clip_level=0.6, dropout_rate=0.5, dropout_ms=200),
}
