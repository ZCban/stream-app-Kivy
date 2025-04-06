import requests
from bs4 import BeautifulSoup
import re
import json

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-mobile": "?0",
}

def estrai_m3u8(text):
    return re.findall(r'https?://[^\s\'"]+\.m3u8', text)

def estrai_fetch_calls(text):
    pattern = r'fetch\s*\(\s*(?P<url>"https?://[^"]+"|{[^}]+})'
    matches = re.finditer(pattern, text)
    fetch_calls = []

    for match in matches:
        part = match.group("url")
        if part.startswith("{"):
            try:
                obj_text = part.replace("'", '"')
                obj_text = re.sub(r'(\w+):', r'"\1":', obj_text)
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

def estrai_link_m3u8_da_url(url):
    risultati = []

    try:
        print(f"\n🔍 Richiedo: {url}")
        response = requests.get(url, headers=BASE_HEADERS, timeout=10)
        html = response.text

        soup = BeautifulSoup(html, 'html.parser')
        text_to_search = soup.prettify()

        # === M3U8 nell'HTML
        for link in estrai_m3u8(text_to_search):
            risultati.append({
                "url": link,
                "referer": url,
                "headers": BASE_HEADERS.copy() | {"Referer": url}
            })

        # === Analizza fetch()
        fetch_calls = estrai_fetch_calls(text_to_search)
        print(f"\n📦 Chiamate fetch trovate: {len(fetch_calls)}")

        for call in fetch_calls:
            print(f"→ {call['method']} {call['url']}")
            try:
                call_headers = BASE_HEADERS.copy()
                call_headers["Referer"] = url

                if call["method"] == "POST":
                    call_headers["Content-Type"] = "application/json"
                    data = call["body"] if call["body"] else "{}"
                    res = requests.post(call["url"], headers=call_headers, data=data, timeout=10)
                else:
                    res = requests.get(call["url"], headers=call_headers, timeout=10)

                content_type = res.headers.get("Content-Type", "")
                text = res.text

                if "application/json" in content_type:
                    try:
                        json_data = res.json()
                        text = json.dumps(json_data)
                    except Exception:
                        pass

                for m3u8 in estrai_m3u8(text):
                    risultati.append({
                        "url": m3u8,
                        "referer": call["url"],
                        "headers": call_headers.copy()
                    })

            except Exception as e:
                print(f"⚠️ Errore {call['method']} {call['url']}: {e}")

        # === Deduplica per (url, referer)
        unici = {(r["url"], r["referer"]): r for r in risultati}
        finali = list(unici.values())

        if finali:
            print(f"\n✅ Trovati {len(finali)} link .m3u8 validi.")
        else:
            print("\n❌ Nessun link .m3u8 trovato.")

        return finali

    except Exception as e:
        print(f"[❌] Errore generale: {e}")
        return []
