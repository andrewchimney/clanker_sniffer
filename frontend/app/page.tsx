'use client';

import { useState } from 'react';

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [useDemucs, setUseDemucs] = useState(true);
  const [useWhisper, setUseWhisper] = useState(true);
  const [useClassifier, setUseClassifier] = useState(true);
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<string | null>(null);

  async function sendAudioForAnalysis(
    file: File,
    useDemucs: boolean,
    useWhisper: boolean,
    useClassifier: boolean
  ): Promise<void> {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('useDemucs', String(useDemucs));
    formData.append('useWhisper', String(useWhisper));
    formData.append('useClassifier', String(useClassifier));

    const res = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      throw new Error(`Request failed with status ${res.status}`);
    }

    const data = await res.json();
    setResponse(JSON.stringify(data, null, 2));
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a WAV file first.');
      return;
    }
    setLoading(true);
    setResponse(null);

    try {
      await sendAudioForAnalysis(file, useDemucs, useWhisper, useClassifier);
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: '2rem' }}>
      <h1>Audio Analysis Upload</h1>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <input
          type="file"
          accept=".wav"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />

        <label>
          <input
            type="checkbox"
            checked={useDemucs}
            onChange={(e) => setUseDemucs(e.target.checked)}
          />
          Use Demucs
        </label>

        <label>
          <input
            type="checkbox"
            checked={useWhisper}
            onChange={(e) => setUseWhisper(e.target.checked)}
          />
          Use Whisper
        </label>

        <label>
          <input
            type="checkbox"
            checked={useClassifier}
            onChange={(e) => setUseClassifier(e.target.checked)}
          />
          Use Classifier
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing...' : 'Submit'}
        </button>
      </form>

      {response && (
        <pre style={{ marginTop: '2rem', background: '#f0f0f0', padding: '1rem' }}>
          {response}
        </pre>
      )}
    </main>
  );
}

