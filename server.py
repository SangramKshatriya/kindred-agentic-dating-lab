#!/usr/bin/env python3
"""Consent-first agentic dating demo. Uses only Python's standard library."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SEED_PATH = ROOT / "data_profiles.json"
DB_PATH = Path(os.environ.get("APP_DB", str(ROOT / "app_data.sqlite3")))
PORT = int(os.environ.get("PORT", "8000"))
MAX_BODY = 64_000

with SEED_PATH.open(encoding="utf-8") as f:
    SEED_PROFILES = json.load(f)


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consented_profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL CHECK(age >= 18),
                city TEXT NOT NULL,
                bio TEXT NOT NULL,
                interests_json TEXT NOT NULL,
                values_json TEXT NOT NULL,
                goal TEXT NOT NULL,
                style TEXT NOT NULL,
                min_age INTEGER NOT NULL,
                max_age INTEGER NOT NULL,
                linkedin_url TEXT NOT NULL,
                instagram_url TEXT NOT NULL,
                consented_at TEXT NOT NULL
            )
        """)


def clean_tags(value, max_items=12):
    if isinstance(value, list):
        raw = value
    else:
        raw = str(value or "").split(",")
    result = []
    for item in raw:
        item = re.sub(r"\s+", " ", str(item)).strip().lower()
        if item and item not in result:
            result.append(item[:40])
        if len(result) >= max_items:
            break
    return result


def read_custom_profiles():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM consented_profiles ORDER BY consented_at DESC").fetchall()
    profiles = []
    for row in rows:
        p = dict(row)
        p["interests"] = json.loads(p.pop("interests_json"))
        p["values"] = json.loads(p.pop("values_json"))
        p["is_demo"] = False
        p["source_mode"] = "consented profile"
        profiles.append(p)
    return profiles


def all_profiles():
    return SEED_PROFILES + read_custom_profiles()


def jaccard(a, b):
    sa, sb = set(a or []), set(b or [])
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def age_compatible(a, b):
    a_ok = int(a["min_age"]) <= int(b["age"]) <= int(a["max_age"])
    b_ok = int(b["min_age"]) <= int(a["age"]) <= int(b["max_age"])
    return a_ok, b_ok


def score_pair(a, b):
    shared_interests = sorted(set(a.get("interests", [])) & set(b.get("interests", [])))
    shared_values = sorted(set(a.get("values", [])) & set(b.get("values", [])))
    interest_points = 32 * jaccard(a.get("interests"), b.get("interests"))
    value_points = 28 * jaccard(a.get("values"), b.get("values"))
    ga, gb = a.get("goal", ""), b.get("goal", "")
    if ga == gb:
        goal_points = 15
    elif ga in {"long-term relationship", "meaningful connection"} and gb in {"long-term relationship", "meaningful connection"}:
        goal_points = 10
    else:
        goal_points = 4
    age_a, age_b = age_compatible(a, b)
    age_points = 15 if age_a and age_b else (8 if age_a or age_b else 0)
    sa, sb = a.get("style", ""), b.get("style", "")
    style_points = 10 if sa == sb else (7 if {sa, sb} <= {"thoughtful", "warm", "curious"} else 5)
    raw_score = interest_points + value_points + goal_points + age_points + style_points
    score = max(0, min(100, round(raw_score)))

    reasons = []
    if shared_interests:
        reasons.append("Shared interests: " + ", ".join(shared_interests[:4]))
    if shared_values:
        reasons.append("Shared values: " + ", ".join(shared_values[:3]))
    if ga == gb:
        reasons.append("Both state the same connection goal")
    elif goal_points >= 10:
        reasons.append("Their stated relationship goals are broadly aligned")
    if age_a and age_b:
        reasons.append("Both ages fit the range each person stated")
    if sa == sb:
        reasons.append("Similar conversation style")
    if not reasons:
        reasons.append("A useful conversation would clarify priorities and expectations")
    return {
        "score": score,
        "shared_interests": shared_interests,
        "shared_values": shared_values,
        "reasons": reasons,
        "breakdown": {
            "interests": round(interest_points),
            "values": round(value_points),
            "goals": round(goal_points),
            "age_preferences": round(age_points),
            "conversation_style": round(style_points),
        },
    }


