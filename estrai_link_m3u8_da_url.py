import requests
from bs4 import BeautifulSoup
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0"
}

def estrai_fetch_calls(text):
    pattern = r'fetch\s*\(\s*(?P<url>"https?://[^"]+"|{[^}]+})'
    matches = re.finditer(pattern, text)
    fetch_calls = []

    for match in matches:
        part = match.group("url")
        if part.startswith("{"):
            obj_text = part.replace("'", '"')
            obj_text = re.sub(r'(\w+):', r'"\1":', obj_text)
            try:
                obj = json.loads(obj_text)
                url = obj.get("url")
                method = obj.get("method", "GET").upper()
                body = obj.get("body", None)
                if url:
                    fetch_calls.append({"url": url, "method": method, "body": body})
            except Exception:
                continue
        else:
            url = part.strip('"')
            fetch_calls.append({"url": url, "method": "GET", "body": None})

    return fetch_calls

def estrai_m3u8(text):
    return re.findall(r'https?://[^\s\'"]+\.m3u8', text)

def get_headers_for_ffmpeg(url, referer=None):
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    headers = {
        "User-Agent": user_agent,
        "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-mobile": "?0",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }

    if referer:
        headers["Referer"] = referer

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, allow_redirects=True, timeout=5)
        final_headers = response.request.headers
    except Exception as e:
        print("⚠️ Errore nel recupero headers:", e)
        final_headers = headers

    return final_headers

def estrai_link_m3u8_da_url(url):
    risultati = []

    try:
        print(f"Richiedo: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        text_to_search = soup.prettify()

        # Link .m3u8 direttamente trovati nell'HTML della pagina
        m3u8_html = estrai_m3u8(text_to_search)
        for link in m3u8_html:
            risultati.append({"url": link, "referer": url})

        # Estrai chiamate fetch
        fetch_calls = estrai_fetch_calls(text_to_search)

        print(f"\nChiamate fetch trovate ({len(fetch_calls)}):")
        for call in fetch_calls:
            print(f"- {call['method']} {call['url']}")

        for call in fetch_calls:
            try:
                if call["method"] == "POST":
                    post_headers = headers.copy()
                    post_headers["Content-Type"] = "application/json"
                    data = call["body"] if call["body"] else "{}"
                    api_response = requests.post(call["url"], headers=post_headers, data=data, timeout=10)
                else:
                    api_response = requests.get(call["url"], headers=headers, timeout=10)

                content_type = api_response.headers.get("Content-Type", "")

                if "application/json" in content_type:
                    try:
                        json_data = api_response.json()
                        json_text = json.dumps(json_data)
                        found = estrai_m3u8(json_text)
                        for link in found:
                            risultati.append({"url": link, "referer": call["url"]})
                    except Exception as e:
                        print(f"[!] Errore decodifica JSON da {call['url']}: {e}")
                else:
                    found = estrai_m3u8(api_response.text)
                    for link in found:
                        risultati.append({"url": link, "referer": call["url"]})

            except Exception as e:
                print(f"[!] Errore richiesta {call['method']} {call['url']}\n{e}")

        # Rimuovi duplicati (url + referer coppia unica)
        unici = {(r["url"], r["referer"]): r for r in risultati}
        return list(unici.values())

    except Exception as e:
        print(f"[!] Errore generale: {e}")
        return []

# Test standalone
if __name__ == "__main__":
    test_url = "https://calcio.codes/live/everton-vs-arsenal"
    risultati = estrai_link_m3u8_da_url(test_url)

    if risultati:
        print("\nLink .m3u8 trovati:")
        for stream in risultati:
            print(f"- {stream['url']}")
            print(f"  ↳ Referer: {stream['referer']}")
            print(f"  ↳ Headers ffmpeg: {get_headers_for_ffmpeg(stream['url'], referer=stream['referer'])}\n")
    else:
        print("Nessun link .m3u8 trovato.")
