import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { pool, insertSong } from '@/lib/db';
import axios from 'axios';
import FormData from 'form-data';

/**
 * Runs Demucs stem separation on a given audio file.
 * Returns stdout text (can be ignored since stem file path is known).
 */

export async function runDemucs(fileName: string): Promise<string> {
  const filePath = path.join("/shared_data", fileName);

  const form = new FormData();
  form.append("file", fs.createReadStream(filePath), fileName);

  try {
    const response = await axios.post("http://clanker_demucs:8000/separate", form, {
      headers: form.getHeaders(),
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
    });

    return response.data.message;
  } catch (err: any) {
    console.error("❌ Demucs API error:", err.response?.data || err.message);
    throw new Error(err.response?.data?.message || "Demucs POST failed");
  }
}

/**
 * Runs Whisper speech-to-text on a vocal stem file.
 * Returns lyrics object.
 */
export async function runWhisper(fileName: string): Promise<{ lyrics: string }> {
  try {
    const response = await axios.get("http://clanker_whisper:8001/transcribe", {
      params: { stem_name: fileName },
    });

    return response.data;
  } catch (err: any) {
    console.error("❌ Whisper API error:", err.response?.data || err.message);
    throw new Error(err.response?.data?.detail || "Whisper transcription failed");
  }
}

/**
 * Runs the AI lyric classifier with given lyrics.
 * Returns classification and accuracy.
 */
export async function runClassifier(lyrics: string): Promise<{ classification: string; accuracy: number }> {
  try {
    const response = await axios.post("http://clanker_classifier:8002/classify", {
      lyrics
    });

    return response.data;
  } catch (err: any) {
    console.error("❌ Classifier API error:", err.response?.data || err.message);
    throw new Error(err.response?.data?.detail || "Classifier failed");
  }
}
export async function runAcousti(fileName: string): Promise<{
  fingerprint: string;
  duration: number;
  matches: {
    title: string;
    artist: string;
  }[];
}> {
  try {
    const filePath = path.join('/shared_data', fileName);
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    formData.append('filename', fileName);

    const res = await axios.post(
      'http://clanker_acousti:8004/identify',
      formData,
      {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      }
    );

    return res.data;
  } catch (err: any) {
    console.error('❌ Acousti API error:', err?.response?.data || err.message);
    throw new Error('Acousti service failed');
  }
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