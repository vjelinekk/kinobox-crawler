import scrapy
import logging


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
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logging.getLogger("playwright").setLevel(logging.WARNING)

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
        for film in response.xpath('//main//li//div[@class = "FilmRankingItemExtended_metaRowWrapper__r3NGx"]'):
            overview_url = film.xpath(".//a[@data-context='title']/@href").get()

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
        director = roles[0]
        screenwriter = roles[1]
        music = roles[2]

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

        comments_url = response.xpath('//ul[@role = "list"]/li[4]/a/@href').get()
        if comments_url:
            yield response.follow(
                comments_url,
                meta={
                    "movie_data": movie_data,
                },
                callback=self.parse_comments
            )
        else:
            yield movie_data

    def parse_comments(self, response: scrapy.http.Response):
        movie_data = response.meta["movie_data"]
        comments = []

        for comment in response.xpath('//article[@class = "UserRatingItem_container__HudHI"]'):
            user = comment.xpath('normalize-space(.//header/div/a)').get()
            published = comment.xpath('normalize-space(.//header//time)').get()
            rating = comment.xpath('normalize-space(.//header/div[@class = "UserRatingItem_score__kgilY"])').get()
            text = comment.xpath('normalize-space(.//div[@class = "ShowMore_container__P4vGZ ShowMore_withoutOverlay__Pv_ox UserRatingItem_ratingContent__i_LV0"])').get()
            likes = comment.xpath('normalize-space(.//footer//div)').get()

            comments.append({
                "user": user,
                "published": published,
                "rating": f"{int(float(rating) * 10)}%",
                "text": text,
                "likes": likes
            })

        movie_data["comments"] = comments

        # next_page_url = response.xpath('//div[@class = "Pagination_container__PMgYg"]//a[@class = "Button_container__qRdIS Button_text__AlFCd Button_iconOnly__sFsND"]')
        # if next_page_url:
        #     yield response.follow(
        #         next_page_url.xpath('@href').get(),
        #         meta={
        #             "movie_data": movie_data,
        #             "playwright": True,
        #         },
        #         callback=self.parse_comments
        #     )
        # else:
        #     yield movie_data
