// components/UploadForm.tsx
'use client';

import { useState } from 'react';
import { mutate } from 'swr';

interface Props {
  onResult: (data: any) => void;
}


export default function UploadForm({ onResult }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [lyrics, setLyrics] = useState('');
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [mode, setMode] = useState('demucs');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((mode !== 'classifier-text' && !file) || (mode === 'classifier-text' && !lyrics)) return alert('Missing input');

    setLoading(true);
    const formData = new FormData();

    if (file) formData.append('audio', file);
    if (lyrics) formData.append('lyrics', lyrics);
    formData.append('title', title);
    formData.append('artist', artist);
    formData.append('mode', mode);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      onResult(data);
    } catch (err) {
      alert('Upload failed');
    } finally {
      mutate('/api/songs', undefined, { revalidate: true });
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <h2 className="text-xl font-bold">Clanker Sniffer 🎧</h2>

      {/* <div className="flex gap-2">
        <button type="button" className={mode.startsWith('demucs') ? 'font-bold' : ''} onClick={() => setMode('demucs')}>🔊 Upload Audio</button>
        <button type="button" className={mode === 'classifier-text' ? 'font-bold' : ''} onClick={() => setMode('classifier-text')}>📝 Paste Lyrics</button>
      </div> */}

      <label><input type="radio" name="mode" value="demucs" checked={mode === 'demucs'} onChange={() => setMode('demucs')} /> Isolate Vocals (Demucs)</label>
      <label><input type="radio" name="mode" value="demucs-whisper" checked={mode === 'demucs-whisper'} onChange={() => setMode('demucs-whisper')} /> Transcribe Vocals (Demucs + Whisper)</label>
      <label><input type="radio" name="mode" value="demucs-whisper-classifier" checked={mode === 'demucs-whisper-classifier'} onChange={() => setMode('demucs-whisper-classifier')} /> Detect AI Lyrics from audio (Demucs + Whisper + Classifier)</label>
      <label><input type="radio" name="mode" value="classifier-text" checked={mode === 'classifier'} onChange={() => setMode('classifier-text')} /> Detect AI Lyrics from text (Classifier)</label>

      {/* <input type="text" value={title} onChange={e => setTitle(e.target.value)} placeholder="Song title" required />
      <input type="text" value={artist} onChange={e => setArtist(e.target.value)} placeholder="Artist (optional)" /> */}

      {mode !== 'classifier-text' && (
        <input type="file" accept=".wav,.mp3" onChange={e => setFile(e.target.files?.[0] || null)} required />
      )}

      {mode === 'classifier-text' && (
        <textarea value={lyrics} onChange={e => setLyrics(e.target.value)} placeholder="Paste lyrics here..." className="min-h-[100px]" required />
      )}

      <button type="submit" disabled={loading}>{loading ? 'Analyzing...' : 'Submit 🚀'}</button>
    </form>
  );
}