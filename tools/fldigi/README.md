# fldigi test rig — SITOR-B / NAVTEX decoding

Technology test only (PRD §10.3): play a wav into fldigi through a virtual audio cable and
capture the decoded text via XML-RPC. **This is not the F3 adapter** — it is a one-shot CLI
that writes a `.txt`, listed as pre-work in the README. The adapter is written at the event.

## 0. Fast path (proven 2026-09-07 in a bare Ubuntu 24.04 container, no sound card)

```
sudo apt install fldigi pulseaudio pulseaudio-utils xvfb
tools/fldigi/rig_up.sh                      # PulseAudio null sink "cable" + fldigi headless + XML-RPC
uv run python tools/gen_sitorb.py --fixture 01_navtex_en_nav_warning --out /tmp/fx01.wav
uv run python tools/fldigi/decode_test.py /tmp/fx01.wav --player "paplay --device=cable"
```

Result on the synthetic fixture: `chars=135 star_rate=0.000% frames=IA47`, text decoded
verbatim. With `--error-rate 0.1` fldigi prints wrong characters and wrong-shift runs, never
`*` — see `docs/research_fldigi_navtex_errors.md`. `rig_up.sh stop` tears it down.
`tools/fldigi/fldigi_def.minimal.xml` is the whole configuration (PulseAudio backend,
XML-RPC on, RSID off); it also suppresses the first-run wizard that otherwise blocks XML-RPC.

## 1. Install

- Linux: `sudo apt install fldigi alsa-utils` (or `pipewire-audio` for `pw-play`/`pw-loopback`)
- macOS: `brew install --cask fldigi` + [BlackHole 2ch](https://existential.audio/blackhole/)
  as the virtual cable (fldigi capture = BlackHole, player output = BlackHole).

## 2. Virtual audio cable

Linux/ALSA:
```
sudo modprobe snd-aloop            # creates "Loopback" card: playback hw:Loopback,0,0 -> capture hw:Loopback,1,0
```
Linux/PipeWire:
```
pw-loopback -n falochron-cable --capture-props='media.class=Audio/Sink' &
```
Then in fldigi: Configure → Soundcard → Devices → PortAudio, Capture = `Loopback: PCM (hw:Loopback,1,0)`
(or the PipeWire sink monitor). Playback can be anything.

## 3. fldigi settings (once, in the GUI; then saved in the config dir)

```
fldigi --config-dir tools/fldigi/config --xmlrpc-server-port 7362 -i
```

- Op Mode → NAVTEX/SitorB → **NAVTEX**
- Configure → Modems → NAVTEX/SitorB: AFC on, filter bandwidth 500 Hz
- Configure → Misc → XML-RPC: enable server, address 127.0.0.1, port 7362
- Configure → Rx/Tx → Rx text: uncheck "clear on new mode", so text persists between polls
- Set the carrier by clicking the waterfall on the FSK pair (or leave it: `decode_test.py --carrier`
  sets it over XML-RPC).

`config/` is git-ignored except `config/NOTES.md` — fldigi writes machine-specific paths
into its XML files and they are not worth committing.

Headless (no display) works with `xvfb-run -a fldigi --config-dir ... --xmlrpc-server-port 7362`.

## 4. Decode a file

```
make decode FILE=samples/navtex_wikipedia.wav
# or
uv run python tools/fldigi/decode_test.py samples/navtex_wikipedia.wav --carrier 1000
```

What it does: connects to fldigi, selects NAVTEX, sets carrier + AFC, clears the RX text,
plays the file with `aplay -D hw:Loopback,0,0` (override with `--player`), polls
`text.get_rx` until playback ends, writes `<file>.decoded.txt` next to the wav (or `--out`)
and prints length, `*` rate and whether `ZCZC … NNNN` frames were seen.

## 5. Audio frequency plan

| Recording | Centre of FSK pair in the audio | `--carrier` |
|---|---|---|
| Kiwi USB at 516.8 kHz (Annex A) | 518.0 − 516.8 = 1.2 kHz | `1200` |
| Kiwi IQ at 518.0 kHz → `iq_to_audio.py` (default `--audio-center 1000`) | 1.0 kHz | `1000` |
| synthetic generator | `gen_sitorb.py` default 1000 Hz | `1000` |
| Wikipedia sample (`Navtex transmission example.ogg`) | tones at ~1615/1785 Hz, **inverted polarity** | `1700 --reverse` |
| WebSDR 518 kHz recording (pd0wm/navtex, 2018) | 915/1085 Hz | `1000` |

Kiwi IQ files carry `kiwi` GPS-timestamp chunks between data chunks; `iq_to_audio.py`
understands them, standard wav readers do not. Without a real recording the whole path can
be rehearsed with a synthetic one: `gen_sitorb.py --fixture 08_navtex_en_gale_warning --iq`
→ `iq_to_audio.py` → `decode_test.py` (verified 2026-09-07: full frame decoded by fldigi).

## 6. Smoke test sample

Wikipedia's `Navtex transmission example.ogg` (CC BY-SA, see the file page) — download it
manually into `tools/fldigi/samples/` (git-ignored) and convert:

```
ffmpeg -i "Navtex transmission example.ogg" -ar 8000 -ac 1 tools/fldigi/samples/navtex_wikipedia.wav
```

Acceptance (CLAUDE.md P0.6): the decoded text is readable NAVTEX (station header, message body).

**Done 2026-09-08 in the container** (`docs/evidence/`): the Wikipedia sample decodes to
"WIKIPEDIA, THE FREE ENCYCLOPEDIA THAT ANYONE CAN EDIT." with `--carrier 1700 --reverse`
(a copy ships in github.com/pd0wm/navtex `audio/navtex_wiki.wav`), and the 8.5-minute
off-air WebSDR recording from the same repo decodes all 9 Netherlands Coastguard messages
with **0.0 % character error rate** against the reference transcripts (`--carrier 1000`).
