import re
import urllib.parse
import requests
from config import AMAZON_TAG, FLIPKART_AFFILIATE_ID

AMAZON_REGEX = r"https?://(?:www\.)?(?:amazon\.in|amzn\.in|amzn\.to)/[^\s]+"
FLIPKART_REGEX = r"https?://(?:www\.)?flipkart\.com/[^\s]+"


def extract_urls(text: str):
    if not text:
        return []

    amazon_urls = re.findall(AMAZON_REGEX, text)
    flipkart_urls = re.findall(FLIPKART_REGEX, text)

    urls = []
    for url in amazon_urls:
        urls.append(("amazon", clean_url(url)))

    for url in flipkart_urls:
        urls.append(("flipkart", clean_url(url)))

    return urls


def clean_url(url: str) -> str:
    return url.strip().rstrip(").,]")


def convert_amazon_link(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(parsed.query))

    if AMAZON_TAG:
        query["tag"] = AMAZON_TAG

    new_query = urllib.parse.urlencode(query)

    clean_path = parsed.path

    new_url = urllib.parse.urlunparse((
        parsed.scheme or "https",
        parsed.netloc,
        clean_path,
        "",
        new_query,
        ""
    ))

    return new_url


def convert_flipkart_link(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(parsed.query))

    if FLIPKART_AFFILIATE_ID:
        query["affid"] = FLIPKART_AFFILIATE_ID

    new_query = urllib.parse.urlencode(query)

    return urllib.parse.urlunparse((
        parsed.scheme or "https",
        parsed.netloc,
        parsed.path,
        "",
        new_query,
        ""
    ))


def shorten_url_tinyurl(long_url: str) -> str:
    """
    Free shortener. Production ke liye Bitly/Cuttly/Rebrandly better hai.
    """
    try:
        api = "[tinyurl.com](https://tinyurl.com/api-create.php)"
        res = requests.get(api, params={"url": long_url}, timeout=10)
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception:
        pass

    return long_url


def convert_link(platform: str, url: str, shorten: bool = True) -> str:
    if platform == "amazon":
        converted = convert_amazon_link(url)
    elif platform == "flipkart":
        converted = convert_flipkart_link(url)
    else:
        converted = url

    if shorten:
        return shorten_url_tinyurl(converted)

    return converted
