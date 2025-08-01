import fs from 'fs';
import path from 'path';
import axios from 'axios';
import FormData from 'form-data';
export async function preprocess(audioFile: File): Promise<string> {
  const fileName = `${Date.now()}_${audioFile.name.replace(/[:\s]/g, "_")}`;
  const sharedPath = '/shared_data';
  fs.mkdirSync(sharedPath, { recursive: true });

  if (fileName.toLowerCase().endsWith('.wav')) {
    const finalPath = path.join(sharedPath, fileName);
    fs.writeFileSync(finalPath, Buffer.from(await audioFile.arrayBuffer()));
    return fileName;
  } else {
    const tempPath = path.join(sharedPath, fileName);
    fs.writeFileSync(tempPath, Buffer.from(await audioFile.arrayBuffer()));

    const form = new FormData();
    form.append("file", fs.createReadStream(tempPath));

    const res = await axios.post("http://clanker_acousti:8004/convert", form, {
      headers: form.getHeaders()
    });

    const converted = res.data.filename;
    fs.unlinkSync(tempPath);
    return converted;
  }
}