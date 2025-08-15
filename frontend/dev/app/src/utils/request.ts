export async function fetchJsonContent(input: RequestInfo | URL, init?: RequestInit) {
  try {
    const res = await fetch(input, init);

    if (!res.ok) {
      throw new Error('Network response not ok');
    }

    return await res.json();
  } catch (error) {
    console.error(`Failed request ${error}`)
  }
}