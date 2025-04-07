import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin,urlparse
import re
import html
from servers import supervideo

BASE_URL = "https://filmsenzalimiti.food"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_name():
    return "FilmSenzaLimiti"

def get_categories():
    return {
        "Azione": f"{BASE_URL}/azione/",
        "Animazione": f"{BASE_URL}/animazione/",
        "Avventura": f"{BASE_URL}/avventura/",
        "Biografico": f"{BASE_URL}/biografico/",
        "Commedia": f"{BASE_URL}/commedia/",
        "Crime": f"{BASE_URL}/crime/",
        "Documentario": f"{BASE_URL}/documentario/",
        "Drammatico": f"{BASE_URL}/drammatico/",
        "Erotico": f"{BASE_URL}/erotico/",
        "Famiglia": f"{BASE_URL}/famiglia/",
        "Fantascienza": f"{BASE_URL}/fantascienza/",
        "Fantasy": f"{BASE_URL}/fantasy/",
        "Giallo": f"{BASE_URL}/giallo/",
        "Guerra": f"{BASE_URL}/guerra/",
        "Horror": f"{BASE_URL}/horror/",
        "Musical": f"{BASE_URL}/musical/",
        "Poliziesco": f"{BASE_URL}/poliziesco/",
        "Romantico": f"{BASE_URL}/romantico/",
        "Storico": f"{BASE_URL}/storico-streaming/",
        "Spionaggio": f"{BASE_URL}/spionaggio/",
        "Sportivo": f"{BASE_URL}/sportivo/",
        "Thriller": f"{BASE_URL}/thriller/",
        "Western": f"{BASE_URL}/western/",
        "Cinema": f"{BASE_URL}/cinema/"
    }

def get_series_list(category_url, page):
    if not category_url.endswith("/"):
        category_url += "/"
    url = f"{category_url}page/{page}/"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    for a_tag in soup.select("a[href*='/guarda/']"):
        div_tag = a_tag.find("div", style=True)
        title_div = a_tag.select_one("div.title")
        hd_div = a_tag.select_one("div.hd")
        vote_div = a_tag.select_one("div.episode")
        se_num = a_tag.select_one("span.se_num")

        if not (div_tag and title_div):
            continue

        # Copertina da background-image
        style = div_tag.get("style", "")
        match = re.search(r"url\((.*?)\)", style)
        img_url = urljoin(BASE_URL, match.group(1)) if match else None

        # Dati
        title = title_div.get_text(strip=True)
        quality = hd_div.get_text(strip=True) if hd_div else ""
        vote = vote_div.get_text(strip=True) if vote_div else ""
        episode = se_num.get_text(strip=True) if se_num else ""

        # Titolo con info extra
        info = title
        if episode:
            info += f" - {episode}"
        if quality:
            info += f" [{quality}]"
        if vote:
            info += f" ⭐ {vote}"

        href = urljoin(BASE_URL, a_tag["href"])

        results.append({
            "title": info,
            "poster": img_url,
            "url": href
        })

    return results


