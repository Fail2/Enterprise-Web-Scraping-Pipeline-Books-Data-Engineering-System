
"""Clean scraped book data and persist it to SQLite."""

import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class BooksPipeline:
    """Normalize, validate, and store book items in SQLite."""

    def __init__(self, database_path):
        """Initialize the pipeline with the database file path."""
        self.database_path = database_path
        self.connection = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def from_crawler(cls, crawler):
        """Create the pipeline using Scrapy project settings."""
        database_path = crawler.settings.get(
            "SQLITE_DATABASE", "books.db"
        )
        return cls(database_path)

    def open_spider(self, spider):
        """Open the database connection and create the books table."""
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(str(path))

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                availability BOOLEAN NOT NULL,
                product_url TEXT NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT NOT NULL
            )
            """
        )
        self.connection.execute("DELETE FROM books")

        self.connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_books_product_url
            ON books(product_url)
        """)
        self.connection.commit()

        self.logger.info("SQLite database opened: %s", path)

    def process_item(self, item, spider):
        """Clean, validate, and store one scraped book item."""
        adapter = ItemAdapter(item)

        # Normalize text fields and remove surrounding whitespace.
        text_fields = (
            "title",
            "product_url",
            "image_url",
            "category",
            "availability",
        )

        for field in text_fields:
            value = adapter.get(field)

            if value is None:
                value = ""
            elif not isinstance(value, str):
                value = str(value)

            adapter[field] = unicodedata.normalize(
                "NFKC", value
            ).strip()

        # Reject records missing required fields.
        required_fields = (
            "title",
            "product_url",
            "image_url",
            "category",
            "availability",
            "price",
        )

        missing_fields = [
            field
            for field in required_fields
            if adapter.get(field) in (None, "")
        ]

        if missing_fields:
            raise DropItem(
                f"Missing required fields {missing_fields}: "
                f"{adapter.get('product_url', 'unknown URL')}"
            )

        # Remove currency symbols and convert the price to float.
        raw_price = str(adapter["price"]).strip()
        numeric_price = re.sub(r"[^\d.]", "", raw_price)

        try:
            price = float(numeric_price)
        except (ValueError, TypeError):
            raise DropItem(
                f"Invalid price {raw_price!r} for "
                f"{adapter['product_url']}"
            )

        if not numeric_price or price < 0:
            raise DropItem(
                f"Invalid price {raw_price!r} for "
                f"{adapter['product_url']}"
            )

        adapter["price"] = price


        # Normalize availability to a real Python boolean.
        availability_text = adapter["availability"].casefold().strip()
        adapter["availability"] = availability_text.startswith("in stock")


        existing_book = self.connection.execute(
            "SELECT 1 FROM books WHERE product_url = ?",
            (adapter["product_url"],),
        ).fetchone()

        if existing_book:
            self.logger.warning(
                "Duplicate book skipped: %s",
                adapter["product_url"],
            )
            raise DropItem(
                f"Duplicate book: {adapter['product_url']}"
            )


        # Store exactly the cleaned values that Scrapy exports.
        self.connection.execute(
            """
            INSERT INTO books (
                title,
                price,
                availability,
                product_url,
                image_url,
                category
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                adapter["title"],
                adapter["price"],
                adapter["availability"],
                adapter["product_url"],
                adapter["image_url"],
                adapter["category"],
            ),
        )
        self.connection.commit()

        self.logger.info(
            "Processed book: %s | category=%s",
            adapter["title"],
            adapter["category"],
        )

        return item

    def close_spider(self, spider):
        """Close the SQLite connection when crawling finishes."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

        self.logger.info("SQLite database connection closed.")
