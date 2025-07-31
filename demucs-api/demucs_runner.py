import sys
import shutil
import os
from pathlib import Path
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile
import torchaudio
import soundfile as sf


def separate_vocals(input_path, output_dir, file_name):
    model = get_model(name="htdemucs")

    # Read stereo waveform, shape: [2, time]
    ref = AudioFile(input_path).read(streams=0, samplerate=model.samplerate)
    ref = ref.unsqueeze(0)  # Add batch dim: [1, 2, time]

    sources = apply_model(model, ref, split=True, overlap=0.25)[0]

    for idx, name in enumerate(model.sources):
        if name == "vocals":
            out_path = Path(output_dir) / file_name
            stem = sources[idx]
            if stem.ndim == 3:
                stem = stem.squeeze(0)
            # Convert from torch.Tensor to numpy and transpose to (time, channels)
            sf.write(out_path.as_posix(), stem.T.cpu().numpy(), model.samplerate)


            print(f"✅ Saved {name} to {out_path}", file=sys.stderr)

if __name__ == "__main__":
    file_name = sys.argv[1]
    print(file_name , file=sys.stderr)
    
    input_path = f"/shared_data/{file_name}"
    output_dir = f"/shared_data/vocal_stems/"
    #input_path = Path(file_name)
    #output_dir = Path("vocal_stems")  # ✅ creates ./vocal_stems

    print(f"📥 Received: {input_path}",file=sys.stderr)
    print(f"📤 Output will be: {output_dir}", file=sys.stderr)
    
    os.makedirs(output_dir, exist_ok=True)
    #torchaudio.set_audio_backend("ffmpeg")


    try:
        separate_vocals(input_path, output_dir, file_name)
        os.remove(input_path)
        print("✅ Done (simulated Demucs)", file=sys.stderr)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Failed: {e}", file=sys.stderr)
        sys.exit(1)
