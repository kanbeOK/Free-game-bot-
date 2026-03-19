import requests
import os

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DB_FILE = "sent_games.txt"

def get_epic_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=VN&allowCountries=VN"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        free_now = []
        for game in elements:
            price = game.get('price', {}).get('totalPrice', {})
            # CHỈ LẤY: Game trả phí (original > 0) đang giảm về 0
            if price.get('originalPrice', 0) > 0 and price.get('discountPrice') == 0:
                title = game['title']
                slug = game.get('catalogMappings', [{}])[0].get('pageSlug') or game.get('productSlug') or game.get('urlSlug')
                link = f"https://store.epicgames.com/en-US/p/{slug}"
                free_now.append({"id": f"epic-{game['id']}", "title": title, "link": link, "source": "Epic Games"})
        return free_now
    except: return []

def get_steam_free_games():
    search_url = "https://store.steampowered.com/search/results/?maxprice=free&specials=1&json=1"
    try:
        response = requests.get(search_url).json()
        free_now = []
        if response.get('items'):
            for item in response['items']:
                if "discount_block" in item.get('html', ''): 
                    free_now.append({"id": f"steam-{item['id']}", "title": item['name'], "link": f"https://store.steampowered.com/app/{item['id']}", "source": "Steam"})
        return free_now
    except: return []

def send_to_discord(game):
    payload = {
        "content": "@everyone 🎁 PHÁT HIỆN GAME MIỄN PHÍ!",
        "embeds": [{
            "title": game['title'],
            "url": game['link'],
            "color": 3447003,
            "description": f"Nền tảng: **{game['source']}**\nHãy nhận ngay để sở hữu vĩnh viễn!",
            "footer": {"text": "Bot Check 15 Phút/Lần"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    if not WEBHOOK_URL: exit()
    sent_games = set()
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            sent_games = set(line.strip() for line in f)

    all_free = get_epic_free_games() + get_steam_free_games()
    new_ids = []
    for game in all_free:
        if game['id'] not in sent_games:
            send_to_discord(game)
            new_ids.append(game['id'])

    if new_ids:
        with open(DB_FILE, "a") as f:
            for g_id in new_ids:
                f.write(f"{g_id}\n")
