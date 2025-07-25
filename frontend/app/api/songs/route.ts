//GET /api/songs** — list all processed songs
//POST /api/songs** — manually insert song/lyrics

export async function GET() {

  return new Response(JSON.stringify({suc: true}), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}

export async function POST() {

  return new Response(JSON.stringify({sucess: true}), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}