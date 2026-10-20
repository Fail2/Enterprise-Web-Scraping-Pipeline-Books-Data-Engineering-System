"""Discover categories, crawl their pages, and select five books per category."""
from urllib.parse import urljoin
import random
import scrapy


class BooksSpider(scrapy.Spider):
    """Crawl randomly selected book categories."""

    name = "books"
    allowed_domains = ["toscrape.com", "books.toscrape.com"]
    start_urls = ["https://toscrape.com"]

    def parse(self, response):
        """Discover the books store link dynamically."""
        books_url = response.css(
            'a[href*="books.toscrape.com"]::attr(href)'
        ).get()

        if not books_url:
            self.logger.error("Books store link not found on %s", response.url)
            return

        yield response.follow(books_url, callback=self.parse_categories)

    def parse_categories(self, response):
        """Discover categories and randomly select between five and ten."""
        categories = []

        for link in response.css(
            "div.side_categories ul li ul li a"
        ):
            name = link.css("::text").get(default="").strip()
            href = link.attrib.get("href")

            if name and href:
                categories.append({
                    "name": name,
                    "url": response.urljoin(href),
                })

        if not categories:
            self.logger.error("No categories found on %s", response.url)
            return

        count = random.randint(min(5, len(categories)), min(10, len(categories)))
        selected_categories = random.sample(categories, count)

        self.logger.info(
            "Discovered %d categories; selected %d",
            len(categories),
            count,
        )

        for category in selected_categories:
            self.logger.info("Selected category: %s", category["name"])

            yield response.follow(
                category["url"],
                callback=self.parse_category_page,
                cb_kwargs={
                    "category_name": category["name"],
                    "book_urls": [],
                },
            )

    def parse_category_page(self, response, category_name, book_urls):
        """Collect book URLs across every page of a category."""
        for href in response.css(
            "article.product_pod h3 a::attr(href)"
        ).getall():
            book_url = response.urljoin(href)

            if book_url not in book_urls:
                book_urls.append(book_url)

        next_page = response.css("li.next a::attr(href)").get()

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category_page,
                cb_kwargs={
                    "category_name": category_name,
                    "book_urls": book_urls,
                },
            )
            return

        if len(book_urls) < 5:
            self.logger.warning(
                "Category '%s' has only %d unique books",
                category_name,
                len(book_urls),
            )
            return

        selected_books = random.sample(book_urls, 5)

        self.logger.info(
            "Category '%s': collected %d unique books; selected exactly 5",
            category_name,
            len(book_urls),
        )

        for book_url in selected_books:
            yield response.follow(
                book_url,
                callback=self.parse_book,
                cb_kwargs={"category_name": category_name},
            )

    def parse_book(self, response, category_name):
        """Extract book details from its product page."""
        title = response.css("div.product_main h1::text").get(default="").strip()

        price = response.css("p.price_color::text").get(default="").strip()

        availability_text = " ".join(
            text.strip()
            for text in response.css(
                "div.product_main p.availability ::text"
            ).getall()
            if text.strip()
        )

        image_path = response.css(
            "div.item.active img::attr(src)"
        ).get()

        image_url = urljoin(response.url, image_path) if image_path else ""

        yield {
            "title": title,
            "price": price,
            "availability": availability_text,
            "product_url": response.url,
            "image_url": image_url,
            "category": category_name,
        }

