# plugins/altadefinizione.py
#import mock_kodi
from servers import supervideo
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://altadefinizionegratis.space"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_name():
    return "Altadefinizione"

def get_categories():
    return {
        "Serie TV": f"{BASE_URL}/serie-tv/",
        "Film": f"{BASE_URL}/catalog/all/",
        "Netflix": f"{BASE_URL}/netflix-streaming//"
    }

def get_series_list(category_url, page):
    if not category_url.endswith("/"):
        category_url += "/"
    url = f"{category_url}page/{page}/"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    for div in soup.select("div.wrapperImage"):
        a_tag = div.select_one("a[href]")
        img_tag = div.select_one("img")
        title_tag = div.select_one("h2.titleFilm a")

        if not (a_tag and img_tag and title_tag):
            continue

        href = a_tag["href"]
        poster = urljoin(BASE_URL, img_tag["src"])
        title = title_tag.get_text(strip=True)

        results.append({
            "title": title,
            "poster": poster,
            "url": href
        })

    return results

import re

def get_episodes(series_url):
    res = requests.get(series_url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    episodes = []

    # === 1. PROVA A CERCARE EPISODI PER SERIE ===
    season_divs = soup.select("div.tab-pane[id^=season-]")
    for season_div in season_divs:
        season_id = season_div.get("id", "season-1").replace("season-", "")

        for li in season_div.select("ul > li"):
            a_tag = li.find("a", attrs={"data-link": True})
            if not a_tag:
                continue

            ep_num = a_tag.get("data-num", "")
            ep_title = a_tag.get("data-title", "Episodio")
            mirrors = li.select("div.mirrors a.mr")

            for mirror in mirrors:
                server = mirror.get_text(strip=True)
                url = mirror.get("data-link")
                label = f"{ep_num} - {ep_title} [{server}]"
                episodes.append({"label": label, "link": url})

    # === 2. CERCA FILM: player interno con mirror
    if not episodes:
        player_mirrors = soup.select("ul._player-mirrors li[data-link]")
        for li in player_mirrors:
            url = li.get("data-link", "")
            if url.startswith("//"):
                url = "https:" + url
            label = li.get_text(strip=True)
            episodes.append({
                "label": f"{label} [Film]",
                "link": url
            })

    # === 3. Fallback se proprio non trova nulla ===
    #if not episodes:
    #    episodes = [{"label": "Guarda ora", "link": series_url}]

    # Debug
    print("▶️ Episodi trovati:")
    for ep in episodes:
        print(f"- {ep['label']}: {ep['link']}")

    return episodes


    # Debug print
    print("▶️ Episodi trovati:")
    for ep in episodes:
        print(f"- {ep['label']}: {ep['link']}")

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

    #return m3u8_links



#use a brosware to resolve in dinamic mode
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
