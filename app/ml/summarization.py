import requests
from bs4 import BeautifulSoup
from app.utils.logger import log_info, log_error
import os
from openai import OpenAI

def extractive_summary(text: str, max_sentences: int = 3) -> str:
    """
    Create an extractive summary of the text by selecting the most important sentences.
    This is used as a fallback when AI summarization is not available.
    
    Args:
        text (str): The text to summarize
        max_sentences (int): Maximum number of sentences to include in summary
        
    Returns:
        str: The summarized text
    """
    # Split text into sentences (simple implementation)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    if not sentences:
        return text
        
    # For simple implementation, return first few sentences
    summary = '. '.join(sentences[:max_sentences]) + '.'
    return summary

def summarize_url(url: str) -> str:
    """
    Fetch content from a URL and generate a summary using AI.
    
    Args:
        url (str): The URL to fetch and summarize
        
    Returns:
        str: AI-generated summary of the content
        
    Raises:
        Exception: If URL fetch fails or AI summarization fails
    """
    try:
        # Fetch URL content with User-Agent header to avoid 403 errors
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch URL: {url} with status {response.status_code}")
            
        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        
        # First try AI summarization
        try:
            # Get OpenAI API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OpenAI API key not configured")
            
            # Initialize OpenAI client
            client = OpenAI(api_key=api_key)
                
            # Generate summary using OpenAI
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": f"Summarize the following text in a few sentences, focusing on key points and technical details if present:\n\nContent from {url}:\n{text}\n\nSummary:"}
                ],
                max_tokens=200,
                temperature=0.5,
                top_p=1.0
            )
            
            summary = response.choices[0].message.content.strip()
            log_info(f"Successfully generated AI summary for URL: {url}")
            return summary
            
        except Exception as e:
            # If AI summarization fails, fall back to extractive summary
            log_error(f"AI summarization failed, falling back to extractive summary: {str(e)}")
            return extractive_summary(text)
        
    except Exception as e:
        log_error(f"Failed to summarize URL {url}: {str(e)}")
        raise Exception(f"Summarization failed: {str(e)}")
