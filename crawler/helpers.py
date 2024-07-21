from urllib.parse import urlparse
import time
import random

def extract_domain(url):
    """Extract the domain from a URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def random_delay(min_delay=1, max_delay=3):
    """Introduce a random delay to mimic human browsing behavior."""
    time.sleep(random.uniform(min_delay, max_delay))