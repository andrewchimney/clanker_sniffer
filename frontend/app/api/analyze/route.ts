// - **POST /api/analyze**

//   - Accepts: `.mp3` and flags to control pipeline steps
//   - Optional flags:
//     - `run_demucs`: bool
//     - `run_whisper`: bool
//     - `run_classifier`: bool
//   - Orchestrates the above 3 services
//   - Stores result in Postgres


import { exec } from 'child_process';
import { NextRequest } from 'next/server';

// export async function GET() {

//   return new Response(JSON.stringify({sucess: true}), {
//     status: 200,
//     headers: { "Content-Type": "application/json" },
//   });
// }

export async function POST(req: NextRequest) {

  //const { filepath } = await req.json();
  const inputString = "testing"

  // Step 1: Run Demucs
  const runDemucs = () =>
    new Promise((resolve, reject) => {
      exec(
        `docker exec clanker_demucs python3 /app/demucs_runner.py "${inputString}"`,
        (error, stdout, stderr) => {
          if (error) return reject(stderr);
          resolve(stdout);
        }
      );
    });

  // Step 2: Run Whisper
  const runWhisper = () =>
    new Promise((resolve, reject) => {
      exec(
        `docker exec clanker_whisper python3 /app/whisper_runner.py "${inputString}"`,
        (error, stdout, stderr) => {
          if (error) return reject(stderr);
          resolve(stdout);
        }
      );
    });

  // Step 3: Run Classifier
  const runClassifier = () =>
    new Promise((resolve, reject) => {
      exec(
        `docker exec clanker_classifier python3 /app/classifier_runner.py "${inputString}"`,
        (error, stdout, stderr) => {
          if (error) return reject(stderr);
          resolve(stdout);
        }
      );
    });

  try {
    const demucsOut = await runDemucs();
    const whisperOut = await runWhisper();
    const classifierOut = await runClassifier();

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
