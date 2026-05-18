import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 Windows NT 10.0; Win64; x64 "
        "AppleWebKit/537.36 KHTML, like Gecko "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9"
}


def fetch_amazon_product(url: str) -> dict:
    """
    Amazon scraping kabhi-kabhi block ho sakti hai.
    Reliable production ke liye Amazon Product Advertising API use karo.
    """
    data = {
        "title": "Amazon Product",
        "price": "",
        "mrp": "",
        "rating": "",
        "discount": "",
        "image": ""
    }

    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "lxml")

        title = soup.select_one("#productTitle")
        if title:
            data["title"] = title.get_text(strip=True)

        price = (
            soup.select_one(".a-price .a-offscreen")
            or soup.select_one("#priceblock_ourprice")
            or soup.select_one("#priceblock_dealprice")
        )
        if price:
            data["price"] = price.get_text(strip=True)

        mrp = soup.select_one(".a-price.a-text-price .a-offscreen")
        if mrp:
            data["mrp"] = mrp.get_text(strip=True)

        rating = soup.select_one("span.a-icon-alt")
        if rating:
            data["rating"] = rating.get_text(strip=True).split(" ")[0]

        image = soup.select_one("#landingImage")
        if image and image.get("src"):
            data["image"] = image["src"]

    except Exception:
        pass

    return data


def fetch_flipkart_product(url: str) -> dict:
    data = {
        "title": "Flipkart Product",
        "price": "",
        "mrp": "",
        "rating": "",
        "discount": "",
        "image": ""
    }

    try:
        res = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(res.text, "lxml")

        title = soup.select_one("span.B_NuCI") or soup.select_one("h1")
        if title:
            data["title"] = title.get_text(strip=True)

        price = soup.select_one("div._30jeq3")
        if price:
            data["price"] = price.get_text(strip=True)

        mrp = soup.select_one("div._3I9_wc")
        if mrp:
            data["mrp"] = mrp.get_text(strip=True)

        rating = soup.select_one("div._3LWZlK")
        if rating:
            data["rating"] = rating.get_text(strip=True)

        img = soup.select_one("img._396cs4")
        if img and img.get("src"):
            data["image"] = img["src"]

    except Exception:
        pass

    return data


def fetch_product(platform: str, url: str) -> dict:
    if platform == "amazon":
        return fetch_amazon_product(url)

    if platform == "flipkart":
        return fetch_flipkart_product(url)

    return {
        "title": "Product",
        "price": "",
        "mrp": "",
        "rating": "",
        "discount": "",
        "image": ""
    }
