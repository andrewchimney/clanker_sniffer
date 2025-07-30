import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { pool, insertSong } from '@/lib/db';

/**
 * Runs Demucs stem separation on a given audio file.
 * Returns stdout text (can be ignored since stem file path is known).
 */
export function runDemucs(fileName: string): Promise<string> {
  return new Promise((resolve, reject) => {
    exec(
      `docker exec clanker_demucs python3 /app/demucs_runner.py "${fileName}"`,
      (error, stdout, stderr) => {
        if (error) {
          console.error("❌ Demucs error:", stderr);
          return reject(stderr);
        }
        resolve(stdout.trim());
      }
    );
  });
}

/**
 * Runs Whisper speech-to-text on a vocal stem file.
 * Returns lyrics object.
 */
export function runWhisper(fileName: string): Promise<{ lyrics: string }> {
  return new Promise((resolve, reject) => {
    exec(
      `docker exec clanker_whisper python3 /app/whisper_runner.py "${fileName}"`,
      (error, stdout, stderr) => {
        if (error) {
          console.error("❌ Whisper error:", stderr);
          return reject(stderr);
        }

        try {
          const parsed = JSON.parse(stdout);
          resolve(parsed);
        } catch (err) {
          console.error("❌ Whisper output parsing error:", err);
          reject("Invalid JSON from Whisper");
        }
      }
    );
  });
}

/**
 * Runs the AI lyric classifier with given lyrics.
 * Returns classification and accuracy.
 */
export function runClassifier(lyrics: string): Promise<{ classification: string; accuracy: number }> {
  return new Promise((resolve, reject) => {
    exec(
      `docker exec clanker_classifier python3 /app/classifier_runner.py "${lyrics}"`,
      (error, stdout, stderr) => {
        if (error) {
          console.error("❌ Classifier error:", stderr);
          return reject(stderr);
        }

        try {
          const parsed = JSON.parse(stdout);
          resolve(parsed);
        } catch (err) {
          console.error("❌ Classifier output parsing error:", err);
          reject("Invalid JSON from Classifier");
        }
      }
    );
  });
}
export function runAcousti(fileName: string): Promise<{
  fingerprint: string;
  duration: number;
  matches: {
    title: string;
    artist: string;
  }[];
}> {
  return new Promise((resolve, reject) => {
    exec(
      `docker exec clanker_acousti python3 /app/acousti_runner.py "${fileName}"`,
      (error, stdout, stderr) => {
        if (error) {
          console.error("❌ Acousti error:", stderr);
          return reject(stderr);
        }
        const parsed = JSON.parse(stdout);
        resolve(parsed);
      }
    );
  });
}


/**
 * Waits until a file exists (useful for syncing across containers).
 */
export function waitForFile(filePath: string, timeout = 10000): Promise<void> {
  const interval = 100;
  const start = Date.now();

  return new Promise((resolve, reject) => {
    const check = () => {
      if (fs.existsSync(filePath)) return resolve();

      if (Date.now() - start > timeout) {
        return reject(new Error(`Timeout: File ${filePath} not found`));
      }
      setTimeout(check, interval);
    };
    check();
  });
}

export async function dPipeline(fileName: string) {

  await waitForFile(path.join('/shared_data', fileName));
  await runDemucs(fileName);
  await waitForFile(path.join('/shared_data', "vocal_stems/", fileName));
  return {
    title: null,
    artist: null,
    duration: null,
    fingerprint: null,
    lyrics: null,
    classification: null,
    accuracy: null,
  };
}

export async function dwPipeline(fileName: string) {
  await waitForFile(path.join('/shared_data', fileName));
  await runDemucs(fileName);
  await waitForFile(path.join('/shared_data', "vocal_stems/", fileName));
  const whisperOut = await runWhisper(fileName);
  return {
    title: null,
    artist: null,
    duration: null,
    fingerprint: null,
    lyrics: whisperOut.lyrics,
    classification: null,
    accuracy: null,
  };
}

export async function dwcPipeline(fileName: string) {

  await waitForFile(path.join('/shared_data', fileName));

  const acoustiOut = await runAcousti(fileName);
  const existing = await pool.query('SELECT * FROM songs WHERE fingerprint = $1', [acoustiOut.fingerprint]);

  if (existing.rows.length > 0) {
    const fullPath = path.join('/shared_data', fileName);
    fs.unlinkSync(fullPath);

    return existing.rows[0];

  }

  const match = acoustiOut.matches?.[0] ?? { title: 'unknown', artist: 'unknown' };

  await runDemucs(fileName);
  await waitForFile(path.join('/shared_data/vocal_stems/', fileName));

  const whisperOut = await runWhisper(fileName);
  const classifierOut = await runClassifier(whisperOut.lyrics);

  const insertResult = await insertSong({
    title: match.title,
    artist: match.artist,
    duration: acoustiOut.duration,
    fingerprint: acoustiOut.fingerprint,
    lyrics: whisperOut.lyrics,
    classification: classifierOut.classification,
    accuracy: classifierOut.accuracy,
    stem_name: fileName,
  });

  return insertResult;
}


export async function cPipeline(lyrics: string) {
  const classifierOut = await runClassifier(lyrics);
  return {
    title: null,
    artist: null,
    duration: null,
    fingerprint: null,
    lyrics: lyrics,
    classification: classifierOut.classification,
    accuracy: classifierOut.accuracy,
  };
}