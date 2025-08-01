// // - **POST /api/analyze**


// import { NextRequest } from 'next/server';
// import axios from 'axios';
// import FormData from 'form-data';


// export async function POST(req: NextRequest) {
//   try {

//     const formData = await req.formData();
//     const audioFile = formData.get('audio') as File;
//     const mode = formData.get("mode");
//     const title = formData.get('title');
//     const artist = formData.get('artist');
//     const lyricsData = formData.get('lyrics');
//     let lyrics = "";
//     if (typeof lyricsData === 'string') {
//       lyrics = lyricsData;
//     }

//     if (!audioFile) return new Response(JSON.stringify({ error: 'No file uploaded', status: 400 }));

//     const fileBuffer = Buffer.from(await audioFile.arrayBuffer());
//     const form = new FormData();
//     form.append('audio', fileBuffer, audioFile.name);
//     form.append('mode', mode);
//     if (title) form.append('title', title);
//     if (artist) form.append('artist', artist);
//     if (lyrics) form.append('lyrics', lyrics);

//     const response = await axios.post('http://clanker_orchestrator:8005/analyze', form, {
//       headers: form.getHeaders(),
//       maxContentLength: Infinity,
//       maxBodyLength: Infinity,
//     });

//     return new Response(JSON.stringify(response.data), {
//       status: 200,
//       headers: { 'Content-Type': 'application/json' },
//     });
//   } catch (err: any) {
//     console.error("❌ Error calling orchestrator:", err);
//     return new Response(
//       JSON.stringify({ error: 'Failed to reach orchestrator', details: err.message }),
//       { status: 500, headers: { 'Content-Type': 'application/json' } }
//     );
//   }
// }