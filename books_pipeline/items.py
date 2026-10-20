
"""Define the structured data model for scraped books."""

import scrapy


class BookItem(scrapy.Item):
    """Represent a book scraped from a category page."""

    title = scrapy.Field()
    price = scrapy.Field()
    availability = scrapy.Field()
    product_url = scrapy.Field()
    image_url = scrapy.Field()
    category = scrapy.Field()
