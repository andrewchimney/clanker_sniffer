// components/ProcessedSongs.tsx
'use client';

import useSWR from 'swr';

export default function ProcessedSongs() {
  const fetcher = (url: string) => fetch(url).then(res => res.json());
  const { data, error } = useSWR('/api/songs', fetcher);

  if (error) return <div>Failed to load songs</div>;
  if (!data) return <div>Loading...</div>;
  console.log(data)

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Processed Songs</h2>
      <table className="w-full text-sm border">
        <thead>
          <tr>
            <th className="border p-2">Name</th>
            <th className="border p-2">Artist</th>
            <th className="border p-2">Lyrics</th>
            <th className="border p-2">Classification</th>
            <th className="border p-2">Accuracy</th>
          </tr>
        </thead>
        <tbody>
          {data.map((song: any) => (
            <tr key={song.id}>
              <td className="border p-2">{song.name}</td>
              <td className="border p-2">{song.artist}</td>
              <td className="border p-2 line-clamp-2 max-w-xs">{song.lyrics}</td>
              <td className="border p-2">{song.classification}</td>
              <td className="border p-2">{Number(song.accuracy)?.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}