# ASR benchmark `20260907-205336_asr`

- corpus: `data/audio/vhf_synth/local` (12 clips) — synthetic espeak-ng voices, channel presets from modal_jobs/augment.py
- engine: sherpa-onnx Whisper (int8 ONNX), CPU, host vm (Linux-6.18.44-fc-v24-x86_64-with-glibc2.39)
- latency/RTF are for this host only; quality (WER, entity recall) is portable

## Model × preset (mean over clips, both languages)

| model | clean | typical | harsh |
|---|---|---|---|
| tiny | WER 1.22 · entity recall 0.00 · RTF 0.06 | WER 0.99 · entity recall 0.00 · RTF 0.04 | WER 0.99 · entity recall 0.00 · RTF 0.03 |
| small | WER 0.79 · entity recall 0.11 · RTF 0.65 | WER 0.95 · entity recall 0.01 · RTF 0.47 | WER 1.06 · entity recall 0.01 · RTF 0.50 |
| turbo | WER 0.37 · entity recall 0.47 · RTF 0.43 | WER 0.49 · entity recall 0.29 · RTF 0.43 | WER 0.91 · entity recall 0.09 · RTF 0.34 |

## Model × language

| model | en | pl |
|---|---|---|
| tiny | WER 1.13 · entity recall 0.00 · RTF 0.06 | WER 1.00 · entity recall 0.00 · RTF 0.03 |
| small | WER 0.93 · entity recall 0.09 · RTF 0.56 | WER 0.94 · entity recall 0.00 · RTF 0.52 |
| turbo | WER 0.60 · entity recall 0.38 · RTF 0.35 | WER 0.58 · entity recall 0.18 · RTF 0.45 |

## Clips

