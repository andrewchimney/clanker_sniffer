// - **POST /api/analyze**

//   - Accepts: `.mp3` and flags to control pipeline steps
//   - Optional flags:
//     - `run_demucs`: bool
//     - `run_whisper`: bool
//     - `run_classifier`: bool
//   - Orchestrates the above 3 services
//   - Stores result in Postgres
import { exec } from 'child_process';
import { dPipeline, dwPipeline, dwcPipeline, cPipeline } from '@/lib/pipeline';

import { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';
import { promisify } from 'util';


export async function POST(req: NextRequest) {


  const formData = await req.formData();
  const audioFile = formData.get('audio') as File;
  const mode = formData.get("mode");
  const title = formData.get('title');
  const artist = formData.get('artist');
  const lyricsData = formData.get('lyrics');
  let lyrics = "";
  if (typeof lyricsData === 'string') {
    lyrics = lyricsData;
  }
  



  if (!audioFile) return new Response(JSON.stringify({ error: 'No file uploaded', status: 400 }));

  const fileName = `${Date.now()}_${audioFile.name.replace(/[:\s]/g, "_")}`;
  const sharedPath = '/shared_data';
  fs.mkdirSync(sharedPath, { recursive: true });

  let finalFileName: string;
  let finalPath: string;

  if (fileName.toLowerCase().endsWith('.wav')) {
    // Already WAV — just save it directly
    finalFileName = fileName;
    finalPath = path.join(sharedPath, finalFileName);
    fs.writeFileSync(finalPath, Buffer.from(await audioFile.arrayBuffer()));
  } else {
    // Save temp MP3 and convert
    const tempPath = path.join(sharedPath, fileName);
    fs.writeFileSync(tempPath, Buffer.from(await audioFile.arrayBuffer()));

    finalFileName = fileName.replace(/\.[^/.]+$/, '.wav');
    finalPath = path.join(sharedPath, finalFileName);


    try {
      const execAsync = promisify(exec);
      //await execAsync(`ffmpeg -y -i "${tempPath}" -ar 44100 -ac 2 "${finalPath}"`);
      await execAsync(`ffmpeg -y -i "${tempPath}" -acodec pcm_s16le -ar 44100 -ac 2 "${finalPath}"`);

      
      fs.unlinkSync(tempPath); // 🗑️ Remove temp MP3
      console.log(`✅ Converted and saved: ${finalFileName}`);
    } catch (err) {
      console.error("❌ Conversion failed:", err);
      return new Response(JSON.stringify({ error: 'Audio conversion failed' }), { status: 500 });
    }
  }





  try {
    let out;

    switch (mode) {
      case 'demucs':
        out = await dPipeline(finalFileName);
        break;
      case 'demucs-whisper':
        out = await dwPipeline(finalFileName);
        break;
      case 'demucs-whisper-classifier':
        out = await dwcPipeline(finalFileName);
        break;
      case 'classifier-text':
        out = await cPipeline(lyrics);
        break;
      default:
        throw new Error(`Invalid mode: ${mode}`);
    }

    return new Response(
      JSON.stringify({
        success: true,
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