# Requirements

[日本語](requirements.ja.md)

Status: initial requirements accepted on 2026-08-09

## 1. Purpose

Measure event-sound files bundled with operating systems and major applications under a common,
documented procedure. Publish explainable and reproducible reference data for investigating cases
where local notifications play at the same time as content such as a YouTube live stream.

The primary context is competition between stream audio and local notification audio on the
viewer device. Use by a broadcaster whose notification entered the program mix is secondary.

## 2. Non-goals

- Do not prescribe a stream level or minimum level.
- Do not label measurements safe or dangerous.
- Do not rank applications.
- Do not present source-file measurements as acoustic playback levels.

State that OS, application, player, mixer, and output-device settings change actual level
relationships. Any future interpretation must remain separate from measurement records.

## 3. Content priority context

The contextual priority is:

1. Human speech
2. Primary content such as game audio or karaoke backing tracks
3. Incidental background music whose temporary masking is acceptable

These priorities explain the choice of descriptive metrics such as 200 Hz–8 kHz energy. They do
not produce a score or recommendation.

## 4. Initial scope

- macOS system event sounds
- Apple applications bundled with macOS
- Slack
- Discord
- Microsoft Teams
- Zoom
- LINE

The source registry, event IDs, schemas, and generators must remain extensible.

Only the latest observed version of each source is retained in the working tree. Updates replace
the prior snapshot, old states remain in Git history, and unreferenced measurement assets are
removed from the current dataset.

### 4.1 Included sounds

Include short sounds emitted for background events or user actions: messages, incoming calls,
call-state changes, errors, completion, and UI feedback. Exclude primary media such as music,
video soundtracks, or narrated content.

Initial event IDs are:

- `message`
- `incoming_call`
- `call_state`
- `error`
- `completion`
- `ui_feedback`
- `system_alert`
- `unknown`

Classification is source-occurrence metadata, not a measured property. Uncertain uses remain
`unknown` rather than being guessed or silently excluded.

## 5. Source-audio handling

- Measure the bundled file without normalization, gain change, resampling, or lossy conversion.
- Retain SHA-256, in-bundle relative path, OS/application version, and provenance; never retain the
  source audio in the repository.
- An official distribution may be downloaded into temporary storage for an app not locally
  present. Do not install or run it. Record its URL and SHA-256, then delete packages, extracted
  applications, and source audio after measurement.
- Do not bypass authentication, encryption, access controls, or DRM. Record unavailable sources
  explicitly instead.

## 6. Measurements

- Integrated loudness (LUFS)
- Maximum momentary loudness (400 ms, LUFS)
- Maximum short-term loudness (3 s, LUFS)
- Loudness range (LU)
- True peak (dBTP) and sample peak (dBFS)
- Full-file and active-segment RMS (dBFS)
- A non-overlapping short-window RMS envelope (dBFS, at most 400 points)
- Crest Factor
- Duration, active duration, and leading/trailing silence
- Per-channel levels and channel layout
- Broad-band and third-octave energy
- Spectral centroid, peak frequency, and 200 Hz–8 kHz energy proportion
- Codec, sample rate, bit depth, tools, standards, parameters, and timestamps

Exact parameters are versioned in `config/analysis-profile.json` and explained in the methodology.

## 7. Data and publication

- Store on GitHub and publish a static report with GitHub Pages.
- Use pretty-printed JSON as canonical data, split hash-addressed measurements from current source
  occurrences, validate with JSON Schema, and generate readable CSV/HTML from JSON.
- Use English for canonical repository text, field names, unit identifiers, and classification
  IDs; co-locate Japanese versions of user-facing documentation and the report.
- Update data manually with the local CLI. GitHub Actions validates, checks generation, builds, and
  deploys the report. Scheduled update detection or measurement is not an initial requirement.

## 8. Evidence and reproducibility

Record standards, tool versions, parameters, timestamps, hashes, and source provenance. Document
the formula and purpose of descriptive metrics not defined by a cited standard.

## 9. Licensing

- Code: MIT License.
- Measurement data and documentation: CC BY 4.0.
- Original audio is not included or licensed. Product names, trademarks, and original-sound rights
  remain with their owners.

## 10. Static-site information design

Use the functionality and general information density of these existing services as references,
without copying their visual design:

- <https://ai-compare.semnil.com/ja/>
- <https://koe-zukan.semnil.com/>

Provide a centered, information-dense layout; prominent search and filters; ascending/descending
sorting on every data column; progressive navigation from list to detail; visible counts and
snapshot time; distinct values, units, provenance, and caveats; English/Japanese switching;
responsive and keyboard-accessible operation; useful no-JS links; canonical/alternate/OG
metadata; and JSON/CSV downloads. Do not store or play audio.

Each detail page includes a responsive level-over-time SVG generated from the canonical RMS
envelope. Use a fixed 0 to −80 dBFS display range, identify the active-segment threshold, and state
that values below the visual floor are retained in JSON. Do not imply that the plot is LUFS or a
waveform.

On desktop, constrain long result tables to a viewport-height scroll region. When columns overflow
horizontally, expose persistent, keyboard-accessible left/right controls in addition to the native
scrollbar. Use the labeled card layout only on narrow mobile screens.

On a first visit, choose English or Japanese from the browser's ordered language preferences,
which normally reflect the OS locale. Persist an explicit language-switch selection in browser
local storage and prefer it over automatic detection on later visits. Preserve the current page,
query parameters, and fragment when changing languages.
