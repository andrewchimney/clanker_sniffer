import sys
import os
import json
from faster_whisper import WhisperModel

if __name__ == "__main__":
    stem_name = sys.argv[1]
    input_path = f"/shared_data/vocal_stems/{stem_name}"

    print(f"📥 Received: {input_path}", file=sys.stderr)

    if not os.path.exists(input_path):
        print("❌ File not found", file=sys.stderr)
        sys.exit(1)

    # Load model (you can use 'tiny', 'base', 'small', 'medium', 'large')
    model = WhisperModel("base", device="cpu", compute_type="int8")  # or "float32" if needed

    segments, info = model.transcribe(input_path, beam_size=5)

    transcript = " ".join(segment.text.strip() for segment in segments)

    print(f"📝 Transcription: {transcript}", file=sys.stderr)
    print(json.dumps({"lyrics": transcript}))
