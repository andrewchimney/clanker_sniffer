// 'use client';

// import { useState } from 'react';

// export default function HomePage() {
//   const [file, setFile] = useState<File | null>(null);
//   const [name, setName] = useState('');
//   const [artist, setArtist] = useState('');
//   const [useDemucs, setUseDemucs] = useState(true);
//   const [useWhisper, setUseWhisper] = useState(true);
//   const [useClassifier, setUseClassifier] = useState(true);
//   const [loading, setLoading] = useState(false);
//   const [response, setResponse] = useState<string | null>(null);

//   async function sendAudioForAnalysis() {
//     if (!file) return;

//     const formData = new FormData();
//     formData.append('audio', file);
//     formData.append('name', name);
//     formData.append('artist', artist);
//     formData.append('useDemucs', String(useDemucs));
//     formData.append('useWhisper', String(useWhisper));
//     formData.append('useClassifier', String(useClassifier));

//     const res = await fetch('/api/analyze', {
//       method: 'POST',
//       body: formData,
//     });

//     if (!res.ok) {
//       throw new Error(`Request failed with status ${res.status}`);
//     }

//     const data = await res.json();
//     setResponse(JSON.stringify(data, null, 2));
//   }

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!file) {
//       alert('Please select a WAV file.');
//       return;
//     }
//     setLoading(true);
//     setResponse(null);

//     try {
//       await sendAudioForAnalysis();
//     } catch (err) {
//       console.error(err);
//       alert('Upload failed');
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <main style={{ padding: '2rem' }}>
//       <h1>Audio Analysis Upload</h1>

//       <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
//         <input
//           type="text"
//           value={name}
//           onChange={(e) => setName(e.target.value)}
//           placeholder="Song name"
//           required
//         />
//         <input
//           type="text"
//           value={artist}
//           onChange={(e) => setArtist(e.target.value)}
//           placeholder="Artist (optional)"
//           required
//         />
//         <input
//           type="file"
//           accept=".wav,.mp3"
//           onChange={(e) => setFile(e.target.files?.[0] || null)}
//           required
//         />

//         <label>
//           <input
//             type="checkbox"
//             checked={useDemucs}
//             onChange={(e) => setUseDemucs(e.target.checked)}
//           />
//           Use Demucs
//         </label>

//         <label>
//           <input
//             type="checkbox"
//             checked={useWhisper}
//             onChange={(e) => setUseWhisper(e.target.checked)}
//           />
//           Use Whisper
//         </label>

//         <label>
//           <input
//             type="checkbox"
//             checked={useClassifier}
//             onChange={(e) => setUseClassifier(e.target.checked)}
//           />
//           Use Classifier
//         </label>

//         <button type="submit" disabled={loading}>
//           {loading ? 'Analyzing...' : 'Submit'}
//         </button>
//       </form>

//       {response && (
//         <pre style={{ marginTop: '2rem', background: '#f0f0f0', padding: '1rem' }}>
//           {response}
//         </pre>
//       )}
//     </main>
//   );
// }

// pages.tsx
'use client';

import UploadForm from '@/components/UploadForm';
import ProcessedSongs from '@/components/ProcessedSongs';
import Queue from '@/components/Queue';
import { useState } from 'react';

export default function HomePage() {
  const [results, setResults] = useState<any | null>(null);
  const [queue, setQueue] = useState<string[]>([]);

  return (
    <main className="p-8 space-y-8">
      <h1 className="text-2xl font-bold">Audio Analyzer</h1>
      <UploadForm
        onResult={(data) => {
          setResults(data);
          setQueue((q) => [...q, data?.outputs?.whisperOut?.lyrics || 'Unknown']);
        }}
      />
      <ProcessedSongs />
      <Queue items={queue} />
      {results && (
        <pre className="bg-gray-100 p-4 rounded text-xs overflow-x-auto">
          {JSON.stringify(results, null, 2)}
        </pre>
      )}
    </main>
  );
}

