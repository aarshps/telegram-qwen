import sys
import urllib.request
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.ignore_tags = {'script', 'style', 'head', 'title', 'meta', '[document]'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.ignore_tags:
            content = data.strip()
            if content:
                self.text.append(content)

    def get_text(self):
        return '\n'.join(self.text)

def fetch_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            
            parser = TextExtractor()
            parser.feed(html_content)
            print(f"--- CONTENT FROM {url} ---")
            print(parser.get_text()[:10000]) # Scan first 10k chars to avoid overload
            print("\n--- END OF CONTENT ---")
            
    except Exception as e:
        print(f"Error fetching URL: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python web_reader.py <url>")
    else:
        # Force UTF-8 output even on Windows console
        sys.stdout.reconfigure(encoding='utf-8')
        fetch_url(sys.argv[1])
