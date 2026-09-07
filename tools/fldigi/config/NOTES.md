# fldigi config dir

Point fldigi here with `--config-dir tools/fldigi/config`. Everything fldigi writes into this
directory (`fldigi_def.xml`, `fldigi.prefs`, logs, macros) is git-ignored: it contains
machine-specific audio device names and absolute paths.

Settings to make once in the GUI (see ../README.md §3):

- Op Mode: NAVTEX
- Modems → NAVTEX/SitorB: AFC on, filter bandwidth 500 Hz
- Soundcard → Devices: PortAudio, Capture = virtual cable capture side
- Misc → XML-RPC: enabled, 127.0.0.1:7362
- Rx/Tx: do not clear RX text on mode change