def rankings_for(profile, profiles):
    items = []
    for other in profiles:
        if other["id"] == profile["id"]:
            continue
        result = score_pair(profile, other)
        items.append({"profile": public_profile(other), **result})
    return sorted(items, key=lambda x: (-x["score"], x["profile"]["name"]))


def public_profile(p):
    # Deliberately do not return consent timestamps or raw database fields.
    return {
        "id": p["id"], "name": p["name"], "age": int(p["age"]), "city": p.get("city", ""),
        "bio": p.get("bio", ""), "interests": p.get("interests", []), "values": p.get("values", []),
        "goal": p.get("goal", "meaningful connection"), "style": p.get("style", "thoughtful"),
        "min_age": int(p.get("min_age", 18)), "max_age": int(p.get("max_age", 99)),
        "linkedin_url": p.get("linkedin_url", ""), "instagram_url": p.get("instagram_url", ""),
        "is_demo": bool(p.get("is_demo", False)), "source_mode": p.get("source_mode", "synthetic demo" if p.get("is_demo") else "consented profile"),
    }


def simulate_date(a, b):
    match = score_pair(a, b)
    overlap = match["shared_interests"]
    opener = overlap[0] if overlap else (a.get("interests") or ["a favourite weekend plan"])[0]
    second_topic = overlap[1] if len(overlap) > 1 else (b.get("interests") or ["travel"])[0]
    common_value = match["shared_values"][0] if match["shared_values"] else "open communication"
    a_name, b_name = a["name"].split()[0], b["name"].split()[0]
    if match["score"] >= 75:
        readout = "Strong conversation potential in this simulation; verify the fit with real, voluntary conversation."
    elif match["score"] >= 55:
        readout = "Some promising overlap, with a few preferences worth discussing openly."
    else:
        readout = "This pairing has fewer obvious overlaps; a thoughtful conversation could still reveal surprises."
    return {
        "a": public_profile(a), "b": public_profile(b), "match": match,
        "readout": readout,
        "dialogue": [
            {"speaker": f"{a_name}'s agent", "text": f"{a_name} enjoys {opener}. What kind of first-date plan around that would feel fun and comfortable for you?"},
            {"speaker": f"{b_name}'s agent", "text": f"{b_name} is interested in {second_topic}, too. A relaxed café or a public walk with an easy exit sounds like a good low-pressure start."},
            {"speaker": f"{a_name}'s agent", "text": f"{a_name} values {common_value}. They would rather ask a clear question than guess what someone wants."},
            {"speaker": f"{b_name}'s agent", "text": f"That suits {b_name}. They would be curious to talk about expectations, favourite routines and what a good connection looks like to each person."},
        ],
        "green_flags": [
            f"Common ground: {', '.join(overlap[:3])}" if overlap else "The agents identified topics to explore despite limited shared interests",
            f"Potentially shared value: {common_value}",
            "Both agents propose a public, low-pressure first meeting",
        ],
        "next_question": "What would each person need to feel respected, safe and understood on a first date?",
        "notice": "This is a fictional, on-site simulation only. It does not contact anyone, book a date, or speak for a real person.",
    }


def validate_url(url, domain):
    from urllib.parse import urlparse
    parsed = urlparse(str(url or "").strip())
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and host in {domain, "www." + domain} and bool(parsed.path and parsed.path != "/")


