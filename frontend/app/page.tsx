// pages.tsx
'use client';

import UploadForm from '@/components/UploadForm';
import ProcessedSongs from '@/components/ProcessedSongs';
import Queue from '@/components/Queue';
import { useState } from 'react';
import { mutate } from 'swr';

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
      {/* <Queue items={queue} />
      {results && (
        <pre className="bg-gray-100 p-4 rounded text-xs overflow-x-auto">
          {JSON.stringify(results, null, 2)}
        </pre>
      )} */}
    </main>
  );
}

