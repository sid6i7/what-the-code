import time
import random
from urllib.parse import urljoin
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from crawler.helpers import extract_domain

class Crawler:
    def __init__(self, start_url, web_graph, max_depth):
        self.domain = extract_domain(start_url)
        self.start_url = start_url
        self.web_graph = web_graph
        self.max_depth = max_depth
        self.driver = uc.Chrome(headless=True)

    def random_delay(self, min_delay=1, max_delay=3):
        """Introduce a random delay to mimic human browsing behavior."""
        time.sleep(random.uniform(min_delay, max_delay))

    def extract_page_data(self):
        """Extract page title and text content using BeautifulSoup."""
        try:
            title = self.driver.title
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return title, text
        except Exception as e:
            print(f"Error extracting page data: {e}")
            return "", ""

    def extract_links(self, base_url):
        """Extract all href links from the page source using BeautifulSoup."""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        links = [urljoin(base_url, a.get('href')) for a in soup.find_all('a', href=True)]
        return links

    def crawl(self, url, depth):
        if depth > self.max_depth:
            return
        
        try:
            self.driver.get(url)
            self.random_delay(2, 5)
            title, text = self.extract_page_data()
            current_node = self.web_graph.add_node(url, depth)
            current_node.title = title
            current_node.text = text

            links = self.extract_links(url)
            print(f"Found {len(links)} at depth {depth} for {url}")
            for href in links:
                if href and extract_domain(href) == self.domain:
                    if not self.web_graph.get_node(href):
                        self.web_graph.add_node(href, depth + 1)
                    self.web_graph.add_edge(url, href)

                    if not self.web_graph.get_node(href).visited:
                        self.crawl(href, depth + 1)

            current_node.visited = True

        except Exception as e:
            print(f"Failed to crawl {url}: {e}")

    def start_crawling(self):
        self.crawl(self.start_url, 0)
        self.driver.quit()