def validate_profile(body):
    errors = []
    name = re.sub(r"\s+", " ", str(body.get("name", "")).strip())
    age_raw = body.get("age", "")
    try:
        age = int(age_raw)
    except (TypeError, ValueError):
        age = 0
    city = re.sub(r"\s+", " ", str(body.get("city", "")).strip())
    bio = re.sub(r"\s+", " ", str(body.get("bio", "")).strip())
    interests = clean_tags(body.get("interests", []))
    values = clean_tags(body.get("values", []))
    goal = str(body.get("goal", "")).strip()
    style = str(body.get("style", "")).strip()
    try:
        min_age, max_age = int(body.get("min_age", 18)), int(body.get("max_age", 99))
    except (TypeError, ValueError):
        min_age, max_age = 0, 0
    linkedin_url, instagram_url = str(body.get("linkedin_url", "")).strip(), str(body.get("instagram_url", "")).strip()
    if len(name) < 2 or len(name) > 80: errors.append("Enter a name between 2 and 80 characters.")
    if not 18 <= age <= 100: errors.append("Only adults aged 18–100 can be added.")
    if not city or len(city) > 80: errors.append("Enter a city or broad location.")
    if len(bio) < 20 or len(bio) > 600: errors.append("Add a self-written summary of 20–600 characters.")
    if len(interests) < 2: errors.append("Add at least two interests.")
    if not values: errors.append("Add at least one self-stated value.")
    allowed_goals = {"long-term relationship", "meaningful connection", "friendship first", "casual dating"}
    allowed_styles = {"thoughtful", "curious", "playful", "expressive", "warm", "direct"}
    if goal not in allowed_goals: errors.append("Choose a valid connection goal.")
    if style not in allowed_styles: errors.append("Choose a conversation style.")
    if not (18 <= min_age <= max_age <= 100): errors.append("Check the preferred age range.")
    if not validate_url(linkedin_url, "linkedin.com"): errors.append("Enter a valid public LinkedIn profile URL (https://www.linkedin.com/in/...).")
    if not validate_url(instagram_url, "instagram.com"): errors.append("Enter a valid public Instagram profile URL (https://www.instagram.com/...).")
    if body.get("consent") is not True: errors.append("Confirm that the adult has explicitly agreed to this profile being used in the demo.")
    if errors:
        return None, errors
    return {
        "id": "person-" + uuid.uuid4().hex[:10], "name": name, "age": age, "city": city,
        "bio": bio, "interests": interests, "values": values, "goal": goal, "style": style,
        "min_age": min_age, "max_age": max_age, "linkedin_url": linkedin_url,
        "instagram_url": instagram_url, "consented_at": datetime.now(timezone.utc).isoformat(),
        "is_demo": False, "source_mode": "consented profile",
    }, []


