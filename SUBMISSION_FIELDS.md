# Submission fields

## Overall explanation (190/200 characters)

Consent-first dating lab: inspect 25 fictional profiles, simulate agent dates, and compare explainable match rankings. Add consenting adults with approved summaries and public profile links.

## Technical section (453/500 characters)

Python 3.11 standard-library HTTP server and SQLite, with responsive HTML/CSS and vanilla JavaScript. A transparent compatibility heuristic scores self-declared interests, values, goals, age preferences and conversation style. Public LinkedIn/Instagram URLs are validated and stored as references only; the app makes no scraping requests. Includes 25 synthetic adult personas, profile analysis, agent dialogue simulation, ranking UI and automated tests.

## URLs that must be added after publishing

- **YouTube link:** Upload `kindred-prototype-walkthrough.mp4` to your YouTube account and paste its URL. The supplied video is a narrated prototype walkthrough using fictional demo data, not a live browser capture.
- **Live website:** Deploy this project to a Python/Docker host and paste its public URL, such as `https://YOUR-SERVICE.onrender.com/`.
- **Demo link:** Use the same URL with `?demo=1`, such as `https://YOUR-SERVICE.onrender.com/?demo=1`. It automatically runs the rankings and a sample agent date, so the reviewer can inspect results without entering anything. Do not submit `localhost` as a public URL.
- **GitHub URL:** Push the folder to a new **public** GitHub repository. Example repository name: `kindred-agentic-dating-lab`.

## Push to a new GitHub repository

From this project folder, after creating an empty public repository on GitHub:

```bash
git init
git add .
git commit -m "Build Kindred agentic dating lab"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/kindred-agentic-dating-lab.git
git push -u origin main
```

Then deploy from that repository using the included `Dockerfile` or `render.yaml`. A GitHub account and hosting account are needed to create the external URLs; none have been fabricated here.

## Important requirement gap

The built-in 25 people are explicitly fictional. They do not satisfy a requirement for 25 real participants. To demonstrate real adults, recruit 25 consenting participants, obtain their approval for the profile summaries and public URLs, and record the working app with their permission. Do not silently represent synthetic personas as real people or scrape their social accounts without consent.



/*
git init
git add .
git commit -m "Build Kindred agentic dating lab"
git branch -M main
git remote add origin https://github.com/SangramKshatriya/kindred-agentic-dating-lab.git
git push -u origin main
*/