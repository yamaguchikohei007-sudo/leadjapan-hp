// Cloudflare Pages Function for /pm-book-bonus/download (see _routes.json, written by build.py).
// The password form on /pm-book-bonus posts here; see bonus/download.js.
import file from "../../bonus/pm-book-gantt-tool.js";
import { FORM_PAGE, handlePost } from "../../bonus/download.js";

export function onRequestPost(context) {
  return handlePost(context.request, file);
}

// Opened directly (bookmark, reload): back to the form.
export function onRequestGet() {
  return new Response(null, { status: 303, headers: { Location: FORM_PAGE } });
}
