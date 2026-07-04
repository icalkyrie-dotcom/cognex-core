import httpx
from bs4 import BeautifulSoup


def read_url(url: str, max_chars: int = 3000) -> str:
    """
    Membaca dan mengekstrak konten teks dari URL.
    Return: string berisi konten yang sudah dibersihkan.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        with httpx.Client(timeout=10, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Hapus elemen yang tidak perlu
        for tag in soup(["script", "style", "nav", "footer",
                         "header", "aside", "form"]):
            tag.decompose()

        # Ambil teks utama
        text = soup.get_text(separator="\n", strip=True)

        # Bersihkan blank lines berlebihan
        lines = [line for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        # Truncate kalau terlalu panjang
        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n\n[... konten dipotong]"

        return f"Konten dari {url}:\n\n{clean_text}"

    except httpx.TimeoutException:
        return f"Timeout saat mengakses URL: {url}"
    except httpx.HTTPStatusError as e:
        return f"HTTP error {e.response.status_code} saat akses: {url}"
    except Exception as e:
        return f"Gagal membaca URL: {str(e)}"