import requests, json, time, threading, random, os, aiohttp, httpx, asyncio
from urllib3.exceptions import InsecureRequestWarning
from discord import Webhook, Embed, Colour

settings = json.load(open("settings.json", "r"))
webhook = settings[0]["webhook"]
cookietouse = settings[0]["cookie"]
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def getuser():
    with requests.session() as s:
        s.cookies['.ROBLOSECURITY'] = cookietouse
        conn = s.get("https://users.roblox.com/v1/users/authenticated")

    if conn.status_code == 200:
        return conn.json()["name"]
    else:
        return "Account Unknown"

def webhook_info(item_id):
    api = requests.get(f'https://economy.roblox.com/v2/assets/{item_id}/details').json()
    img_api = requests.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={item_id}&size=420x420&format=Png').json()
    info = {
        "purchaser": getuser(),
        "name": api["Name"],
        "price": api["PriceInRobux"],
        "creator": api["Creator"]["Name"],
        "img": img_api["data"][0]["imageUrl"],
        "itemUrl": f"https://www.roblox.com/catalog/{item_id}",
    }

    return info


session = requests.session()
session.cookies['.ROBLOSECURITY'] = settings[0]["cookie"]

token = None
payload = [{ "itemType": "Asset", "id": id } for id in settings[1]["items"]]
cache = []

logs = []
checks = 0

def refresh_tokens():
    while True:
        _set_auth()
        time.sleep(150)

def _set_auth():
    global token, session
    try:
        conn = session.post("https://auth.roblox.com/v2/logout")
        if conn.headers.get("x-csrf-token"):
            token = conn.headers["x-csrf-token"]
    except:
        time.sleep(5)
        return _set_auth()
    
def get_product_id(id):
    try:
        conn = session.get(f"https://economy.roblox.com/v2/assets/{id}/details", verify=False)
        data = conn.json()

        if conn.status_code == 200:
            return  {
                "id": data["ProductId"],
                "creator": data["Creator"]["Id"]
            }
        else:
            time.sleep(1)
            return get_product_id(id)
    except:
        time.sleep(1)
        return get_product_id(id)

def buy_item(product_id, seller_id, price, actual_item_id):
    global logs

    try:

        authorized = settings[0]["authorized"]
        ping_string = ""
        for x in authorized:
            ping_string = ping_string + f"<@{x}>"
        info = webhook_info(int(actual_item_id))
        name = info["name"]
        purchaser = info["purchaser"]
        price = info["price"]
        creator = info["creator"]
        img = info["img"]
        itemUrl = info["itemUrl"]
        authorized = settings[0]["authorized"]
        body = {
            "expectedCurrency": 1,
            "expectedPrice": price,
            "expectedSellerId": seller_id
        }
        headers = {
            "x-csrf-token": token,
        }
        conn = session.post(f"https://economy.roblox.com/v1/purchases/products/{product_id}", headers=headers, json=body)
        data = conn.json()
        if conn.status_code == 200:
            if ("purchased" in data) and data["purchased"] == True:
                logs.append(f"Bought {data['assetName']}")
                webhook_data = {
                    "content": ping_string,
                    "embeds": [
                                {
                                    "title": f"{purchaser} bought {name}",
                                    "description": f"Price: `{price}`\nCreator: `{creator}`",
                                    "url": itemUrl,
                                    "color": 16234703,
                                    "thumbnail": {
                                        "url": img
                                    },
                                    "footer": {
                                                "text": "frames personals sniper",
                                                "icon_url": "https://cdn.discordapp.com/attachments/1152278211317731448/1152305921872109648/vlqrp6dkh88nlptlbs43o7nfgg-39571d408b0354614327b0eee935167f.png"
                                            }
                                    }
                                ]
                            }
                with requests.session() as s:
                    s.post(webhook, json=webhook_data)

        else:
            return buy_item(product_id, seller_id, price, actual_item_id)
    except:
        return buy_item(product_id, seller_id, price, actual_item_id)

def status_update():
    global checks, logs

    while True:
        print("made by frames, discord.gg/mewt")
        print(f"Checks: {checks}")
        print(f"Logs: \n" + "\n".join(log for log in logs[-10:]))

        time.sleep(1)
        os.system('cls' if os.name == 'nt' else 'clear')

def watcher():
    global token, session, checks, logs
    while True:
        try:
            headers = {
                "x-csrf-token": token,
                "cache-control": "no-cache",
                "pragma": "no-cache",
            }
            conn = session.post("https://catalog.roblox.com/v1/catalog/items/details", json={ "items": payload }, headers=headers, verify=False)

            data = conn.json()
            if conn.status_code == 200:
                checks+= 1
                if "data" in data:
                    for item in data["data"]:
                        if "price" in item and not item["id"] in cache and not item["price"] > settings[1]["items"][str(item["id"])]:
                            cache.append(item["id"])
                            r_data = get_product_id(item["id"])
                            logs.append("Buying item")
                            buy_item(r_data["id"], r_data["creator"], item["price"], item["id"])
            elif conn.status_code == 403:
                logs.append('force refreshing auth token')
                _set_auth()
            else:
                logs.append(f"{data}, status: {conn.status_code}")
        except Exception as error:
            logs.append(str(error))
            pass
        time.sleep(settings[0]["watch_speed"])


if __name__ == '__main__':
    threading.Thread(target=refresh_tokens,).start()
    print("Waiting to fetch token, restart if it takes too long")
    while token == None:
        time.sleep(1)
    print("Fetched token")
    threading.Thread(target=status_update,).start()
    threading.Thread(target=watcher,).start()
