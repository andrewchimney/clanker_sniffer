// - **POST /api/analyze**

//   - Accepts: `.mp3` and flags to control pipeline steps
//   - Optional flags:
//     - `run_demucs`: bool
//     - `run_whisper`: bool
//     - `run_classifier`: bool
//   - Orchestrates the above 3 services
//   - Stores result in Postgres

import { pool } from '@/lib/db';
import { runDemucs, runWhisper, runClassifier, waitForFile } from '@/lib/pipeline';
import { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';


export async function POST(req: NextRequest) {


  const formData = await req.formData();
  const audioFile = formData.get('audio') as File;
  const useDemucs = formData.get('useDemucs') === 'true';
  const useWhisper = formData.get('useWhisper') === 'true';
  const useClassifier = formData.get('useClassifer') === 'true';
  const name = formData.get('name');
  const artist = formData.get('artist');


  if (!audioFile) return new Response(JSON.stringify({ error: 'No file uploaded', status: 400 }));

  const fileBuffer = Buffer.from(await audioFile.arrayBuffer());
  const sharedPath = '/shared_data';

  let fileName = `${Date.now()}_${audioFile.name}`;
  fileName = `${Date.now()}_${audioFile.name.replace(/[:\s]/g, "_")}`;
  const fullPath = path.join(sharedPath, fileName);

  // Make sure shared path exists
  fs.mkdirSync(sharedPath, { recursive: true });

  // Write to shared volume
  fs.writeFileSync(fullPath, fileBuffer);


  try {
    await waitForFile(path.join(sharedPath, fileName));
    const demucsOut = await runDemucs(fileName);
    await waitForFile(path.join(sharedPath,"vocal_stems/", fileName));
    const whisperOut = await runWhisper(fileName);
    const classifierOut = await runClassifier(whisperOut.lyrics);


    await pool.query(
      `INSERT INTO songs (name, artist, lyrics, classification, accuracy, stem_name)
     VALUES ($1, $2, $3, $4, $5, $6)`,
      [name, artist, whisperOut.lyrics, classifierOut.classification, classifierOut.accuracy, fileName]
    );


    return new Response(
      JSON.stringify({
        success: true,
        outputs: { demucsOut, whisperOut, classifierOut },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: String(err) }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}