def get_episodes1(series_url):
    episodes = []

    res = requests.get(series_url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    script_tag = soup.find("script", src=re.compile(r"guardahd\.stream/ddl/tt\d+"))
    if not script_tag:
        return []

    script_url = script_tag["src"]
    if script_url.startswith("//"):
        script_url = "https:" + script_url
    elif script_url.startswith("/"):
        script_url = "https://guardahd.stream" + script_url

    js_res = requests.get(script_url, headers=HEADERS)
    if not js_res.ok:
        return []

    js_lines = js_res.text.splitlines()
    html_parts = []

    for line in js_lines:
        if line.strip().startswith("document.write("):
            content = re.sub(r"^document\.write\(\s*[\"']", "", line.strip())
            content = re.sub(r"[\"']\s*\);\s*$", "", content)
            html_parts.append(content)

    full_html = html.unescape("".join(html_parts).replace("\\'", "'"))
    soup = BeautifulSoup(full_html, "html.parser")
    rows = soup.select("table#download-table tr[onclick]")

    for row in rows:
        onclick = row.get("onclick", "")
        match = re.search(r"window\.open\(\s*'([^']+)'", onclick)
        if not match:
            continue

        link = match.group(1)
        if "mostraguarda.stream" in link:
            continue

        # Host name from domain
        parsed = urlparse(link)
        host = parsed.netloc.replace("www.", "").split(".")[0].capitalize()

        # Extra details
        tds = row.select("td.hide-on-mobile")
        resolution = tds[1].get_text(strip=True) if len(tds) >= 2 else ""
        peso = tds[3].get_text(strip=True) if len(tds) >= 4 else ""
        audio = tds[4].get_text(strip=True) if len(tds) >= 5 else ""

        # Costruisci label solo se ci sono info utili
        info_parts = []
        if resolution:
            info_parts.append(resolution)
        if audio:
            info_parts.append(audio)
        if peso:
            info_parts.append(peso)

        label = f"{host} [{' - '.join(info_parts)}]" if info_parts else host

        episodes.append({"label": label, "link": link})

    return episodes

import html
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_episodes(series_url):
    episodes = []

    res = requests.get(series_url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    # Controlla se è una serie TV con struttura HTML classica
    series_tabs = soup.select("div.tab-pane.fade")
    if series_tabs:
        for season in series_tabs:
            season_id = season.get("id", "")
            season_num = season_id.replace("season-", "").strip()

            for li in season.select("li"):
                ep_anchor = li.select_one("a[data-num]")
                mirrors = li.select("div.mirrors2 a.mr")

                if not ep_anchor or not mirrors:
                    continue

                ep_num = ep_anchor.get("data-num", "").strip()
                ep_title = ep_anchor.get("data-title", "").strip()

                for mirror in mirrors:
                    link = mirror.get("data-link", "").strip()
                    if not link or "mostraguarda" in link:
                        continue

                    host = mirror.get_text(strip=True)
                    label = f"{host} [{ep_num} - {ep_title}]"
                    episodes.append({
                        "label": label,
                        "link": link
                    })

        return episodes  # Ritorna subito se è serie

    # Altrimenti prova con struttura film via script JS
    script_tag = soup.find("script", src=re.compile(r"guardahd\.stream/ddl/tt\d+"))
    if not script_tag:
        return []

    script_url = script_tag["src"]
    if script_url.startswith("//"):
        script_url = "https:" + script_url
    elif script_url.startswith("/"):
        script_url = "https://guardahd.stream" + script_url

    js_res = requests.get(script_url, headers=HEADERS)
    if not js_res.ok:
        return []

    js_lines = js_res.text.splitlines()
    html_parts = []

    for line in js_lines:
        if line.strip().startswith("document.write("):
            content = re.sub(r"^document\.write\(\s*[\"']", "", line.strip())
            content = re.sub(r"[\"']\s*\);\s*$", "", content)
            html_parts.append(content)

    full_html = html.unescape("".join(html_parts).replace("\\'", "'"))
    soup = BeautifulSoup(full_html, "html.parser")
    rows = soup.select("table#download-table tr[onclick]")

    for row in rows:
        onclick = row.get("onclick", "")
        match = re.search(r"window\.open\(\s*'([^']+)'", onclick)
        if not match:
            continue

        link = match.group(1)
        if "mostraguarda.stream" in link:
            continue

        parsed = urlparse(link)
        host = parsed.netloc.replace("www.", "").split(".")[0].capitalize()

        tds = row.select("td.hide-on-mobile")
        resolution = tds[1].get_text(strip=True) if len(tds) >= 2 else ""
        peso = tds[3].get_text(strip=True) if len(tds) >= 4 else ""
        audio = tds[4].get_text(strip=True) if len(tds) >= 5 else ""

        info_parts = []
        if resolution:
            info_parts.append(resolution)
        if audio:
            info_parts.append(audio)
        if peso:
            info_parts.append(peso)

        label = f"{host} [{' - '.join(info_parts)}]" if info_parts else host
        episodes.append({"label": label, "link": link})

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

# Test (puoi rimuoverlo se lo usi da plugin)
if __name__ == "__main__":
    test_url = "https://filmsenzalimiti.food/guarda/29289-the-monkey-streaming-hd.html"
    episodes = get_episodes(test_url)

    print("🎬 Link trovati per:", test_url)
    for ep in episodes:
        print(f"- {ep['label']} → {ep['link']}")

