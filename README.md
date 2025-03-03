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

### Running the Crawler
There are two crawlers available in this project:
1. **Top Movies List Crawler**: This crawler scrapes data from the list of top movies on kinobox.cz.
* To run the Top Movies List Crawler, use the following command:
```bash
python crawler.py start kinobox
```

2. **Sitemap Crawler**: This crawler scrapes data from the sitemaps on kinobox.cz.
* To run the Sitemap Crawler, use the following command:
```bash
python crawler.py start kinobox_sitemap
```

### Stopping the Crawler
Because the crawler uses `scrapy_playwright` stoping it with `Ctrl+C` may not always work. To stop the crawler, use the following command:
```bash
python crawler.py stop
```
Then wait for the crawler to stop.

This uses telnet connectiong to the running crawler and stops it gracefully.
Telnet is configured this way:
```python
TELNETCONSOLE_PORT = [6025]
TELNETCONSOLE_USERNAME = "scrapy"
TELNETCONSOLE_PASSWORD = "1111"
```

If the command does not work for you (e.g. different operating system I used MacOS),
you can use telnet directly:
```bash
telnet localhost 6025
```
After you are connected, you can stop the crawler by typing:
```bash
Username: scrapy
Password: 1111
>>>engine.stop()
```

## Project Structure

```
crawls/
├── kinobox_jobdir/
└── kinobox_sitemap_jobdir/
kinobox_crawler/
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
├── README.md
├── movies.json
├── requirements.txt
└── scrapy.cfg
```

## Dependencies
**Important**: It is suggested to use virtual environment to run the crawler.

**Used python version**: `3.13.2`

Make sure to install the required dependencies before running the crawler. You can install the dependencies using the following command:
```bash
pip install -r requirements.txt
```
