from urllib.parse import urlparse

def extract_domain(url):
    """Extract the domain from a URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain