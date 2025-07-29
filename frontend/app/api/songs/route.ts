//GET /api/songs** — list all processed songs
//POST /api/songs** — manually insert song/lyrics

import { pool } from '@/lib/db';
import { NextRequest } from 'next/server';

export async function GET(req: NextRequest) {
  try {
    const result = await pool.query('SELECT * FROM songs ORDER BY created_at DESC');
    return new Response(JSON.stringify(result.rows), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error('DB error in GET /api/songs:', err);
    return new Response(JSON.stringify({ error: 'Database error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
}

export async function POST() {

  return new Response(JSON.stringify({sucess: true}), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}