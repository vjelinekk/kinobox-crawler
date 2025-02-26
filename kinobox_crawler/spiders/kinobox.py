import scrapy
import playwright
from scrapy_playwright.page import PageMethod


def should_abort_request(req):
    if req.resource_type == 'image':
        return True

    return False


class KinoboxSpider(scrapy.Spider):
    name = "kinobox"

    start_urls = [
        "https://www.kinobox.cz/zebricky/nejlepsi/filmy"
    ]

    custom_settings = {
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "DOWNLOAD_HANDLERS": {
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        # "PLAYWRIGHT_LAUNCH_OPTIONS": {
        #     "headless": False,
        # },
        "LOG_LEVEL": "ERROR",
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'RETRY_TIMES': 5,  # Retry up to 5 times
        'RETRY_HTTP_CODES': [429],  # Retry on 429 status code
        'PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT': 100000,
        'PLAYWRIGHT_ABORT_REQUEST': should_abort_request,
    }

    movie_comments_map = {}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True
                },
                callback=self.parse
            )

    def parse(self, response: scrapy.http.Response):
        for movie in response.xpath('//main//li//div[@class = "FilmRankingItemExtended_metaRowWrapper__r3NGx"]'):
            overview_url = movie.xpath(".//a[@data-context='title']/@href").get()

            if overview_url:
                yield response.follow(
                    overview_url,
                    callback=self.parse_overview
                )

    def parse_overview(self, response: scrapy.http.Response):
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

        movie_data = {
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

        comments_url = response.xpath('//ul[@role="list"]/li//i[@title="Komentáře"]/../../../@href').get()
        if comments_url:
            comments_url = response.urljoin(comments_url)
            yield scrapy.Request(
                comments_url,
                meta={
                    "movie_data": movie_data,
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", '.Pagination_container__PMgYg', state='attached'),
                    ]
                },
                callback=self.parse_comments
            )
        else:
            yield movie_data

    async def parse_comments(self, response: scrapy.http.Response):
        page: playwright.async_api.Page = response.meta["playwright_page"]
        # link_container = await page.query_selector('.Pagination_container__PMgYg')
        # await link_container.wait_for_element_state('stable')
        # print(f"[PAGE] {link_container}")

        movie_data = response.meta["movie_data"]
        movie_title = movie_data["title"]

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

        # movie_data["comments"] = comments
        # yield movie_data

        next_page_url = response.xpath('//div[@class = "Pagination_container__PMgYg"]//a[not(@disabled)]//i[@class = "Icon_container__te_GQ Icon_chevron-down__pX_uW Pagination_nextIcon__H_WMv"]/../../@href').get()

        if next_page_url:
            print(f"[NEXT PAGE {movie_title}] Going to next page: {next_page_url}")
            yield scrapy.Request(
                next_page_url,
                meta={
                    "movie_data": movie_data,
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", '.Pagination_container__PMgYg', state='attached'),
                    ]
                },
                callback=self.parse_comments
            )
        else:
            print(f"[FINISHED {movie_title}] Got all comments for movie, comments count: {len(self.movie_comments_map[movie_title])}")
            # show whats stored in paginator
            print(f"[FINISHED {movie_title}] Value in paginator element: {response.xpath('//div[@class = "Pagination_container__PMgYg"]//a[not(@disabled)]//i[@class = "Icon_container__te_GQ Icon_chevron-down__pX_uW Pagination_nextIcon__H_WMv"]').get()}")
            final_data = movie_data.copy()
            final_data["comments"] = self.movie_comments_map[movie_title]
            yield final_data

        await page.close()
