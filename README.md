# Enterprise Web Scraping Pipeline – Books Data Engineering System

## 1. Project Overview

This project is an automated web scraping pipeline built with Scrapy to collect book data from [Books to Scrape](https://books.toscrape.com/). It dynamically discovers categories, selects random categories and books, cleans the collected data, exports it into multiple formats, and stores it in an SQLite database.

## 2. Features

- Dynamically discovers book categories and URLs.
- Randomly selects 5–10 categories.
- Collects all book URLs across category pagination and randomly selects exactly 5 books per selected category.
- Extracts title, price, availability, product URL, image URL, and category.
- Cleans and normalizes scraped data.
- Converts prices to numeric values and availability to Boolean values.
- Exports data to JSON, CSV, and XML.
- Stores processed data in SQLite.
- Supports Docker containerization and Scrapyd deployment.
- Includes logging and duplicate-record handling.

## 3. Tech Stack

- **Python** – Core programming language
- **Scrapy** – Web scraping framework
- **SQLite** – Database storage
- **Docker** – Containerization
- **Scrapyd** – Spider deployment and scheduling
- **scrapyd-client** – Deployment command-line tool

## 4. Installation Guide

Clone the repository:

```bash
git clone https://github.com/Fail2/Enterprise-Web-Scraping-Pipeline-Books-Data-Engineering-System.git
cd Enterprise-Web-Scraping-Pipeline-Books-Data-Engineering-System
```

Create and activate a virtual environment.

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 5. Environment Setup

The project uses Scrapy settings to configure the spider, processing pipeline, database, and feed exports.

Important configuration values are defined in `books_pipeline/settings.py`:

- `SPIDER_MODULES` – Spider package location
- `ITEM_PIPELINES` – Data processing pipeline
- `FEEDS` – JSON, CSV, and XML export configuration
- `SQLITE_DATABASE` – SQLite database location
- `ROBOTSTXT_OBEY` – Respects the website's robots.txt rules

No environment variables are required by default. If the database path or other settings are customized, update the configuration accordingly.

## 6. Running the Spider

Run the spider locally:

```bash
scrapy crawl books
```

The spider discovers categories dynamically, selects 5–10 categories, follows pagination to collect book URLs, and selects five books from each selected category.

Generated files are configured to be saved in the `output/` directory:

- `books.json`
- `books.csv`
- `books.xml`
- `books.db`

The exact output depends on the categories and books randomly selected during each run.

## 7. Docker Setup Guide

### Build the Docker Image

Run from the project root:

```bash
docker build -t books-scrapyd .
```

### Start a New Container

```bash
docker run -d --name books-scrapyd -p 6800:6800 books-scrapyd
```

Scrapyd will be available at:

`http://localhost:6800`

### Manage Containers

List all containers:

```bash
docker ps -a
```

List running containers:

```bash
docker ps
```

Start an existing container:

```bash
docker start books-scrapyd
```

Stop a running container:

```bash
docker stop books-scrapyd
```

Restart a container:

```bash
docker restart books-scrapyd
```

### Delete a Container

Stop and remove the container:

```bash
docker stop books-scrapyd
docker rm books-scrapyd
```

Or force-remove it:

```bash
docker rm -f books-scrapyd
```

### Delete the Docker Image

List images:

```bash
docker images
```

Remove the image after removing containers that use it:

```bash
docker rmi books-scrapyd
```

**Important:** `docker start` starts an existing container, whereas `docker run` creates a new one. If a container name or host port is already in use, remove the old container or use an available name and port.

Container removal may delete data stored only inside the container. Use a Docker volume or bind mount if generated files and database data must persist outside the container.

## 8. Scrapyd Deployment Guide

Scrapyd runs the spider as a deployable project and provides an HTTP API for scheduling jobs.

### Start Scrapyd Locally

Open **Terminal 1** from your project environment and run:

```bash
scrapyd
```

This starts the Scrapyd server at `http://localhost:6800`. Keep this terminal running.

Verify that Scrapyd is running by opening **Terminal 2**:

```bash
curl http://localhost:6800/daemonstatus.json
```

### Deploy the Project

In Terminal 2, navigate to the project root directory where `scrapy.cfg` is located.

Configure `scrapy.cfg` with the Scrapyd deployment URL and project name.

Deploy using `scrapyd-client`:

```bash
cd books_pipeline
scrapyd-deploy
```

If your configuration defines a deployment target named `default`, you can use:

```bash
scrapyd-deploy default
```

The deployment target and its configuration must match your local `scrapy.cfg` setup.

### Check the Deployment

List deployed projects:

```bash
curl http://localhost:6800/listprojects.json
```

List spiders in the project:

```bash
curl "http://localhost:6800/listspiders.json?project=books_pipeline"
```

### Execute the Spider Through the API

```bash
curl http://localhost:6800/schedule.json \
  -d project=books_pipeline \
  -d spider=books
```

Check job status:

```bash
curl "http://localhost:6800/listjobs.json?project=books_pipeline"
```

After changing the source code, redeploy the project before scheduling the updated spider.

## 9. Output Format Description

The pipeline exports the processed records into three formats:

- **JSON (`books.json`)** – Structured data suitable for APIs and applications.
- **CSV (`books.csv`)** – Tabular data suitable for spreadsheets and analysis.
- **XML (`books.xml`)** – Structured data suitable for XML-compatible systems.

Each record contains:

| Field | Description |
|---|---|
| `title` | Book title |
| `price` | Numeric book price |
| `availability` | Boolean stock status |
| `product_url` | URL of the book's product page |
| `image_url` | URL of the book's image |
| `category` | Category name |

The feed exporter processes items after the configured item pipeline, so exported records should correspond to successfully processed and accepted database records.

## 10. Database Configuration

The project uses SQLite to store processed book records.

The database path is configured through `SQLITE_DATABASE` in `books_pipeline/settings.py`.

The pipeline creates the database table if it does not exist and inserts normalized records. Duplicate product URLs are rejected.

Example SQL queries:

```sql
SELECT * FROM books;

SELECT COUNT(*) FROM books;

SELECT category, COUNT(*)
FROM books
GROUP BY category;
```

Open the database with an SQLite client or use Python's built-in `sqlite3` module.

**Note:** The current pipeline clears existing book records when a crawl starts. Therefore, each run replaces the previous database contents rather than preserving a historical collection. Configure persistent storage when running in Docker if the database must survive container removal.

## 11. Architecture Diagram

```text
Books to Scrape Website
          |
          v
Category Discovery
          |
          v
Random Category Selection
       (5–10)
          |
          v
Category Pagination
          |
          v
Book URL Collection
          |
          v
Random Book Selection
     (5 per category)
          |
          v
Scrapy Spider
          |
          v
Data Cleaning Pipeline
          |
          +------------------+
          |                  |
          v                  v
    Feed Exporter        SQLite DB
          |
          +--------+--------+
                   |
           JSON / CSV / XML
```

Scrapyd can deploy and schedule the spider, while Docker provides the containerized runtime environment.

## 12. Folder Structure

```text
books_pipeline/
├── __init__.py
├── items.py
├── middlewares.py
├── pipelines.py
├── settings.py
└── spiders/
    ├── __init__.py
    └── books.py

output/
scrapy.cfg
setup.py
requirements.txt
Dockerfile
.dockerignore
.gitignore
scrapyd.conf
README.md
```

The `output/` directory is generated at runtime and may be excluded from version control.

## 13. Design Decisions

- **Dynamic discovery:** Categories and their URLs are extracted from the website rather than hardcoded.
- **Random sampling:** Random category and book selection meets the assignment's sampling requirements.
- **Pagination handling:** The spider traverses category pages to collect book URLs before sampling.
- **Separation of concerns:** Scraping, cleaning, storage, configuration, and deployment are handled in separate modules.
- **Data normalization:** Text is cleaned, prices are converted to numeric values, and availability is represented as a Boolean.
- **Duplicate prevention:** Duplicate product URLs are rejected by the pipeline.
- **Multiple exports:** JSON, CSV, and XML support different data-consumption needs.
- **Containerization:** Docker provides a consistent environment for running Scrapyd.
- **Deployment:** Scrapyd's HTTP API allows spiders to be scheduled without manually running a local crawl command.

## 14. Known Limitations

- The website is intended for scraping practice; its structure may change.
- Random selection means different runs may produce different datasets.
- If a category contains fewer than five unique books, selecting five unique books from it may not be possible.
- The pipeline currently clears existing database records at the start of each crawl.
- Output and database persistence in Docker depends on the configured paths and whether persistent storage is mounted.
- Scrapyd API access is not secured by this basic configuration; avoid exposing it publicly without appropriate access controls.
- The project is designed for a small practice dataset and may require additional configuration for large-scale scraping.

---

## License

This project is intended for educational and practice purposes.