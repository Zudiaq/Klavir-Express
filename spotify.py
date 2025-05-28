addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const mp3Link = url.searchParams.get("url");
  if (!mp3Link) {
    return new Response("Missing 'url' parameter", { status: 400 });
  }

  try {
    const encodedMp3Link = encodeURI(mp3Link); // Ensure proper encoding of the URL
    const response = await fetch(encodedMp3Link, { method: "HEAD" });
    if (response.ok) {
      return new Response(encodedMp3Link);
    } else {
      return new Response("Failed to validate MP3 link", { status: 400 });
    }
  } catch (error) {
    return new Response("Error processing request", { status: 500 });
  }
}
