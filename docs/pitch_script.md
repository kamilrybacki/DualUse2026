# FALOCHRON — 3-minute pitch, spoken script (EN)

Hard cap: 3:00 (Terms and Conditions). Target 2:45. ~400 words. Numbers in brackets are
the ones measured so far; replace with event-day numbers from `bench/reports/pareto.md`.

---

**[0:00] Problem** *(slide: Baltic map, jamming radius)*

When a crisis hits the Baltic, the cloud and GNSS are the first things to go. GPS spoofing
from the Kaliningrad area already reaches four hundred and fifty kilometres and the waters
of seven countries.

But the sea keeps broadcasting. NAVTEX on five-one-eight kilohertz, navigational warnings
as text, VHF voice. None of it needs a satellite or an internet connection. And today, a
human reads all of it.

FALOCHRON is a box that listens to those broadcasts and turns them into trustworthy,
geo-referenced events, with no cloud and no GNSS.

**[0:30] Live** *(screen: map + input panel)*

Here is a real NAVTEX signal on five-one-eight, decoded by the box. Cable repair,
Pomeranian Bay, polygon, validity window. The card shows the raw text next to the fields:
every value is traceable to the source, nothing is invented.

Now a Polish coastal warning from the Hydrographic Office, plain text. Same schema, same
card, Polish in, S-124 fields out.

Now a VHF voice report. Speech to text, then extraction. The box says: I heard a vessel
without lights near cable works, position here, but this came through speech, so a human
must confirm. It flags it instead of guessing.

And here the correlator proposes: this report is zero point nine nautical miles from the
cable works, inside its time window, same entity. Candidate. It proposes, it does not
merge.

**[1:30] Pull the cable** *(unplug WAN, wait two seconds)*

That was the internet. Next report. Still processed. Still on the map. The queue counter
went up by one.

**[1:45] Reconnect** *(plug in)*

Reconnected. The queued events sync to the second node, same identifiers, no duplicates.
This is store-and-forward, not a demo trick.

**[2:00] One table** *(slide: benchmark)*

We tested the whole cascade of small models on real and synthetic warnings. [The 0.8B
model passes our threshold at X milliseconds and Y megabytes; the 3B model is needed for
N percent of cases.] The metric we care about most is the unsupported-fact rate, values
that are not in the source, and it is [Z percent]. On the radio side, the decoder ran real
off-air audio at zero character errors. On the speech side, only the largest Whisper
variant is good enough for Polish over a marine channel, and it still runs in real time on
a laptop CPU.

**[2:30] Dual-use close** *(slide: marina by day, crisis node by night)*

On a normal day this is a warnings board for a marina or a harbour master. In a crisis it
is a situational-awareness node that survives jamming and a cut cable. We do not replace
TAK, VTS or emergency management systems. We make their inputs resilient and
interoperable: S-124 fields, GeoJSON and CAP out. Sub-billion models, fully on-premise.
Trained anywhere. Running everywhere. Thank you.

---

## If asked

- *Why not AIS?* AIS is what gets spoofed; broadcast channels are independent of it.
- *Why small models?* Extraction and normalization only; deterministic validators own the
  truth. Grammar-constrained output means the shape is guaranteed; the facts are checked.
- *Spoofed NAVTEX?* It exists: on 8 September Irakleio radio warned about an unauthorized
  station broadcasting NAVTEX messages. That is why every card keeps station, time and raw
  text, and why we never auto-merge.
- *FROM SCRATCH?* Pre-event work was research, data, benchmarks and configs, listed in the
  README with the regulation clause they fall under; the pipeline started Friday 18:00,
  see the `event-start` tag.
- *Legal?* NAVTEX is public safety information; the VHF audio you heard is my own voice.
