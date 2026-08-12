import type { APIRoute } from "astro";
import fs from "node:fs";
import path from "node:path";
import { groupPostMedia, groupPosts } from "../../lib/groupPosts";

export const prerender = true;

const media = [...new Set(groupPosts.flatMap(groupPostMedia))].map((savedPath) => {
  const relativePath = savedPath.replace(/^images\//, "");
  return {
    relativePath,
    absolutePath: path.resolve("fb_group_archive/images", relativePath)
  };
});

export function getStaticPaths() {
  return media.map((item) => ({ params: { path: item.relativePath }, props: item }));
}

export const GET: APIRoute = ({ props }) => {
  const absolutePath = String(props.absolutePath);
  const extension = path.extname(absolutePath).toLowerCase();
  const contentTypes: Record<string, string> = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp"
  };
  return new Response(fs.readFileSync(absolutePath), {
    headers: {
      "Content-Type": contentTypes[extension] || "application/octet-stream",
      "Cache-Control": "public, max-age=31536000, immutable"
    }
  });
};
