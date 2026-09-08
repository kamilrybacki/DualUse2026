# BHMW — indeks ostrzeżeń nawigacyjnych (stan 2026-09-07, wklejony z telefonu)

Źródło: bhmw.gov.pl, lista „Ostrzeżenia nawigacyjne”. Treści są w PDF-ach; do seedów trafia
tekst skopiowany z PDF (`tools/curate_seed.py --source bhmw --lang pl --url <link do PDF>`).
Priorytet: typ „NAVTEX” (208, 213) i „Brzegowe” z pozycjami (211–212, 215–216).

| Numer ON | Data rozpowszechnienia | Rodzaj | Tytuł | Seed |
|---|---|---|---|---|
| 216/2026 | 07.09.2026 11:42 | Brzegowe | WYSTAWIENIE PŁAW | [ ] |
| 215/2026 | 06.09.2026 10:35 | Brzegowe | Holowanie rurociągu | [ ] |
| 213/2026 | 03.09.2026 02:36 | NAVTEX | AKWEN NIEBEZPIECZNY | [ ] |
| 212/2026 | 03.09.2026 01:16 | Brzegowe | AKWEN NIEBEZPIECZNY | [ ] |
| 211/2026 | 03.09.2026 01:06 | Brzegowe | STREFA Nr: 13 ZAMKNIĘTA | [ ] |
| 210/2026 | 03.09.2026 12:51 | Brzegowe | STREFA Nr: 12 ZAMKNIĘTA | [ ] |
| 209/2026 | 03.09.2026 12:36 | Brzegowe | STREFA Nr: 6c ZAMKNIĘTA | [ ] |
| 208/2026 | 03.09.2026 12:21 | NAVTEX | STREFA Nr: 6 ZAMKNIĘTA | [ ] |
| 207/2026 | 03.09.2026 11:39 | Lokalne BHMW | STREFA Nr: 1b ZAMKNIĘTA | [ ] |
| 206/2026 | 03.09.2026 11:31 | Lokalne BHMW | STREFA Nr: 1a ZAMKNIĘTA | [ ] |

Uwaga do fixture'ów: prawdziwe BHMW rozróżnia „NAVTEX” (nadawane po polsku na 490 kHz),
„Brzegowe” i „Lokalne BHMW” — pole `agency` w schemacie zostaje `BHMW`, rodzaj może wejść
do `location_name`/notatki; kandydat na pole w schemacie v0.2.
