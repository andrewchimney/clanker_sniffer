import { Pool } from 'pg';

export const pool = new Pool({
  host: 'db', // docker-compose service name
  port: 5432,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  database: process.env.POSTGRES_DB,
});

export async function insertSong({
  name,
  artist,
  lyrics,
  classification,
  accuracy,
  stem_name,
}: {
  name: string | null;
  artist: string | null;
  lyrics: string;
  classification: string;
  accuracy: number;
  stem_name: string;
}) {
  return pool.query(
    `INSERT INTO songs (name, artist, lyrics, classification, accuracy, stem_name)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [name, artist, lyrics, classification, accuracy, stem_name]
  );
}
