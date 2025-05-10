import requests
from bs4 import BeautifulSoup

def fetch_url_text(url: str) -> str:
    """
    Fetch the URL content and extract visible text for analysis.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "noscript"]):
            script_or_style.decompose()
        
        # Get visible text
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception as e:
        return f"Error fetching URL content: {str(e)}"
