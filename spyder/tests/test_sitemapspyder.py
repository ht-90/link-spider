from django.test import TestCase
from bs4 import BeautifulSoup

from ..sitemapspyder import SitemapSpyder


URL = "https://test.com"

MAX_CRAWL = 5

SITEMAP = """
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
    <url>
      <loc>https://test.com/page1/</loc>
      <lastmod>2020-05-01T09:00:00+10:00</lastmod>
    </url>
    <url>
       <loc>https://test.com/page2/</loc>
       <lastmod>2020-05-02T14:00:00+10:00</lastmod>
     </url>
    <url>
      <loc>https://test.com/page3/</loc>
      <lastmod>2020-05-03T20:00:00+10:00</lastmod>
    </url>
  </urlset>
"""

PAGE_1 = """
  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>PAGE_1</title>
      <meta name="description" content="Page 1 Description">
    </head>
    <body>
      <div>
        <a href="https://page_2">Internal Link to Page 2</a>
        <a href="https://page_3">Internal Link to Page 3</a>
      </div>
    </body>
  </html>
"""

PAGE_2 = """
  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>PAGE_2</title>
      <meta name="description" content="Page 2 Description">
    </head>
    <body>
      <div>
        <a href="https://page_1">Internal Link to Page 1</a>
        <a href="https://page_3">Internal Link to Page 3</a>
      </div>
    </body>
  </html>
"""

PAGE_3 = """
  <!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>PAGE_3</title>
      <meta name="description" content="Page 1 Description">
    </head>
    <body>
      <div>
        <a href="https://page_1">Internal Link to Page 1</a>
        <a href="https://page_2">Internal Link to Page 2</a>
      </div>
    </body>
  </html>
"""


class TestSitemapSpyder(TestCase):

    def setUp(self):
        self.crawler = SitemapSpyder(
            url=URL,
            max_crawl=MAX_CRAWL,
        )

    def test_retrieve_domain(self):
        """Test extracting domain name from url"""
        domain = self.crawler.retrieve_domain()
        self.assertEqual(domain, "test.com")

    def test_parse_sitemap_loc(self):
        """Ensure all urls in sitemap are extracted"""
        locs_url = self.crawler.parse_sitemap(sitemap=SITEMAP)
        self.assertEqual(len(locs_url), 3)

    def test_parse_sitemap_strip(self):
        """Ensure '/' is stripped out from all urls in sitemap"""
        locs_url = self.crawler.parse_sitemap(sitemap=SITEMAP)
        last_letters = [url[-1] for url in locs_url]
        self.assertTrue("/" not in last_letters)

    def test_extract_a_tags(self):
        """Ensure anchor tags and hrefs are extracted from a page"""
        soup = BeautifulSoup(PAGE_1, "html.parser")
        a_tags = self.crawler.extract_a_tags(soup=soup)
        self.assertEqual(len(a_tags), 2)
        self.assertEqual(a_tags[0].get("href"), "https://page_2")
        self.assertEqual(a_tags[1].get("href"), "https://page_3")

    def test_retrieve_a_tags(self):
        """Test retrieval of anchor tags and formation of origin page to destination pages list"""
        locs_url = self.crawler.parse_sitemap(sitemap=SITEMAP)
        pages = [
            [locs_url[0], BeautifulSoup(PAGE_1, "html.parser")],
            [locs_url[0], BeautifulSoup(PAGE_2, "html.parser")],
            [locs_url[0], BeautifulSoup(PAGE_3, "html.parser")],
        ]
        list_page_od = self.crawler.retrieve_a_tags(parsed_pages=pages)
        self.assertEqual(len(list_page_od), 3)
        self.assertEqual(len(list_page_od[0][1]), 2)
        self.assertEqual(len(list_page_od[1][1]), 2)
        self.assertEqual(len(list_page_od[2][1]), 2)

    def test_convert_to_absolute_url(self):
        """Test conversion of relative URL to absolute URL"""
        href_rel_url = "/page_1"
        abs_url = self.crawler.convert_to_absolute_url(href=href_rel_url)
        self.assertEqual(abs_url, "https://test.com/page_1")

    def test_normalize_url(self):
        """Test normalization of ugly URLs"""
        # Prepare ugly URLs
        url_slash = URL + "/"
        url_double_slash = URL + "//" + "page_1"
        url_param = URL + "/" + "page_1" + "/" + "?param=abc"

        # Normalize ugly URLs
        norm_url_slash = self.crawler.normalize_url(url=url_slash)
        norm_url_double_slash = self.crawler.normalize_url(url=url_double_slash)
        norm_url_param = self.crawler.normalize_url(url=url_param)

        self.assertEqual(norm_url_slash, "https://test.com")
        self.assertEqual(norm_url_double_slash, "https://test.com/page_1")
        self.assertEqual(norm_url_param, "https://test.com/page_1")

    def test_page_url_validator(self):
        """Ensure page URL validator catches invalid URL"""
        # Prepare valid URLs
        valid_url = "https://test.com/page_1/post_1"

        # Prepare invalid URLs
        invalid_url_netloc = "http://test/page_1"
        invalid_url_scheme = "test.com"
        invalid_url_localhost_1 = "http://localhost:8000"
        invalid_url_localhost_2 = "http://127.0.0.1:8000"

        # Run validator
        self.assertTrue(self.crawler._page_is_valid(url=valid_url))
        self.assertFalse(self.crawler._page_is_valid(url=invalid_url_netloc))
        self.assertFalse(self.crawler._page_is_valid(url=invalid_url_scheme))
        self.assertFalse(self.crawler._page_is_valid(url=invalid_url_localhost_1))
        self.assertFalse(self.crawler._page_is_valid(url=invalid_url_localhost_2))
