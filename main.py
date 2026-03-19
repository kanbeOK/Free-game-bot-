import requests
import os
import datetime

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DB_FILE = "sent_games.txt"

# Định nghĩa màu sắc Embed
EPIC_COLOR = 3447003  # Xanh dương Epic
STEAM_COLOR = 10181046 # Xanh navy Steam
DEFAULT_COLOR = 15844367 # Vàng (cho lỗi)

# Placeholder logo nền tảng (sử dụng placeholder đáng tin cậy)
EPIC_LOGO_THUMBNAIL = "https://i.imgur.com/vH9Z67A.png" # Placeholder nền tảng
STEAM_LOGO_THUMBNAIL = "https://i.imgur.com/vH9Z67A.png" # Placeholder nền tảng
# Placeholder ảnh game rộng (sử dụng nếu không lấy được ảnh rộng thực tế)
IMAGE_PLACEHOLDER = "https://i.imgur.com/f2597fS.png"

def get_epic_free_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=VN&allowCountries=VN"
    try:
        response = requests.get(url).json()
        elements = response['data']['Catalog']['searchStore']['elements']
        free_now = []
        for game in elements:
            price = game.get('price', {}).get('totalPrice', {})
            # CHỈ LẤY: Game trả phí (originalPrice > 0) đang giảm về 0 (discountPrice == 0)
            original_price = price.get('originalPrice', 0)
            discount_price = price.get('discountPrice', 0)
            
            if original_price > 0 and discount_price == 0:
                title = game['title']
                
                # Sửa link Epic bền bỉ 3 cấp để tránh lỗi 404
                slug = None
                if game.get('catalogMappings'):
                    slug = game['catalogMappings'][0].get('pageSlug')
                if not slug:
                    slug = game.get('productSlug') or game.get('urlSlug')
                if not slug or slug == "home":
                    slug = game.get('id')
                link = f"https://store.epicgames.com/en-US/p/{slug}"
                
                # Launcher link cho Epic
                launcher_link = f"com.epicgames.launcher://store/en-US/p/{slug}"

                # Lấy ảnh game rộng đẹp cho Embed
                image_url = IMAGE_PLACEHOLDER
                if game.get('keyImages'):
                    for img in game['keyImages']:
                        if img['type'] == 'OfferImageWide':
                            image_url = img['url']
                            break
                    if image_url == IMAGE_PLACEHOLDER:
                        # Nếu không có ảnh rộng, lấy ảnh Thumbnail làm Placeholder
                        for img in game['keyImages']:
                            if img['type'] == 'Thumbnail':
                                image_url = img['url']
                                break
                
                free_now.append({
                    "id": f"epic-{game['id']}", 
                    "title": title, 
                    "link": link, 
                    "launcher_link": launcher_link,
                    "source": "Epic Games",
                    "image_url": image_url,
                    "color": EPIC_COLOR,
                    "logo": EPIC_LOGO_THUMBNAIL
                })
        return free_now
    except Exception as e:
        print(f"Lỗi Epic: {e}")
        return []

def get_steam_free_games():
    search_url = "https://store.steampowered.com/search/results/?maxprice=free&specials=1&json=1"
    try:
        response = requests.get(search_url).json()
        free_now = []
        if response.get('items'):
            for item in response['items']:
                if "discount_block" in item.get('html', ''): 
                    game_id = item.get('id')
                    title = item['name']
                    link = f"https://store.steampowered.com/app/{game_id}"
                    
                    # Launcher link cho Steam
                    launcher_link = f"steam://run/{game_id}"

                    # Tạo link ảnh header đẹp cho Steam
                    image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{game_id}/header.jpg"

                    free_now.append({
                        "id": f"steam-{game_id}", 
                        "title": title, 
                        "link": link, 
                        "launcher_link": launcher_link,
                        "source": "Steam",
                        "image_url": image_url,
                        "color": STEAM_COLOR,
                        "logo": STEAM_LOGO_THUMBNAIL
                    })
        return free_now
    except Exception as e:
        print(f"Lỗi Steam: {e}")
        return []

def send_to_discord(game):
    payload = {
        # Đã xóa tag @everyone
        "embeds": [{
            "title": f"🎁 PHÁT HIỆN GAME TRẢ PHÍ MIỄN PHÍ: {game['title']}",
            "description": f"🚀 Đây là game trả phí đang được tặng 100% trên **{game['source']}**. Hãy nhận ngay để sở hữu vĩnh viễn!\n\n📅 Nhanh tay kẻo lỡ!",
            "url": game['link'],
            "color": game['color'],
            "thumbnail": {"url": game['logo']}, # Logo nền tảng nhỏ ở góc Embed
            "image": {"url": game['image_url']}, # Ảnh game lớn ở giữa
            "footer": {
                "text": "Săn Game Tự Động - 15 Phút/Lần",
                "icon_url": game['logo']
            },
            "timestamp": datetime.datetime.utcnow().isoformat()
        }],
        # Nút bấm đẳng cấp (Components)
        "components": [
            {
                "type": 1,
                "components": [
                    {
                        "type": 2,
                        "label": "Mở trong trình duyệt",
                        "style": 5, # Style link nút bấm
                        "url": game['link']
                    },
                    {
                        "type": 2,
                        "label": f"Mở trong {game['source']} Launcher",
                        "style": 5, # Style link nút bấm
                        "url": game['launcher_link']
                    }
                ]
            }
        ]
    }
    requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    if not WEBHOOK_URL:
        print("Thiếu Webhook URL!")
        exit()
    
    # Đọc danh sách game đã gửi
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

    # Lưu lại những game đã gửi
    if new_ids:
        with open(DB_FILE, "a") as f:
            for g_id in new_ids:
                f.write(f"{g_id}\n")
        print(f"Đã gửi {len(new_ids)} game mới.")
    else:
        print("Không có game mới hoặc game đã được gửi trước đó.")
