"""Cloud recording of 518 kHz NAVTEX slots from KiwiSDR (PRD Annex A.1) when no machine with
open network is at hand. Same slot table and file naming as tools/record_navtex.py; the wav
lands in the volume under ``recordings/518khz/`` and is mirrored with ``modal volume get``.

    modal run modal_jobs/record.py --station HIJ --kiwi host1,host2:8073   # waits for the slot
    modal run modal_jobs/record.py --station U --auto 2                      # picks 2 Kiwis by SNR
    modal run modal_jobs/record.py --station J --kiwi host1 --now            # start immediately
    modal volume get falochron-artifacts recordings/518khz data/recordings/518khz/

The function is spawned detached, so the local ``modal run`` returns at once; watch it in the
Modal dashboard or with ``modal app logs falochron``.
"""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from modal_jobs.common import REPO_ROOT, app, base_image, mirror_hint, vol_path, volume

rec_image = (
    base_image.run_commands(
        "git clone --depth 1 https://github.com/jks-prv/kiwiclient /opt/kiwiclient "
        "&& cd /opt/kiwiclient && git checkout -q 4eb733e6b6147f7fbeb97ced64cdac029b202d18"
    )
    .add_local_file(str(REPO_ROOT / "tools" / "__init__.py"), remote_path="/repo/tools/__init__.py")
    .add_local_file(
        str(REPO_ROOT / "tools" / "record_navtex.py"), remote_path="/repo/tools/record_navtex.py"
    )
    .add_local_file(
        str(REPO_ROOT / "tools" / "fetch_kiwis.py"), remote_path="/repo/tools/fetch_kiwis.py"
    )
)
KIWIRECORDER = Path("/opt/kiwiclient/kiwirecorder.py")


@app.function(image=rec_image, volumes={"/vol": volume}, timeout=5 * 3600, cpu=1)
def record(station: str, kiwis: list[str] | None, auto: int, mode: str, now: bool) -> str:
    sys.path.insert(0, "/repo")
    from tools import fetch_kiwis as fk
    from tools import record_navtex as rn

    stations = rn.parse_station_arg(station)
    if not kiwis:
        page = fk.fetch_public()
        ranked = fk.rank(fk.parse_public_list(page), stations[0].id)[: max(auto * 3, 6)]
        fk.KIWIRECORDER = KIWIRECORDER
        for k in ranked:
            k.snr_db = fk.measure_snr(k, seconds=15)
        ranked.sort(key=lambda k: -(k.snr_db if k.snr_db is not None else -999))
        chosen = ranked[: auto or 2]
        print("auto-picked:", [(k.host, k.snr_db) for k in chosen])
        kiwi_list = [rn.Kiwi(k.host, k.port) for k in chosen]
    else:
        kiwi_list = rn.parse_kiwi_arg(",".join(kiwis))

    window = rn.plan_window(stations, datetime.now(UTC))
    out_dir = Path(vol_path("recordings", "518khz"))
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = rn.build_command(
        window, kiwi_list, mode, out_dir, python=sys.executable, kiwirecorder=KIWIRECORDER
    )
    print(
        f"window {window.first_slot:%Y-%m-%d %H:%M}Z..{window.last_slot:%H:%M}Z "
        f"tlimit {window.tlimit}s"
    )
    print(" ".join(cmd))
    if not now:
        wait = (window.record_start - datetime.now(UTC)).total_seconds()
        if wait > 0:
            print(f"sleeping {int(wait)} s until {window.record_start:%H:%M:%S}Z")
            time.sleep(wait)
    rc = subprocess.call(cmd)
    files = sorted(p.name for p in out_dir.glob(rn.filename(window) + "*"))
    volume.commit()
    log = out_dir / "recordings.log"
    with log.open("a", encoding="utf-8") as f:
        f.write(
            f"{datetime.now(UTC).isoformat(timespec='seconds')} {station} rc={rc} "
            f"kiwis={[k.host for k in kiwi_list]} files={files}\n"
        )
    volume.commit()
    return f"rc={rc} files={files}"


@app.local_entrypoint()
def main(
    station: str = "HIJ",
    kiwi: str = "",
    auto: int = 0,
    mode: str = "iq",
    now: bool = False,
    wait: bool = False,
):
    kiwis = [k for k in kiwi.split(",") if k] or None
    if not kiwis and not auto:
        auto = 2
    call = record.spawn(station, kiwis, auto, mode, now)
    print(f"spawned {call.object_id}; logs: modal app logs falochron")
    if wait:
        print(call.get())
    print("mirror: " + mirror_hint("recordings/518khz", "data/recordings/518khz/"))
