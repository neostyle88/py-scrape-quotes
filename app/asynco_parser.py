import asyncio
import csv
from dataclasses import dataclass, fields, astuple

import aiohttp
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com/"
MAX_PAGES = 10  # Set the maximum number of pages to scrape


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()


async def parse_single_quote(quote_soup: BeautifulSoup) -> Quote:
    return Quote(
        text=quote_soup.select_one(".text").text,
        author=quote_soup.select_one(".author").text,
        tags=[tag.text for tag in quote_soup.select("a.tag")],
    )


async def get_single_page_quotes(session, page_num):
    url = f"{BASE_URL}page/{page_num}/"
    page_content = await fetch_page(session, url)
    page_soup = BeautifulSoup(page_content, "html.parser")
    return [
        await parse_single_quote(quote_soup)
        for quote_soup in page_soup.select(".quote")
    ]


async def get_all_quotes():
    async with aiohttp.ClientSession() as session:
        tasks = [
            get_single_page_quotes(session, page_num)
            for page_num in range(1, MAX_PAGES + 1)
        ]
        quotes_per_page = await asyncio.gather(*tasks)
        all_quotes = [quote for quotes in quotes_per_page for quote in quotes]
        return all_quotes


async def main(output_csv_path: str):
    quotes = await get_all_quotes()
    write_quotes_to_csv(quotes, output_csv_path)


def write_quotes_to_csv(quotes: [Quote], csv_file: str) -> None:
    with open(csv_file, "w", encoding="utf-8") as output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow([field.name for field in fields(Quote)])
        writer.writerows([astuple(quote) for quote in quotes])


if __name__ == "__main__":
    asyncio.run(main("quotes.csv"))