class Handler(BaseHTTPRequestHandler):
    server_version = "KindredDemo/1.0"

    def log_message(self, fmt, *args):
        if os.environ.get("APP_LOG", "0") == "1":
            super().log_message(fmt, *args)

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > MAX_BODY:
            raise ValueError("Request body is too large.")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            return self.send_json({"ok": True, "service": "kindred-agent-demo", "mode": "consent-first; no external scraping"})
        if parsed.path == "/api/profiles":
            profiles = [public_profile(p) for p in all_profiles()]
            return self.send_json({"profiles": profiles, "demo_count": sum(1 for p in profiles if p["is_demo"]), "consented_count": sum(1 for p in profiles if not p["is_demo"])})
        if parsed.path == "/api/rankings":
            q = parse_qs(parsed.query)
            pid = q.get("profile_id", [""])[0]
            profiles = all_profiles()
            by_id = {p["id"]: p for p in profiles}
            if pid:
                if pid not in by_id: return self.send_json({"error": "Profile not found."}, 404)
                return self.send_json({"profile": public_profile(by_id[pid]), "rankings": rankings_for(by_id[pid], profiles)})
            all_rankings = {}
            for p in profiles:
                all_rankings[p["id"]] = [{"profile": item["profile"], "score": item["score"], "reasons": item["reasons"]} for item in rankings_for(p, profiles)[:5]]
            return self.send_json({"rankings": all_rankings, "profile_count": len(profiles)})
        if parsed.path == "/" or parsed.path == "/index.html":
            return self.serve_static("index.html")
        if parsed.path.startswith("/static/"):
            relative = parsed.path[len("/static/"):]
            if ".." in relative or relative.startswith("/"):
                return self.send_json({"error": "Not found."}, 404)
            return self.serve_static(relative)
        if parsed.path == "/favicon.ico":
            self.send_response(204); self.end_headers(); return
        return self.send_json({"error": "Not found."}, 404)

    def serve_static(self, relative):
        path = (STATIC / relative).resolve()
        if STATIC.resolve() not in path.parents and path != STATIC.resolve() / "index.html":
            return self.send_json({"error": "Not found."}, 404)
        if not path.is_file():
            return self.send_json({"error": "Not found."}, 404)
        content_types = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml"}
        payload = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_types.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            body = self.read_json()
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return self.send_json({"error": str(exc) or "Invalid JSON."}, 400)
        if parsed.path == "/api/profiles":
            profile, errors = validate_profile(body)
            if errors: return self.send_json({"error": "Please correct the form.", "details": errors}, 400)
            with connect_db() as conn:
                conn.execute("""INSERT INTO consented_profiles
                    (id,name,age,city,bio,interests_json,values_json,goal,style,min_age,max_age,linkedin_url,instagram_url,consented_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                    profile["id"], profile["name"], profile["age"], profile["city"], profile["bio"],
                    json.dumps(profile["interests"]), json.dumps(profile["values"]), profile["goal"], profile["style"],
                    profile["min_age"], profile["max_age"], profile["linkedin_url"], profile["instagram_url"], profile["consented_at"]
                ))
            return self.send_json({"profile": public_profile(profile), "message": "Profile added with consent. No social profile was scraped."}, 201)
        if parsed.path == "/api/date":
            profiles = all_profiles(); by_id = {p["id"]: p for p in profiles}
            a, b = by_id.get(str(body.get("a_id", ""))), by_id.get(str(body.get("b_id", "")))
            if not a or not b: return self.send_json({"error": "Choose two available profiles."}, 400)
            if a["id"] == b["id"]: return self.send_json({"error": "Choose two different profiles."}, 400)
            return self.send_json(simulate_date(a, b))
        if parsed.path == "/api/simulate":
            profiles = all_profiles()
            if len(profiles) < 2: return self.send_json({"error": "At least two profiles are needed."}, 400)
            ranking_map = {}
            for p in profiles:
                ranking_map[p["id"]] = [{"profile": item["profile"], "score": item["score"], "reasons": item["reasons"]} for item in rankings_for(p, profiles)[:3]]
            pairs = []
            seen = set()
            for p in profiles:
                ranked = rankings_for(p, profiles)
                if not ranked: continue
                other_id = ranked[0]["profile"]["id"]
                key = tuple(sorted([p["id"], other_id]))
                if key in seen: continue
                seen.add(key)
                other = next(x for x in profiles if x["id"] == other_id)
                pairs.append({"a": public_profile(p), "b": public_profile(other), "match": score_pair(p, other)})
            pairs.sort(key=lambda x: -x["match"]["score"])
            demo_pairs = pairs[:5]
            dates = [simulate_date(next(p for p in profiles if p["id"] == pair["a"]["id"]), next(p for p in profiles if p["id"] == pair["b"]["id"])) for pair in demo_pairs[:3]]
            return self.send_json({"profile_count": len(profiles), "possible_pairs": len(profiles) * (len(profiles) - 1) // 2, "rankings": ranking_map, "top_pairs": demo_pairs, "sample_dates": dates})
        return self.send_json({"error": "Not found."}, 404)


def main():
    init_db()
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Kindred demo running at http://127.0.0.1:{PORT}")
    print("Consent-first mode: synthetic fixtures; user-provided profile links are references only, never scraped.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
