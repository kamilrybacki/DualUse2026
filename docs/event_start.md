# Event start procedure (Friday 2026-09-11, 18:00 CEST)

Hackathon window per the Terms and Conditions: **Fri 11 Sep 18:00 → Sun 13 Sep 18:00 CEST**.

## Before 18:00
- `git status` clean on `main`; `make test` green; STATUS.md says what is prepared.
- Read the scoring criteria the organizer publishes that day; note weights in `docs/pitch_skeleton.md`.
- Confirm category FROM SCRATCH on the Team list (D5.3).

## At 18:00
```
export FALOCHRON_EVENT=1                      # lifts the src/ guard (tools/hooks/pre-commit)
git tag -a event-start -m "Hackathon start, FROM SCRATCH: first implementation commit follows" 
git push origin event-start
```
The first commit touching `src/` comes *after* the tag. Commit small and often: the
timestamps are the evidence (PRD Annex B).

## During
- PRD §14.2 windows are relative to 18:00 Friday: 0–6 h = Fri evening, 6–14 h = night/Sat morning, …
- Full QLoRA run (W4) may start in the 6–16 h window: `FALOCHRON_EVENT=1 modal run modal_jobs/finetune.py --full`.
- Anything from the pre-work you *reuse* (schemas, grammar, gazetteer, recordings, benchmark) is fine; anything you *rewrite* into the pipeline (adapter logic, validator, correlator) is new code under `src/`.

## ~44 h (Sunday ~14:00)
```
git tag -a demo-freeze -m "Feature freeze before the final" && git push origin demo-freeze
```
Then only the reset script, backups and pitch rehearsal (docs/demo_checklist.md).
