from scrapy.http.response import Response
from scrapy import Request
from scrapy.spiders import SitemapSpider
from playwright.async_api import Page
from kinobox_crawler.helpers.helpers import should_abort_request


class KinoboxSitemapSpider(SitemapSpider):
    """
    Kinobox crawler that crawls through the sitemap and scrapes the movie details and comments.
    """

    name = "kinobox_sitemap"

    sitemap_urls = [
        "https://www.kinobox.cz/sitemap.xml"
    ]

    sitemap_rules = [
        ("/film/", "parse_overview"),
    ]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "LOG_LEVEL": "INFO",
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'RETRY_TIMES': 5,  # Retry up to 5 times
        'RETRY_HTTP_CODES': [429],  # Retry on 429 status code
        'PLAYWRIGHT_ABORT_REQUEST': should_abort_request,
        'JOBDIR': 'crawls/kinobox_sitemap_jobdir',
        'TELNETCONSOLE_USERNAME': "scrapy",
        'TELNETCONSOLE_PASSWORD': "1111",
        'TELNETCONSOLE_PORT': [6025]
    }

    movie_comments_map = {}

    def parse_overview(self, response: Response) -> None:
        """
        Parse the movie details and follow the link to the comments.

        Args:
            response (Response): The response from the movie details.

        Returns:
            None
        """
        movie_data = self.extract_movie_data(response)
        self.logger.info(f"[STARTED {movie_data['title']} url: {response.url}] Started scraping movie details")
        comments_url = response.xpath('//ul[@role="list"]/li//i[@title="Komentáře"]/../../../@href').get()

        if comments_url:
            comments_url = response.urljoin(comments_url)
            yield Request(
                comments_url,
                meta={
                    "movie_data": movie_data,
                    "playwright": True,
                    "playwright_include_page": True,
                    "page_num": 1,
                    "url": comments_url
                },
                callback=self.parse_comments
            )
        else:
            yield movie_data

    def extract_movie_data(self, response: Response) -> dict:
        """
        Extract the movie data from the response.

        Args:
            response (Response): The response from the movie details.

        Returns:
            dict: The movie data.
        """
        title = response.xpath('normalize-space(//h1)').get()
        title_eng = response.xpath('normalize-space(//div[@class = "FilmLayout_metadata__7nnz4"]/h2)').get()

        year = response.xpath('normalize-space(//div[@class = "FilmLayout_metadata__7nnz4"]//p[@class = "FilmLayout_yearLabel__MYmp_"])').get()

        duration = response.xpath('normalize-space(//div[@class = "FilmLayout_metadata__7nnz4"]//span[2])').get()

        rating = response.xpath('normalize-space(//aside//div[@class = "Score_container__eAKcX Score_positive__IHjEw Score_staticBadge__a4po7 FilmLayout_score__2JrHf"]/div)').get()

        description = response.xpath('normalize-space(//main/div[@class = "ShowMore_container__P4vGZ FilmPageOverviewContainer_summary__DJLug"])').get()

        actors_sel = response.xpath('//section/div/div/a[@class="CastItem_container__hzzP4"]//h4')
        main_actors = [actor.xpath('normalize-space(.)').get() for actor in actors_sel if actor.xpath('normalize-space(.)').get()]

        roles = [
            role.xpath("normalize-space(.)").get()
            for role in response.xpath('//section//div[@class="FilmPageOverviewContainer_castInfo__aPQjG"]//a')
            if role.xpath("normalize-space(.)").get()
        ]
        director = roles[0] if len(roles) > 0 else None
        screenwriter = roles[1] if len(roles) > 1 else None
        music = roles[2] if len(roles) > 2 else None

        return {
            "title": title,
            "title_eng": title_eng,
            "year": year,
            "duration": duration,
            "rating": rating,
            "description": description,
            "main_actors": main_actors,
            "director": director,
            "screenwriter": screenwriter,
            "music": music
        }

    async def parse_comments(self, response: Response) -> None:
        """
        Parse the comments for the movie.

        Args:
            response (Response): The response from the comments page.

        Returns:
            None
        """
        page: Page = response.meta["playwright_page"]
        current_page = response.meta.get("page_num", 1)

        movie_data = response.meta["movie_data"]
        movie_title = movie_data["title"]

        try:
            await page.wait_for_selector('.Pagination_container__PMgYg a:not([disabled]) i.Pagination_nextIcon__H_WMv', state="visible")
            await page.wait_for_selector('.UserRatingItem_container__HudHI', state="visible")

            self.extract_comments(response, movie_title)

            next_page_url = await page.evaluate('document.querySelector(".Pagination_container__PMgYg a:not([disabled]) i.Pagination_nextIcon__H_WMv").closest("a").href')

            if next_page_url:
                yield Request(
                    next_page_url,
                    meta={
                        "movie_data": movie_data,
                        "playwright": True,
                        "playwright_include_page": True,
                        "page_num": current_page + 1,
                        "url": next_page_url
                    },
                    callback=self.parse_comments
                )
            else:
                yield self.finalize_movie_data(movie_data, movie_title)
        except Exception:
            # it is still possible that there are some comments but no next page button
            self.extract_comments(response, movie_title)
            yield self.finalize_movie_data(movie_data, movie_title)

        await page.close()

    def finalize_movie_data(self, movie_data: dict, movie_title: str) -> dict:
        """
        Add the comments to the movie data.

        Args:
            movie_data (dict): The movie data.
            movie_title (str): The title of the movie.

        Returns:
            dict: The movie data with comments.
        """
        self.logger.info(f"[FINISHED {movie_title}] Got all comments for movie, comments count: {len(self.movie_comments_map[movie_title])}")
        movie_data["comments"] = self.movie_comments_map[movie_title]

        return movie_data

    def extract_comments(self, response: Response, movie_title: str) -> None:
        """
        Read the comments from the response.

        Args:
            response (Response): The response from the comments page.
            movie_title (str): The title of the movie.

        Returns:
            None
        """
        if movie_title not in self.movie_comments_map:
            self.movie_comments_map[movie_title] = []

        comments = []

        for comment in response.xpath('//article[@class = "UserRatingItem_container__HudHI"]'):
            user = comment.xpath('normalize-space(.//header/div/a)').get()
            published = comment.xpath('normalize-space(.//header//time)').get()
            rating = comment.xpath('normalize-space(.//header/div[@class = "UserRatingItem_score__kgilY"])').get()
            text = comment.xpath('normalize-space(.//div[@class = "ShowMore_container__P4vGZ ShowMore_withoutOverlay__Pv_ox UserRatingItem_ratingContent__i_LV0"])').get()
            likes = comment.xpath('normalize-space(.//footer//div)').get()

            rating_string = f"{int(float(rating) * 10)}%" if rating else "N/A"

            comments.append({
                "user": user,
                "published": published,
                "rating": rating_string,
                "text": text,
                "likes": likes
            })

        self.movie_comments_map[movie_title].extend(comments)
