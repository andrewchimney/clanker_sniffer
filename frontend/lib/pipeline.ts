import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';

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
