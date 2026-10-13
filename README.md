# Kindred — Agentic Dating Lab

A responsive, dark-and-gold matchmaking demo built from the task brief. It includes 25 clearly fictional adult personas, inspectable profile readouts, a transparent compatibility ranking engine, and scripted agent-to-agent first-date simulations.

> **Consent and data boundaries:** the 25 seeded records are synthetic. The site does not scrape LinkedIn or Instagram, infer sensitive traits, contact people, send messages, or schedule dates. Real-profile intake is only for an adult who explicitly consented; the app asks for an approved summary and stores two supplied public profile URLs as references. Scoring only uses the profile fields explicitly entered into the app.

## Features

- 25 fictional demo profiles with interests, self-stated values, connection goals, conversation styles, and age preferences.
- Search and filtering across names, cities, interests, values and goals.
- Profile pages with a plain-language readout and source-reference section.
- Explainable compatibility score from 0–100 using shared interests (32 points), shared values (28), connection goals (15), mutual age-range fit (15), and stated conversation-style fit (10).
- Per-person top-three rankings for the full line-up, including reasons and visual score bars.
- Agent date lab with four dialogue turns, common-ground flags and a next question to discuss in real life. This is a role-play simulation, not a claim that a real person said these words.
- Consent-gated form for adding an adult profile to local SQLite storage. URLs are validated but never fetched.
- Standard-library Python server, automated tests and Dockerfile; no third-party Python dependencies.

## Run locally

Requirements: Python 3.11 or newer.

```bash
python server.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The app creates `app_data.sqlite3` in the project folder when started. Set `PORT` or `APP_DB` to override the defaults.

For an evaluator-friendly, pre-run demo, open `http://127.0.0.1:8000/?demo=1`. It automatically runs the rankings and a sample simulated agent date, so the reviewer does not need to type anything. After deployment, use the same suffix on the public URL: `https://YOUR-SERVICE.onrender.com/?demo=1`.

## Run tests

```bash
python -m unittest discover -s tests -v
```

Tests cover the 25-person demo dataset, score bounds and symmetry, ranking order, simulation boundaries, adult-only profile intake, consent requirements, and URL host validation.

## Run with Docker

```bash
docker build -t kindred-agentic-dating .
docker run --rm -p 8000:8000 -v kindred-data:/data -e APP_DB=/data/app_data.sqlite3 kindred-agentic-dating
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deploy

The container listens on `0.0.0.0:$PORT` and is suitable for a Python-capable host such as Render, Railway, Fly.io or a VPS. Configure a persistent path for `APP_DB` if consented profiles should survive restarts. No API keys are needed. A deployment account is required to publish a public live URL.

## API

- `GET /api/health` — health check
- `GET /api/profiles` — demo and consented profiles
- `GET /api/rankings?profile_id=demo-01` — a person's complete ranking list
- `GET /api/rankings` — top-five results for every profile
- `POST /api/simulate` — rank all profiles and return sample date simulations
- `POST /api/date` — JSON body `{"a_id":"demo-01","b_id":"demo-02"}`
- `POST /api/profiles` — create a consented profile; see `server.py` for required fields and validation

## Submission copy

**Overall explanation (under 200 characters):**

> Consent-first dating lab: inspect 25 fictional profiles, simulate agent dates, and compare explainable match rankings. Add consenting adults with approved summaries and public profile links.

**Technical section (under 500 characters):**

> Python 3.11 standard-library HTTP server and SQLite, with responsive HTML/CSS and vanilla JavaScript. A transparent compatibility heuristic scores self-declared interests, values, goals, age preferences and conversation style. Public LinkedIn/Instagram URLs are validated and stored as references only; the app makes no scraping requests. Includes 25 synthetic adult personas, profile analysis, agent dialogue simulation, ranking UI and automated tests.

## Three-minute demo video run-of-show

Keep the video under three minutes. Record a real browser walkthrough after starting the app; show the complete flow rather than only slides.

- **0:00–0:15 — Intro:** “This is Kindred, a consent-first agentic dating lab. Each profile has an agent that considers stated interests, values and preferences.”
- **0:15–0:45 — Profile pages:** Open the People section, search/filter profiles, and click at least two profiles. Show their profile readouts, interests, stated values, goals and source policy. Explain that the built-in people are fictional demo records.
- **0:45–1:15 — Agent date:** Select two profiles in Date Lab and start the simulation. Keep the four back-and-forth agent messages on screen. Call out the shared interests and follow-up question. Clarify that no real person is contacted.
- **1:15–1:45 — Rankings:** Click “Rank everyone”. Scroll the per-person board and show why the top recommendations vary. Open a profile again to show that its top three rankings are also available on the profile page.
- **1:45–2:15 — Add a consenting adult:** Open the intake form; walk through the two URLs, approved self-written summary, interests, values and consent checkbox. Do not submit another person's information without their explicit permission.
- **2:15–2:40 — Technical overview:** Briefly show the README and `server.py`; explain the weighted score (32 interests, 28 values, 15 goals, 15 age-range fit, 10 conversation style), SQLite persistence, and that the social URLs are references, not scraped.
- **2:40–2:55 — Close:** Run the health check if useful, return to the ranking board and summarize the project's working features.

**Suggested YouTube title:** `Kindred — Agentic Dating Lab | Profile Analysis, Agent Dates & Match Rankings`

## Limitations to state honestly

- This is a deterministic, explainable heuristic and scripted dialogue—not a validated relationship prediction model or a live LLM agent.
- Built-in profiles are fictional; they are not evidence of having processed 25 real people's social media.
- A public GitHub repository, live demo URL and YouTube upload need to be created from the owner's accounts after review and deployment.
