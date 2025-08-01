'use client';

import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then(res => res.json());

export function useSWRSongs() {
  return useSWR('http://localhost:8005/api/songs', fetcher, { refreshInterval: 5000 });
}

type Song = {
  id: string | number;
  title?: string;
  artist?: string;
  lyrics?: string;
  classification?: string;
  accuracy?: number | string;
}

export default function ProcessedSongs() {
  const { data, error } = useSWRSongs();

  if (error) return <div>Failed to load songs</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Processed Songs</h2>
      <div className="overflow-x-auto">
        <table className="w-full table-auto text-sm border border-gray-600">


          <thead>
            <tr>
              <th className="border p-2">Title</th>
              <th className="border p-2">Artist</th>
              <th className="border p-2">Lyrics</th>
              <th className="border p-2">Classification</th>
              <th className="border p-2">Accuracy</th>
            </tr>
          </thead>
          <tbody>
            
            {data.map((song: Song) => (
              <tr key={song.id}>
                <td className="border p-2">{song.title || '—'}</td>
                <td className="border p-2">{song.artist || '—'}</td>
                <td className="border p-2 text-xs font-mono break-words max-w-[30ch] overflow-hidden text-ellipsis whitespace-nowrap">
                  {song.lyrics || <span className="italic text-gray-400">No lyrics</span>}
                </td>


                <td className="border p-2">{song.classification || '—'}</td>
                <td className="border p-2">
                  {song.accuracy && !isNaN(Number(song.accuracy))
                    ? Number(song.accuracy).toFixed(2)
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
