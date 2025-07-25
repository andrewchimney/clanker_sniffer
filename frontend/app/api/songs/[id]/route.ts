//GET /api/songs/:id** — full song result
//DELETE /api/songs/:id** — delete a record

export async function GET() {

  return new Response(JSON.stringify({sucess: true}), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}