import requests
from bs4 import BeautifulSoup
from estrai_link_m3u8_da_url import estrai_link_m3u8_da_url#, get_headers_for_ffmpeg

BASE_URL = "https://sportzone.lat/"

def get_name():
    return "SportZone"

def get_categories():
    return {"Eventi in diretta": BASE_URL}

def get_series_list(category_url=None, page=1):
    """
    Torna la lista degli eventi sportivi live.
    """
    events = []
    try:
        response = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print("❌ Errore nel caricamento: HTTP", response.status_code)
            return events

        doc = BeautifulSoup(response.content, 'html.parser')
        event_elements = doc.select(".list-group-item")

        for element in event_elements:
            try:
                link = element.parent['href']
                teams = element.select_one(".cat_item").text.strip()
                time = element.select_one(".da").text.strip()

                events.append({
                    "title": f"{teams} - {time}",
                    "url": link,
                    "poster": "https://i.imgur.com/svLxgqC.png"
                })
            except Exception as e:
                print(f"[⚠️ Evento saltato] {e}")
    except Exception as e:
        print(f"[Error get_series_list - SportZone] {e}")

    return events

def get_episodes(event_url):
    """
    Ogni evento ha un solo link 'Guarda Live'.
    """
    print(event_url)
    return [{"label": "Guarda Live", "link": event_url}]

def resolve_stream_url1(supervideo_url):
    risultati = estrai_link_m3u8_da_url(supervideo_url)

    if not risultati:
        print("❌ Nessun link .m3u8 trovato per SportZone.")
        return None

    stream = risultati[0]
    url = stream['url']
    referer = stream['referer']
    headers = get_headers_for_ffmpeg(url, referer)


    print("\n✅ Link .m3u8 trovato (SportZone):")
    print(f"- {url}")
    print(f"  ↳ Referer: {referer}")
    print(f"  ↳ Headers: {headers}\n")

    return url, headers

def resolve_stream_url(supervideo_url):
    risultati = estrai_link_m3u8_da_url(supervideo_url)

    if not risultati:
        print(f"❌ Nessun link .m3u8 trovato per {supervideo_url}")
        return None

    stream = risultati[0]
    return stream["url"], stream["headers"]
