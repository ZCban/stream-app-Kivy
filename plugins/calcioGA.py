import requests
from bs4 import BeautifulSoup
from estrai_link_m3u8_da_url import estrai_link_m3u8_da_url,get_headers_for_ffmpeg


BASE_URL = "https://calcio.codes/streaming-gratis-calcio-1.php"

def get_name():
    return "Calcio Codes"

def get_categories():
    # Singola categoria generica
    return {"Eventi in diretta": BASE_URL}

def get_series_list(category_url=None, page=1):
    """
    Torna la lista degli eventi sportivi live come fossero 'serie'.
    """
    events = []
    try:
        response = requests.get(BASE_URL, headers={"User-Agent": "Mozilla/5.0"})
        doc = BeautifulSoup(response.content, 'html.parser')
        event_elements = doc.select("ul.kode_ticket_list > li")

        for element in event_elements:
            name = " VS ".join([h2.text.strip() for h2 in element.select("div.ticket_title > h2")])
            time = element.select_one("div.kode_ticket_text > p").text.strip()
            link = element.select_one("div.ticket_btn > a")['href']

            events.append({
                "title": f"{name} - {time}",
                "url": link,
                "poster": "https://i.imgur.com/svLxgqC.png"  # immagine generica per eventi sportivi
            })
    except Exception as e:
        print(f"[Error get_series_list] {e}")

    return events

def get_episodes(event_url):
    """
    Ogni evento ha solo un 'episodio' cioè il link allo stream.
    """
    return [{"label": "Guarda Live", "link": event_url}]

#no need brosware from kodi
def resolve_stream_url(supervideo_url):
    risultati = estrai_link_m3u8_da_url(supervideo_url)

    if not risultati:
        print("❌ Nessun link .m3u8 trovato.")
        return None

    stream = risultati[0]  # puoi aggiungere selezione se più link
    url = stream['url']
    referer = stream['referer']
    headers = get_headers_for_ffmpeg(url, referer)

    print("\n✅ Link .m3u8 trovato:")
    print(f"- {url}")
    print(f"  ↳ Referer: {referer}")
    print(f"  ↳ Headers: {headers}\n")

    SOURCE_URL = url
    proxied_headers = headers

    return SOURCE_URL,proxied_headers




