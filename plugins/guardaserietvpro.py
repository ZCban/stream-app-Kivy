import os
import time
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
#import mock_kodi
from servers import supervideo

USER_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data")
BRAVE_PATH = r"C:\\Users\\Admin\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

CATEGORIES = {
    "Tutte le Serie TV": "https://guardaserietv.live/serietv-streaming/",
    "Popolari": "https://guardaserietv.live/serietv-popolari/",
    "Netflix": "https://guardaserietv.live/netflix-gratis/",
    "Biografico": "https://guardaserietv.live/biografico/",
    "Commedia": "https://guardaserietv.live/commedia/",
    "Crime": "https://guardaserietv.live/crime/",
    "Documentario": "https://guardaserietv.live/documentario/",
    "Dramma": "https://guardaserietv.live/dramma/",
    "Drammatico": "https://guardaserietv.live/drammatico/",
    "Fantascienza": "https://guardaserietv.live/fantascienza/",
    "Fantastico": "https://guardaserietv.live/fantastico/",
    "Fantasy": "https://guardaserietv.live/fantasy/",
    "Giallo": "https://guardaserietv.live/giallo/",
    "Guerra": "https://guardaserietv.live/guerra/",
    "Horror": "https://guardaserietv.live/horror/",
}

def get_name():
    return "GuardaSerieTV Pro"

def get_categories():
    return CATEGORIES


def get_series_list(category_url, page=1):
    url = f"{category_url.rstrip('/')}/page/{page}/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    posters = soup.select(".mlnh-thumb a")

    series_list = []
    for poster in posters:
        href = poster['href']
        img = poster.find('img')
        title = img.get('alt', 'Sconosciuto')
        src = img.get('src')
        if src.startswith("/"):
            src = f"https://guardaserietv.live{src}"

        series_list.append({
            "title": title,
            "url": href,
            "poster": src
        })

    return series_list


def get_episodes(series_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(series_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    episodes = []
    added = set()

    for season_div in soup.select("div[id^='season']"):
        season_id = season_div.get("id", "")
        season_number = season_id.replace("season-", "")

        for li in season_div.select("ul li"):
            ep_link = li.select_one("a[data-num]")
            if not ep_link:
                continue

            ep_num = ep_link.get("data-num", "x").split("x")[1]
            label = f"Stagione {season_number} Episodio {ep_num}"

            if label in added:
                continue

            a = li.select_one("a[data-link]")
            if a:
                link = a.get("data-link", "")
                if "supervideo.cc" in link:
                    episodes.append({"label": label, "link": link})
                    added.add(label)

    return episodes

#no need brosware from kodi
def resolve_stream_url(supervideo_url):
    exists, msg = supervideo.test_video_exists(supervideo_url)
    if exists:
        links = supervideo.get_video_url(supervideo_url)
        #m3u8_links = [(label, link) for label, link in links if ".m3u8" in link]
        for label, url in links:
            if ".m3u8" in url:
                return url  # ✅ Ritorna solo il primo valido

def resolve_stream_url1(supervideo_url):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            executable_path=BRAVE_PATH,
            headless=True,
            args=["--start-maximized"]
        )
        page = browser.new_page()
        found_url = None

        def handle_request(request):
            nonlocal found_url
            if ".m3u8" in request.url and "master" in request.url and "dropload.io" not in request.url:
                found_url = request.url

        page.on("request", handle_request)
        page.goto(supervideo_url)
        time.sleep(3)
        browser.close()

        return found_url


def search_series(query):
    search_url = "https://guardaserietv.live/"
    params = {
        "story": query,
        "do": "search",
        "subaction": "search"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    res = requests.get(search_url, params=params, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    posters = soup.select(".mlnh-thumb a")

    series_list = []
    for poster in posters:
        href = poster['href']
        img = poster.find('img')
        if not img:
            continue
        title = img.get('alt', 'Sconosciuto')
        src = img.get('src')
        if src.startswith("/"):
            src = f"https://guardaserietv.live{src}"

        series_list.append({
            "title": title,
            "url": href,
            "poster": src
        })

    return series_list

