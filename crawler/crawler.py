import json
import os
from collections import deque
from urllib.parse import urljoin
import logging

import undetected_chromedriver as uc
from bs4 import BeautifulSoup

from crawler.helpers import extract_domain, random_delay
from config import CRAWLER_STATE_DIR

class Crawler:
    def __init__(self, start_url, web_graph, max_depth, db, batch_size=10, state_file='crawler_state.json'):
        """
        Initialize the crawler with the given parameters.

        Args:
            start_url (str): The starting URL for the crawler.
            web_graph: An object representing the web graph.
            max_depth (int): The maximum depth to crawl.
            db: The database object for storing crawled data.
            batch_size (int, optional): The number of pages to store in the database at a time. Defaults to 10.
            state_file (str, optional): The file to save the crawler state. Defaults to 'crawler_state.json'.
        """
        self.start_url = start_url
        self.web_graph = web_graph
        self.max_depth = max_depth
        self.db = db
        self.batch_size = batch_size
        self.pages_data = []
        self.n_pages_crawled = 0
        self.urls_to_crawl = deque()
        self.visited_urls = set() 
        self.state_file = os.path.join(CRAWLER_STATE_DIR, state_file)
        self.seen_urls = {}

        self.driver = None
        self.domain = extract_domain(start_url)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        self.load_state()

        if not self.urls_to_crawl:
            self.urls_to_crawl.append((start_url, 0))

        self.init_driver()

    def init_driver(self):
        """Initialize the Chrome driver."""
        if self.driver:
            self.driver.quit()
        self.driver = uc.Chrome(headless=True)

    def save_state(self):
        """Utility function to save the current state of crawler."""
        state = {
            'urls_to_crawl': list(self.urls_to_crawl),
            'visited_urls': list(self.visited_urls),
            'pages_data': self.pages_data
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f)

    def load_state(self):
        """Utility function to load a previous state of crawler and continue a previous crawling session."""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                self.urls_to_crawl = deque(tuple(item) for item in state.get('urls_to_crawl', []))
                self.visited_urls = set(state.get('visited_urls', []))
                self.pages_data = state.get('pages_data', [])

    def extract_page_data(self):
        """Extract page title and text content using BeautifulSoup."""
        try:
            title = self.driver.title
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
            return title, text
        except Exception as e:
            logging.error(f"Error extracting page data: {e}")
            return "", ""

    def extract_links(self, base_url):
        """Extract all href links from the page source using BeautifulSoup."""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            full_url = urljoin(base_url, a.get('href'))
            if full_url not in self.seen_urls:
                links.add(full_url)
        links.discard(base_url)
        return links

    def is_404_page(self):
        """Check if the current page indicates a 404 error."""
        try:
            return "404" in self.driver.title
        except Exception as e:
            logging.error(f"Error checking for 404 page: {e}")
            return False

    def crawl(self):
        """Recursive driver function used for crawling, uses depth first search approach."""
        while self.urls_to_crawl:
            url, depth = self.urls_to_crawl.popleft()
            if depth > self.max_depth or url in self.visited_urls:
                continue

            try:
                self.driver.get(url)
                random_delay(2, 5)

                title, text = self.extract_page_data()

                if self.is_404_page():
                    logging.info(f"Skipping non-existent page (404): {url}")
                    continue

                logging.info(f"Crawled {url} with title: {title}")

                current_node = self.web_graph.add_node(url, depth)
                current_node.title = title
                current_node.text = text

                page_data = {
                    'url': url,
                    'depth': depth,
                    'title': title,
                    'text': text
                }
                self.pages_data.append(page_data)
                self.visited_urls.add(url)

                if len(self.pages_data) >= self.batch_size:
                    logging.info(f"Inserting {len(self.pages_data)} pages into MongoDB")
                    self.db.insert_pages(self.pages_data)
                    self.pages_data = []

                links = self.extract_links(url)
                for href in links:
                    if href and extract_domain(href) == self.domain:
                        if not self.web_graph.get_node(href):
                            self.web_graph.add_node(href, depth + 1)

                        self.web_graph.add_edge(url, href)
                        if not self.web_graph.get_node(href).visited:
                            if href not in self.seen_urls:
                                self.seen_urls[href] = None
                                self.urls_to_crawl.append((href, depth + 1))
                                self.n_pages_crawled += 1
                                logging.info(f"Added {href} to crawl list (Index: {self.n_pages_crawled})")

                current_node.visited = True

            except Exception as e:
                logging.error(f"Failed to crawl {url}: {e}")
                logging.info("Restarting the browser driver.")
                self.init_driver()

            finally:
                self.save_state()

    def start_crawling(self):
        """Start the crawling process."""
        self.crawl()

        if self.pages_data:
            logging.info(f"Inserting remaining {len(self.pages_data)} pages into MongoDB")
            self.db.insert_pages(self.pages_data)
            self.pages_data = []

        self.driver.quit()
        self.save_state()