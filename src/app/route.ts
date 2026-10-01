import { readFile } from "node:fs/promises";
import { join } from "node:path";

export async function GET() {
  const html = await readFile(join(process.cwd(), "public", "index.html"), "utf8");
  return new Response(html, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
    },
  });
}
