# Kinobox Crawler

This is a web crawler designed to scrape movie data from [kinobox.cz](https://www.kinobox.cz). The crawler handles both static and dynamic content, ensuring that all relevant movie data is collected in a structured format.

## Features

- **Scrapes data from kinobox.cz**: The crawler gathers movie data from the **Top Movies** list and from **Sitemaps** on kinobox.cz.
- **Handles dynamic content**: The crawler uses `scrapy_playwright` to handle pages rendered by JavaScript, ensuring that even dynamically-loaded data is fetched correctly.
- **Persistent state**: The crawler maintains a persistent state across different runs to avoid duplicate content.
- **Two crawlers**:
  - **Top Movies List Crawler**: Crawls through the list of top movies on kinobox.cz. This crawler is faster and more efficient.
  - **Sitemap Crawler**: Crawls through the sitemap of kinobox.cz. This crawler is slower than the Top Movies List Crawler but captures additional content from the sitemaps.

## Data Format

The movie data is stored in JSON format with each record containing the following fields:
```json
{
    "title": "Název filmu",
    "title_eng": "Movie Title",
    "year": "2024",
    "duration": "1h 42m",
    "rating": "88%",
    "description": "Description", 
    "main_actors": ["List", "of", "main", "actors"], 
    "director": "Director", 
    "screenwriter": "Screenwriter", 
    "music": "Music", 
    "comments": [
        {
            "user": "User Name",
            "published": "30. 11. 2024",
            "rating": "80%",
            "text": "Comment text",
            "likes": "0"
        },
        // more comments...
    ]
}
```

## Usage

There are two crawlers available in this project:
1. **Top Movies List Crawler**: This crawler scrapes data from the list of top movies on kinobox.cz.
* To run the Top Movies List Crawler, use the following command:
```bash
scrapy crawl kinobox -o movies.json
```

2. **Sitemap Crawler**: This crawler scrapes data from the sitemaps on kinobox.cz.
* To run the Sitemap Crawler, use the following command:
```bash
scrapy crawl kinobox_sitemap -o movies_sitemap.json
```

Note: The **Sitemap Crawler** is significantly slower than the **Top Movies List Crawler**

## Project Structure

kinobox_crawler/
├── crawls/
│   ├── kinobox_jobdir/
│   ├── kinobox_sitemap_jobdir/
├── kinobox_crawler/
│   ├── spiders/
│   │   ├── kinobox.py
│   │   ├── kinobox_sitemap.py
│   ├── helpers/
│   │   ├── helpers.py
│   ├── pipelines.py
│   ├── settings.py
│   ├── items.py
│   └─ middlewares.py
├── scrapy.cfg
└── requirements.txt

## Dependencies
**Important**: It is suggested to use virtual environment to run the crawler.

**Used python version**: `3.13.2`

Make sure to install the required dependencies before running the crawler. You can install the dependencies using the following command:
```bash
pip install -r requirements.txt
```
