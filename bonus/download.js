// Reader bonus download: checks the reader password and hands out the file.
// Used by functions/pm-book-bonus/download.js (the form on /pm-book-bonus posts there).
//
// Only a SHA-256 hash of the password is kept here, so the password itself is
// never in the site or the repository. Change it with:
//   python3 -c "import hashlib,unicodedata;print(hashlib.sha256(unicodedata.normalize('NFKC',input()).strip().lower().encode()).hexdigest())"
export const PASSWORD_SHA256 = "408a5aacb0c57887c68643c79d194b863b73689c98bb5c706c7b17a57979119a";

export const FORM_PAGE = "/pm-book-bonus.html";
export const ERROR_PAGE = "/pm-book-bonus-error.html";
const FILENAME_ASCII = "PM_FirstBook_gantt-chart-tool.html";
const FILENAME = "PM_FirstBook_ガントチャート作成支援ツール.html";

// Readers type what is printed in the book, often with a Japanese IME: full-width
// letters, stray spaces and capitals are all accepted.
export function normalize(input) {
  return String(input ?? "").normalize("NFKC").trim().toLowerCase();
}

export async function sha256Hex(text) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function seeOther(location) {
  return new Response(null, { status: 303, headers: { Location: location, "Cache-Control": "no-store" } });
}

export async function handlePost(request, file, expectedHash = PASSWORD_SHA256) {
  let password = "";
  try {
    password = (await request.formData()).get("password");
  } catch {
    return seeOther(ERROR_PAGE);
  }
  if (typeof password !== "string" || password.length > 200) return seeOther(ERROR_PAGE);
  if ((await sha256Hex(normalize(password))) !== expectedHash) return seeOther(ERROR_PAGE);
  return new Response(file, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Disposition": `attachment; filename="${FILENAME_ASCII}"; filename*=UTF-8''${encodeURIComponent(FILENAME)}`,
      "Cache-Control": "private, no-store",
      "X-Robots-Tag": "noindex",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