| model | clip | voice | preset | WER | entity recall | RTF | hypothesis |
|---|---|---|---|---|---|---|---|
| tiny | 06_vhf_pl_voice_report | pl | clean | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 06_vhf_pl_voice_report | pl | typical | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 06_vhf_pl_voice_report | pl | harsh | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 06_vhf_pl_voice_report | pl+f3 | clean | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 06_vhf_pl_voice_report | pl+f3 | typical | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 06_vhf_pl_voice_report | pl+f3 | harsh | 1.00 | 0.00 | 0.03 | [MUZYKA] |
| tiny | 07_vhf_en_voice_report | en-gb | clean | 1.90 | 0.00 | 0.16 | I'm not really doing anything. I'm not really doing anything. I'm not really doing anythin |
| tiny | 07_vhf_en_voice_report | en-gb | typical | 0.99 | 0.00 | 0.05 | I don't know if you're in the other room. |
| tiny | 07_vhf_en_voice_report | en-gb | harsh | 0.99 | 0.00 | 0.04 | I don't know if you're interested in the competition. |
| tiny | 07_vhf_en_voice_report | en-us+m3 | clean | 0.97 | 0.00 | 0.04 | I've been planning on having a better time of doing this for the first time. |
| tiny | 07_vhf_en_voice_report | en-us+m3 | typical | 0.97 | 0.00 | 0.03 | I've been planning on having a better time with the government. |
| tiny | 07_vhf_en_voice_report | en-us+m3 | harsh | 0.99 | 0.00 | 0.03 | I don't have any other information on the information. |
| small | 06_vhf_pl_voice_report | pl | clean | 1.00 | 0.00 | 0.11 | (Zbunie rające) |
| small | 06_vhf_pl_voice_report | pl | typical | 1.00 | 0.00 | 0.11 | [MUZYKA] |
| small | 06_vhf_pl_voice_report | pl | harsh | 1.00 | 0.00 | 0.12 | (muzyka) |
| small | 06_vhf_pl_voice_report | pl+f3 | clean | 0.71 | 0.00 | 0.83 | Dynia raniotu, dynia raniotu, jednostka, małty, małty, kotbiór, dynia raniom, małty, kotbi |
| small | 06_vhf_pl_voice_report | pl+f3 | typical | 0.90 | 0.00 | 0.97 | [Zynia kanią, zynia kanią, tu jednostka, małty, małty, kombiór, tu zynia kanią, małty, kom |
| small | 06_vhf_pl_voice_report | pl+f3 | harsh | 1.02 | 0.00 | 0.98 | [Znając na radion jednostkę, wauty, wauty, kodliu] [Znając na radion wauty, kodliu] [Znają |
| small | 07_vhf_en_voice_report | en-gb | clean | 0.66 | 0.44 | 0.92 | Talin, Rabi-O, Talin, Rabi-O is in motor vessel Nordlin, Nordlin, Kohl, Heim, Lima, Alpha, |
| small | 07_vhf_en_voice_report | en-gb | typical | 0.99 | 0.06 | 0.11 | (Police radio) |
| small | 07_vhf_en_voice_report | en-gb | harsh | 0.99 | 0.06 | 0.09 | (Police radio chatter) |
| small | 07_vhf_en_voice_report | en-us+m3 | clean | 0.80 | 0.00 | 0.75 | Talin Rabid-O, Talin Rabid-O is in motorbass. Oh Nordlin, Nordlin calls. I'm Lima, Alpha,  |
| small | 07_vhf_en_voice_report | en-us+m3 | typical | 0.93 | 0.00 | 0.69 | Palin Rabid-O Palin Rabid-O is in motor-metal Nordlin Nordlin Calls I leave a helper, Obe- |
| small | 07_vhf_en_voice_report | en-us+m3 | harsh | 1.24 | 0.00 | 0.82 | (Pilot reading the instructions) (Pilot reading the instructions) (Pilot reading the instr |
| turbo | 06_vhf_pl_voice_report | pl | clean | 0.40 | 0.18 | 0.42 | Dynia radio, dynia radio, tu jednostka Bałtyk, Bałtyk odbiór, dynia radio, Bałtyk odbiór,  |
| turbo | 06_vhf_pl_voice_report | pl | typical | 0.50 | 0.18 | 0.46 | Dynia radio, dynia radio, tu jednostka Bałtyk, Bałtyk, odbiór, tu dynia radio, Bałtyk, odb |
| turbo | 06_vhf_pl_voice_report | pl | harsh | 0.98 | 0.09 | 0.51 | Wynia radio, radio jednostka, małty, pałty, czosnów Wynia radio, pałty, czosnów Wynia radi |
| turbo | 06_vhf_pl_voice_report | pl+f3 | clean | 0.40 | 0.18 | 0.40 | Gdynia radio, Gdynia radio, tu jednostka Małtyk, Małtyk odbiór, Gdynia radio, Małtyk odbió |
| turbo | 06_vhf_pl_voice_report | pl+f3 | typical | 0.48 | 0.18 | 0.41 | Zdynia radio, dynia radio tu jednostka, Bałtyk, Bałtyk, odbiór tu. Zdynia radio, Bałtyk, o |
| turbo | 06_vhf_pl_voice_report | pl+f3 | harsh | 0.73 | 0.27 | 0.50 | Dynia radio, na radio, jednostka, pałty, pałty, kączór Dynia radio, pałty, kączór Dynia ra |
| turbo | 07_vhf_en_voice_report | en-gb | clean | 0.24 | 0.83 | 0.46 | Tallinn Radio, Tallinn Radio, this is motor vessel, Nordlin, Nordlin call time, Lima, Alph |
| turbo | 07_vhf_en_voice_report | en-gb | typical | 0.49 | 0.22 | 0.44 | Tallinn Radio, Tallinn Radio, Nissen Motor, vessel Nordlin, Nordlin Call Time, Lima, Alpha |
| turbo | 07_vhf_en_voice_report | en-gb | harsh | 1.00 | 0.00 | 0.16 | *Countains* |
| turbo | 07_vhf_en_voice_report | en-us+m3 | clean | 0.44 | 0.67 | 0.42 | Talon radio, Talon radio, this is motor vessel, Nordlin, Nordlin calls, I'm Lima, Alpha, R |
| turbo | 07_vhf_en_voice_report | en-us+m3 | typical | 0.49 | 0.56 | 0.42 | Palin radio, palin radio, this is motor, vessel Nordlin, Nordlin, call time, Lima, Alpha,  |
| turbo | 07_vhf_en_voice_report | en-us+m3 | harsh | 0.91 | 0.00 | 0.17 | *Captainer is partly submerged, danger navigation over* |
