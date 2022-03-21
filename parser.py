import os
import sys
import pathlib
import argparse
import bs4.element
import urllib.request
from concurrent import futures

from typing import Optional
from bs4 import BeautifulSoup
from urllib.error import URLError, HTTPError


def run_scraper(threads: int, articles: int, out_dir: pathlib.Path) -> None:
    prepared_articles = prepare_articles(articles)
    with futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(
            lambda x: download_pictures_from_article_to_dir(x, out_dir),
            prepared_articles)


def prepare_articles(articles_count: int):
    res = []
    current_page = 1
    while len(res) < articles_count:
        page_val = BeautifulSoup(
            load_content(f"https://habr.com/ru/all/page{current_page}/"))
        res += list(page_val.find_all("article"))
        current_page += 1
    return res[:articles_count]


def download_pictures_from_article_to_dir(
        article: bs4.element.Tag, out_dir: pathlib.Path):
    article_name = extract_article_name(article)
    picture_urls = [x for x in get_picture_urls(article)]
    path = out_dir.joinpath(article_name)
    if len(picture_urls) > 0:
        try:
            os.makedirs(path)
        except FileExistsError:
            pass
        file_counter = 1
        for picture_url in picture_urls:
            urllib.request.urlretrieve(
                picture_url,
                path.joinpath(
                    str(file_counter) + take_file_type(str(picture_url))))
            file_counter += 1


def get_picture_urls(article: bs4.element.Tag):
    template = f"https://habr.com/ru/post/{article['id']}/"
    article = BeautifulSoup(load_content(template)).find_all("article")
    inner_images = BeautifulSoup(str(article[0])).find_all("img")
    for img in inner_images:
        if "data-src" in img.attrs.keys():
            yield img["data-src"]


def take_file_type(name):
    return os.path.splitext(name)[1]


def extract_article_name(article: bs4.element.Tag):
    return article.find_all("h2")[0].text


def load_content(url: str) -> Optional[bytes]:
    try:
        return urllib.request.urlopen(url, timeout=10).read()
    except (HTTPError, URLError):
        return None


def main():
    script_name = os.path.basename(sys.argv[0])
    parser = argparse.ArgumentParser(
        usage=f'{script_name} [ARTICLES_NUMBER] THREAD_NUMBER OUT_DIRECTORY',
        description='Habr parser',
    )
    parser.add_argument(
        '-n', type=int, default=25, help='Number of articles to be processed',
    )
    parser.add_argument(
        'threads', type=int, help='Number of threads to be run',
    )
    parser.add_argument(
        'out_dir', type=pathlib.Path, help='Directory to download habr images',
    )
    args = parser.parse_args()

    run_scraper(args.threads, args.n, args.out_dir)


if __name__ == '__main__':
    main()
