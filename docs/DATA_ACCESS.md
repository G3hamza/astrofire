# Data access: what AstroFire needs, what the big NASA downloads are, and how to work on slow Wi-Fi

> **Update (13 Nov):** the app now uses only the PSI combustion repository (all 24 investigations). The paper-transcribed tests
> described below (Saffire IV–VI, LUCI) were removed from the app because NTRS papers are not in the challenge resources.

## TL;DR
- **You don't need to download anything to run AstroFire.** Everything the app uses is already in this repo
  (`data/raw` is about 44 MB: PSI experimental tables + metadata + 307 NTRS paper texts).
- The **255 GB / 152 GB / 33 GB** totals on NASA PSI pages are mostly **videos and ISS photos of the same tests**
  that are already rows in the experimental tables. Downloading them adds **no new test conditions**.
- The real gap (Moon/Mars gravity, 34% O₂, 56.5 kPa) exists because **NASA has not flown those tests**, not because
  we're missing a download. See "Why some conditions were never tested" below.

## What the big PSI totals contain (checked on psi.nasa.gov, Nov 2026)
| Investigation | PSI total | What the app uses | What the rest is |
|---|---|---|---|
| BASS-II (PSI-25) | 255.77 GB | Experimental table: 130 rows (kB) | Per-test folders. Example: test O11 = two MP4 views (115 MB + 156 MB), two ISS photo ZIPs (1.5 GB each), original videos ZIP (381 MB), proof sheet PDF (1.4 MB). About 3.6 GB per test. |
| BASS (PSI-26) | 152.32 GB | Experimental table | Same kind: videos/images per test |
| SAFFIRE-I / II / III (PSI-98/99/100) | 11.41 / 15.77 / 32.79 GB | Experimental tables (2–9 rows each) | Flight video, images, documents |

NASA's own BASS-II description says the oxygen was **"varied below 21% by adding nitrogen"**. So no BASS-II video,
however large, contains a 34% O₂ test.

What the videos *could* add: flame spread rates or flame sizes measured frame by frame for tests we already have.
That is image processing, not new conditions, and it's out of scope for the hackathon.

## Why some conditions were never tested
| Condition | Why there is no PSI space test | Closest real data (now in the app) |
|---|---|---|
| Moon (0.17 g) / Mars (0.38 g) gravity | Nothing in orbit runs at partial gravity. ISS and Cygnus are ~0 g. Partial g only exists briefly: drop towers, aircraft, centrifuges, rotating rocket. | **LUCI** (Blue Origin rotating rocket, ~2.5 min, simulated lunar g, air): SIBAL and PMMA rod both burned. Drop-tower O₂ margins (Olson & Ferkul). |
| 34% O₂ | ISS experiments run at cabin air; raised oxygen is too risky with a crew. | **Saffire V–VI** on the uncrewed Cygnus after leaving the ISS: up to **31.0% O₂**, all flat PMMA / cotton samples burned. |
| 56.5 kPa | PSI tables don't record pressure for ISS/Cygnus (cabin ~101 kPa assumed). | **Saffire VI** at **54.1–55.2 kPa**. |

These tests are in NASA **papers**, not PSI tables. They were transcribed into `data/curated/literature_fire_tests.csv`
(paper ID + table/section for every row), pass through the pipeline like everything else, and are shown in the app as
**supporting evidence**. They never change the verdict, which stays based on PSI tables. The Nomex sample on Saffire VI
"did not ignite" with no reason or conditions given, so it is listed but not used as evidence.

## Working with little or no Wi-Fi
1. **Use what's in the repo.** `git clone` once (about 100 MB with data) or copy the folder by USB. Everything runs offline
   except AI-written answers on Ask NASA, which need the internet and an API key.
2. **Need one more PSI table?** On the investigation page, open **Experimental Table** and download only that CSV,
   or in **Data files and documents** tick only the `Experimental table` folder. That's kilobytes, not gigabytes.
3. **Need a video or a big file?** Don't download it to a laptop. Use **Google Colab** (free): the download runs on
   Google's network, and you only transfer results (a CSV of measurements):
   ```python
   # In a Colab cell: fetch ONE file by its PSI download link (copy it from the PSI page), process it there.
   !wget -O test.mp4 "<paste the PSI file link here>"
   ```
   Or preview videos in the browser (PSI has a **Preview** button) without downloading.
4. **Share data with the team** through the repo (CSV is the source of truth). Never edit `data/raw` or `data/curated`
   by hand without a source: add a new file, run `python -m pipelines.orchestration.run_all`, and let validation check it.

## How to add more paper-reported tests (the main way to grow the evidence)
1. Find a NASA paper with a test table (NTRS). Note the NTRS ID and the table/section.
2. Add rows to `data/curated/literature_fire_tests.csv` (one row per test, same columns, `outcome_basis` = observed only
   if the paper states the outcome; leave conditions empty if the paper doesn't give them).
3. Run the pipeline and `pytest -q`. The new tests appear in Scenario (supporting evidence) and on the Gaps map.
