# Intervals.icu Integration for Home Assistant

A custom Home Assistant integration for [Intervals.icu](https://intervals.icu), a training analytics platform for endurance athletes.

## Installation

### HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Intervals.icu" and install
3. Restart Home Assistant

### Manual

1. Copy the `custom_components/intervals_icu` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Intervals.icu"
3. Enter your **Athlete ID** and **API Key**
   - Find these in your Intervals.icu account under **Settings** > **Developer Settings**

## Sensors

### Wellness (daily)

| Sensor | Description |
|--------|-------------|
| Weight | Body weight (kg) |
| Resting heart rate | Resting HR (bpm) |
| HRV | Heart rate variability (ms) |
| HRV SDNN | HRV SDNN (ms) |
| Sleep time | Total sleep duration |
| Sleep score | Sleep quality score |
| Readiness | Readiness score |
| SpO2 | Blood oxygen saturation (%) |
| Steps | Daily step count |
| Fitness (CTL) | Chronic Training Load |
| Fatigue (ATL) | Acute Training Load |
| Form (TSB) | Training Stress Balance (CTL - ATL) |
| Ramp rate | Training ramp rate |
| Stress | Subjective stress level |
| Mood | Subjective mood |
| Motivation | Subjective motivation |
| Fatigue (subjective) | Subjective fatigue |
| Soreness | Subjective soreness |
| Basal calories | Basal metabolic calories |
| Active calories | Calories from activity |
| Total calories | Total daily calories |

### Latest Activity

| Sensor | Description |
|--------|-------------|
| Last activity | Activity name |
| Last activity type | Activity type (Ride, Run, etc.) |
| Last activity duration | Moving time |
| Last activity distance | Distance (m) |
| Last activity training load | Training load score |
| Last activity avg HR | Average heart rate (bpm) |
| Last activity max HR | Max heart rate (bpm) |
| Last activity avg power | Average power (W) |
| Last activity normalized power | Normalized power (W) |
| Last activity intensity | Intensity factor |
| Last activity calories | Calories burned |
| Last activity elevation gain | Total elevation gain (m) |

### Planned Workouts

| Sensor | Description |
|--------|-------------|
| Next workout | Name of next planned workout |
| Next workout date | Date of next planned workout |
| Next workout type | Type of next planned workout |

### Athlete Profile

| Sensor | Description |
|--------|-------------|
| FTP | Functional Threshold Power (W) |
| LTHR | Lactate Threshold Heart Rate (bpm) |
| Max heart rate | Max heart rate (bpm) |
| Resting heart rate (profile) | Resting HR from profile (bpm) |

### Calendar

A calendar entity shows planned workouts, targets, notes, and races from your Intervals.icu calendar. Events appear in the Home Assistant calendar card and can be used in automations.

## Data Update

Data is polled from the Intervals.icu API every 2 hours. The calendar fetches events on demand when browsing date ranges.

## Weekly training history (Fantail extension)

The **Weekly training** sensor reports this week's total hours. Its attributes
contain `current_week` and `history` (12 weeks including the current partial
week), with `strength`, `swimming`, `cycling`, `running`, and `other` buckets.
Each bucket exposes hours, seconds, distance in metres/km, session count,
indoor seconds, virtual distance, and missing-measurement counts. Strength
distance is not meaningful; dashboards should show a dash.

Weeks run Monday–Sunday. Recorded activity local dates take precedence; UTC
dates fall back to the configured HA timezone. Strength/swim use elapsed time
(including rests); run/bike use moving time, falling back to the other duration
only when missing. Missing values are counted, never invented. All sport types
not explicitly mapped are retained under `other`.

Every two-hour refresh replaces the entire window, so corrections and deletions
are reflected without double counting. Identical activity IDs count once; separate
Garmin/Strava uploads with different IDs must be reconciled in Intervals itself.
API failures or the 1000-row safety limit mark sensors unavailable rather than
showing misleading zero totals. Historical chart data lives in attributes; this
is not a backfill of HA recorder statistics.

Use `homeassistant.update_entity` on the Weekly training sensor for a manual
refresh. Add a second integration entry with Laura's own athlete ID and authorised
API key to keep athletes separate. Existing entity IDs and credentials are retained
when replacing the upstream HACS package with this fork (same `intervals_icu` domain).
Install only one repository for this domain. Restart HA after upgrading Python code.
