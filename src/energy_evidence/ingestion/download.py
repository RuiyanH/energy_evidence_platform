from urllib.request import Request, urlopen

DEFAULT_USER_AGENT = "energy-evidence-platform/1.0"

def download_url(url: str) -> bytes:
    """
    Downloads the content of a URL and returns it as bytes.
    """
    request = Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urlopen(request, timeout = 30) as response:
        return response.read()