import sys
import subprocess
import json
import requests
import os

def run_fpcalc(file_name):
    file_path = f"/shared_data/{file_name}"
    result = subprocess.run(["fpcalc", file_path], capture_output=True, text=True)
    # Only fail if no fingerprint or duration could be parsed
    if "FINGERPRINT=" not in result.stdout or "DURATION=" not in result.stdout:
        print("Error: Failed to generate fingerprint", file=sys.stderr)
        print("stderr:", result.stderr, file=sys.stderr)
        sys.exit(1)

    
    fingerprint = None
    duration = None

    for line in result.stdout.splitlines():
        if line.startswith("FINGERPRINT="):
            fingerprint = line.split("=", 1)[1]
        elif line.startswith("DURATION="):
            duration = int(float(line.split("=", 1)[1]))

    if not fingerprint or not duration:
        print("Failed to extract fingerprint or duration", file=sys.stderr)
        sys.exit(1)

    return fingerprint, duration

def lookup_acoustid(fingerprint, duration, api_key):
    url = "https://api.acoustid.org/v2/lookup"
    payload = {
        "client": api_key,
        "format": "json",
        "fingerprint": fingerprint,
        "duration": duration,
        "meta": "recordings"
    }

    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print("AcoustID API error:", response.text, file=sys.stderr)
        sys.exit(1)

    return response.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python acousti_runner.py <audio_filename.wav>", file=sys.stderr)
        sys.exit(1)

    api_key = os.getenv("ACOUSTID_API_KEY")
    if not api_key:
        print("Missing ACOUSTID_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    file_name = sys.argv[1]
    fingerprint, duration = run_fpcalc(file_name)
    result = lookup_acoustid(fingerprint, duration, api_key)

    output = {
        "fingerprint": fingerprint,
        "duration": duration,
        "matches": []
    }

    for result_entry in result.get("results", []):
        for recording in result_entry.get("recordings", []):
            title = recording.get("title", "Unknown")
            artist = "Unknown"
            if recording.get("artists"):
                artist = recording["artists"][0].get("name", "Unknown")
            output["matches"].append({
                "title": title,
                "artist": artist
            })

    print(json.dumps(output, indent=2))
    if not output["matches"]:
        print("No match found. Raw API response:", file=sys.stderr)
        print(json.dumps(result, indent=2), file=sys.stderr)

