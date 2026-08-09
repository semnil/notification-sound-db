# Measurement methodology

[日本語](methodology.ja.md)

## Scope and signal path

Each record describes the first audio stream in an original file bundled with an operating system
or application. FFmpeg decodes it to interleaved 64-bit floating-point PCM at the original sample
rate and channel count. The analyzer does not normalize, change gain, resample, or create a lossy
intermediate. The decoded stream is analysis material only and is never saved.

The exact machine-readable parameters are in
[`config/analysis-profile.json`](../config/analysis-profile.json). Records name that profile so a
future incompatible method can coexist under a new profile ID.

## Loudness and true peak

FFmpeg's `ebur128` filter measures loudness using **ITU-R BS.1770-5 / EBU Mode** with true-peak
measurement enabled. The database records:

- integrated loudness in LUFS;
- the maximum 400 ms momentary loudness in LUFS;
- the maximum 3 s short-term loudness in LUFS when the source is at least 3 s;
- loudness range in LU when the source is at least 3 s; and
- true peak in dBTP.

A 3.1 s silent tail is added inside the measurement filter so the meter emits settled frames after
a short event. The original samples and stored duration are not changed. The tail contains digital
silence and cannot raise a maximum or peak. Records carry a note when the original is shorter than
the 400 ms or 3 s window. Short-term loudness and LRA are stored as JSON `null` below 3 s rather
than being presented as zero.

The standards referenced by this profile are [ITU-R BS.1770-5](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I/en)
and [EBU Tech 3341](https://tech.ebu.ch/docs/tech/tech3341.pdf).

## Sample peak, RMS, and crest factor

Let `x[n,c]` be a decoded floating-point sample for frame `n` and channel `c`, where digital full
scale is 1. Full-file RMS combines every sample and channel:

```text
RMS = sqrt(sum(x[n,c]^2) / (frame_count * channel_count))
RMS_dBFS = 20 * log10(RMS)
```

Sample peak is the greatest absolute decoded sample across all channels. The sample crest factor is
`sample_peak_dBFS - RMS_dBFS`; the true-peak crest factor substitutes true peak for sample peak.
Per-channel RMS and sample peak use the same equations without channel combination.

## Active segment

Activity is detected with non-overlapping 10 ms frames. Frame RMS combines all channels. The
threshold is:

```text
max(-60 dBFS, maximum_frame_RMS_dBFS - 40 dB)
```

The active segment extends from the start of the first frame at or above the threshold to the end
of the last such frame. Active RMS, start/end, duration, and leading/trailing silence are stored.
This detector is a project-defined descriptive operation, not a loudness-gating standard.

## RMS level envelope

The level-over-time plot uses non-overlapping frames and combines every sample and channel with the
same RMS equation as the full-file value. Frames are at least 10 ms. For a longer source, the frame
size grows to keep the series at or below 400 points. Each point is placed at the center of its
frame; the final frame uses only the remaining source samples and is not padded with silence.

Canonical JSON stores each point's time in seconds and RMS in dBFS. Digital silence remains `null`.
The site plots a fixed range from 0 to −80 dBFS to make detail pages visually comparable. Values
below −80 dBFS are pinned to the lower edge only while drawing the chart and are not truncated in
the data. This is an RMS envelope, not a waveform, LUFS time series, or reconstruction of the
original audio.

## Spectral characteristics

Channels are reduced by arithmetic mean for descriptive spectral analysis. A Welch power spectral
density estimate uses a Hann window, a segment of at most 4096 samples, 50% overlap, no detrending,
and the original sample rate. Values are limited to 20 Hz through the lower of 20 kHz or Nyquist.

The database records broad-band and nominal third-octave-band energy in dBFS, spectral centroid,
the frequency of maximum PSD, and the proportion of analyzed energy from 200 Hz to 8 kHz. The last
value is only a broad frequency-overlap descriptor selected because human speech is the primary
content context. It is not a speech-intelligibility, audibility, or masking score. Arithmetic
channel averaging can cancel opposite-polarity content; per-channel time-domain levels remain
available for that reason.

## Provenance, deduplication, and unavailable values

SHA-256 identifies the exact source file. One `data/assets/<sha256>.json` record is shared when the
same bytes occur at multiple current paths. Source records retain relative paths, classifications,
versions, observation time, official URL, acquisition method, and distribution hash where a
package was temporarily downloaded. Analysis failures are retained in the source record without a
fabricated measurement.

JSON `null` always means unavailable or undefined; it never means zero. Source files, packages, and
extracted applications are not published.

## Interpretation boundary

These are digital source-file measurements, not measurements at an application's mixer output,
stream encoder, headphone, speaker, or listener position. OS volume, per-app gain, attenuation,
mixing, dynamics processing, playback device, and environment can change the actual relationship.
The project therefore does not derive a recommended stream level, minimum, safety judgment, or
product ranking from these data.
