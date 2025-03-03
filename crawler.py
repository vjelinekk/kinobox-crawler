from scrapy.crawler import CrawlerProcess
from kinobox_crawler.spiders.kinobox import KinoboxSpider
from kinobox_crawler.spiders.kinobox_sitemap import KinoboxSitemapSpider
import sys
import os
import shutil
import scrapy.utils.reactor
import pexpect


def get_job_dir(spider_name):
    if spider_name == "kinobox":
        return 'crawls/kinobox_jobdir'
    elif spider_name == "kinobox_sitemap":
        return 'crawls/kinobox_sitemap_jobdir'
    else:
        print(f"Unknown spider: {spider_name}")
        print("Available spiders: 'kinobox', 'kinobox_sitemap'")
        return None


def reset_job_dir(job_dir):
    """Reset job directory but preserve hidden files."""
    if not os.path.exists(job_dir):
        os.makedirs(job_dir, exist_ok=True)
        return

    # Get all non-hidden files and directories
    items_to_remove = []
    for item in os.listdir(job_dir):
        if not item.startswith('.'):
            items_to_remove.append(os.path.join(job_dir, item))

    # Remove non-hidden files and directories
    for item in items_to_remove:
        if os.path.isfile(item):
            os.remove(item)
        elif os.path.isdir(item):
            shutil.rmtree(item)

    print(f"Job directory reset: {job_dir} (hidden files preserved)")


def start_crawler(spider_name, reset_state=False):
    """Start the crawler with the specified spider."""
    # Install the required reactor
    scrapy.utils.reactor.install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

    # Select the appropriate spider
    if spider_name == "kinobox":
        spider_class = KinoboxSpider
    elif spider_name == "kinobox_sitemap":
        spider_class = KinoboxSitemapSpider
    else:
        print(f"Unknown spider: {spider_name}")
        print("Available spiders: 'kinobox', 'kinobox_sitemap'")
        return

    job_dir = get_job_dir(spider_name)
    if job_dir is None:
        return

    # Reset job directory if requested
    if reset_state:
        reset_job_dir(job_dir)

    # Create and configure the crawler process
    process = CrawlerProcess()

    # Add the spider to the process
    process.crawl(spider_class)

    # Start the crawler process
    print(f"Starting {spider_name} spider" + (" with fresh state" if reset_state else " resuming previous state"))
    print("Telnet console available at localhost:6025")
    process.start()  # This blocks until the crawling is finished


def stop_crawler():
    # Define the rules (prompts and responses)
    rules = [
        ("Username:", "scrapy"),         # Send username when we see 'Username:'
        ("Password:", "1111"),           # Send password when we see 'Password:'
        (r"\>>>", "engine.stop()"),      # Send stop command when we see the prompt '>>>'
        (r"\>>>", "exit"),               # Exit after the stop command
        (pexpect.EOF, None),             # End of the file (connection closed)
    ]

    # Spawn a new Telnet session to the desired host
    client = pexpect.spawn("telnet localhost 6025")

    # This is so we can see what's happening
    client.logfile = sys.stdout.buffer

    # Iterate over the expected prompts and corresponding responses
    for expect, send in rules:
        client.expect(expect)  # Wait for the expected prompt
        if send is None:
            break  # Exit the loop when there's no further action
        client.sendline(send)  # Send the response


def main():
    # Check if enough arguments are provided
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python crawler.py start <spider_name> [-r]")
        print("  python crawler.py stop")
        print("")
        print("  spider_name: 'kinobox' or 'kinobox_sitemap'")
        print("  -r: Optional flag to reset the resumable state")
        return

    command = sys.argv[1].lower()

    if command == "start":
        # Check if reset flag is present
        reset_state = False
        spider_name = sys.argv[2].lower()
        if len(sys.argv) > 3 and sys.argv[3] == "-r":
            reset_state = True

        start_crawler(spider_name, reset_state)

    elif command == "stop":
        stop_crawler()

    else:
        print(f"Unknown command: {command}")
        print("Available commands: 'start', 'stop'")


if __name__ == "__main__":
    main()
