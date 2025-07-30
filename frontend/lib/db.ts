import { Pool } from 'pg';

export const pool = new Pool({
  host: 'db', // docker-compose service name
  port: 5432,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB,
});

export async function insertSong({
  title,
  artist,
  duration,
  fingerprint,
  lyrics,
  classification,
  accuracy,
  stem_name,
}: {
  title: string;
  artist: string;
  duration: number;
  fingerprint: string;
  lyrics: string;
  classification: string;
  accuracy: number;
  stem_name: string;
}) {
  try {
    const res = await pool.query(
      `INSERT INTO songs (title, artist, duration, fingerprint, lyrics, classification, accuracy, stem_name)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING *`,
      [title, artist, duration, fingerprint, lyrics, classification, accuracy, stem_name]
    );
    return res.rows[0];
  } catch (err) {
    console.error("❌ Failed to insert song:", err);
    throw err;
  }
}