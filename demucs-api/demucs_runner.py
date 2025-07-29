import sys
import shutil
import os
from pathlib import Path

if __name__ == "__main__":
    file_name = sys.argv[1]
    print(file_name)
    
    #file_name = "1753763282545_7:6:25.wav"
    #shared_data/1753763282545_7:6:25.wav
    input_path = f"/shared_data/{file_name}"
    output_dir = f"/shared_data/vocal_stems/"
    output_path = f"{output_dir}"

    print(f"📥 Received: {input_path}",file=sys.stderr)
    print(f"📤 Output will be: {output_path}", file=sys.stderr)
    

    os.makedirs(output_dir, exist_ok=True)

    try:
        print("1", file=sys.stderr)
        shutil.copy(input_path, output_path)  # Fake "vocal stem"
        print("1", file=sys.stderr)
        os.remove(input_path)
        print("✅ Done (simulated Demucs)", file=sys.stderr)
    except Exception as e:
        print(f"❌ Failed: {e}", file=sys.stderr)
        sys.exit(1)
