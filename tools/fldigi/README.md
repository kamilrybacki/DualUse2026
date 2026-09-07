# fldigi test rig — SITOR-B / NAVTEX decoding

Technology test only (PRD §10.3): play a wav into fldigi through a virtual audio cable and
capture the decoded text via XML-RPC. **This is not the F3 adapter** — it is a one-shot CLI
that writes a `.txt`, listed as pre-work in the README. The adapter is written at the event.

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
| Wikipedia sample / synthetic generator | whatever the file uses (`gen_sitorb.py` default 1000 Hz) | `1000` |

Kiwi IQ files carry `kiwi` GPS-timestamp chunks between data chunks; `iq_to_audio.py`
understands them, standard wav readers do not.

## 6. Smoke test sample

Wikipedia's `Navtex transmission example.ogg` (CC BY-SA, see the file page) — download it
manually into `tools/fldigi/samples/` (git-ignored) and convert:

```
ffmpeg -i "Navtex transmission example.ogg" -ar 8000 -ac 1 tools/fldigi/samples/navtex_wikipedia.wav
```

Acceptance (CLAUDE.md P0.6): the decoded text is readable NAVTEX (station header, message body).
