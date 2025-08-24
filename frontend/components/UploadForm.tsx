'use client';
import SongModal from './SongModal';
import { useState } from 'react';
import { mutate } from 'swr';
import { useEffect } from 'react';
function cn(...inputs: (string | boolean | null | undefined)[]): string {
  return inputs.filter(Boolean).join(' ');
}


const steps = [
  { key: 'audio', label: '→ 🎧 Audio' },
  { key: 'identify', label: '→ 🧠 Song Info' },
  { key: 'stems', label: '→ 🎛 Stems' },
  { key: 'lyrics', label: '→ 📝 Lyrics' },
  { key: 'classification', label: '→ 🤖 Classification' },
];


export default function UploadForm({ onResult }: { onResult: (data: any) => void }) {

  interface SongResult {
    title: string;
    artist: string;
    fingerprint: string;
    duration: number;
    lyrics: string;
    classification: string;
    accuracy: number;
  }

  const [start, setStart] = useState<'audio' | 'text' | 'search'>('audio');
  const [end, setEnd] = useState('classification');
  const [file, setFile] = useState<File | null>(null);
  const [lyrics, setLyrics] = useState('');
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [songData, setSongData] = useState<SongResult | null>(null);


  const startIndex = start === 'text'
    ? steps.findIndex(s => s.key === 'lyrics')
    : start === 'search'
      ? steps.findIndex(s => s.key === 'identify')
      : 0;

  const validEndSteps = steps
    .filter((_, idx) => idx > startIndex)
    .filter(s => s.key !== 'stems'); // 👈 Remove stems from end options

  useEffect(() => {
    if (!validEndSteps.find(s => s.key === end)) {
      setEnd(validEndSteps[0]?.key || steps[startIndex].key);
    }
  }, [start]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (start === 'audio' && !file) return alert('Missing audio file');
    if (start === 'text' && !lyrics) return alert('Missing lyrics');
    if (start === 'search' && !(title && artist)) return alert('Missing title or artist');
 
    setLoading(true);
    const formData = new FormData();

    if (start === 'audio' && file) formData.append('audio', file);
    if (start === 'text') formData.append('lyrics', lyrics);

    formData.append('title', title);
    formData.append('artist', artist);
    formData.append('input_type', start);
    formData.append('output', end);

    // Build outputs list based on steps between start and end
    const fromIdx = steps.findIndex(s => s.key === (start === 'text' ? 'lyrics' : start === 'search' ? 'identify' : 'audio'));
    const toIdx = steps.findIndex(s => s.key === end);
    const outputs = steps.slice(fromIdx + 1, toIdx + 1).map(s => s.key);
    outputs.forEach(service => formData.append('outputs', service));

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      onResult(data);
      setSongData(data.result);
      setModalOpen(true);
    } catch (err) {
      alert('Upload failed');
    } finally {
      mutate('/api/songs');
      setLoading(false);
    }
  };


  return (
    <>
      <SongModal isOpen={modalOpen} onClose={() => setModalOpen(false)} result={songData} />

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <h2 className="text-xl font-bold">Clanker Sniffer 🎧</h2>

        <div className="flex items-center gap-6 overflow-x-auto">
          <div className="flex gap-4 items-center">
            <label className="font-medium">Select Input:</label>
            <select
              value={start}
              onChange={e => setStart(e.target.value as typeof start)}
              className="border rounded px-2 py-1 bg-black text-white"
            >
              <option value="audio">🎧 Upload Audio</option>
              <option value="search">🧠 Song Info (DB)</option>
              <option value="text">📝 Paste Lyrics</option>
            </select>
          </div>

          <div className="flex gap-4 items-center">
            <label className="font-medium">Select Output:</label>
            <select
              value={end}
              onChange={e => setEnd(e.target.value)}
              className="border rounded px-2 py-1 bg-black text-white"
            >
              {validEndSteps.map(step => (
                <option key={step.key} value={step.key}>{step.label}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto">
          {steps.map((step, index) => {
            if (step.key === 'stems') return null; // 🚫 Don't render the button

            const startIndex = start === 'text'
              ? steps.findIndex(s => s.key === 'lyrics')
              : start === 'search'
                ? steps.findIndex(s => s.key === 'identify')
                : 0;

            const endIndex = steps.findIndex(s => s.key === end);

            return (
              <div
                key={step.key}
                className={cn(
                  'rounded-full border px-4 py-1 whitespace-nowrap flex items-center',
                  index >= startIndex && index <= endIndex
                    ? 'bg-white text-black'
                    : 'bg-transparent text-white border-white',
                  index > 0 && 'relative before:content-[""] before:mr-2 before:text-white'
                )}
              >
                {step.label}
              </div>
            );
          })}
        </div>


        {
          start === 'audio' && (
            <input type="file" accept=".wav,.mp3" onChange={e => setFile(e.target.files?.[0] || null)} required />
          )
        }

        {
          start === 'text' && (
            <textarea
              value={lyrics}
              onChange={e => setLyrics(e.target.value)}
              placeholder="Paste lyrics here..."
              className="min-h-[100px]"
              required
            />
          )
        }

        {
          (start === 'audio' || start === 'text'|| start==='search') && (
            <>
              <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Song Title (optional)"
                className="border p-2 bg-black text-white"
              />
              <input
                value={artist}
                onChange={e => setArtist(e.target.value)}
                placeholder="Artist (optional)"
                className="border p-2 bg-black text-white"
              />
            </>
          )
        }

        <button type="submit" disabled={loading} className="bg-white text-black px-4 py-2 rounded">
          {loading ? 'Analyzing...' : 'Submit 🚀'}
        </button>
      </form >
    </>
  );

}
