import pip 
try:
    import discord, json, aiohttp, httpx, asyncio, os, time, subprocess, sys, requests, psutil, signal, platform
    from discord.ext import commands
    from discord import Embed, Colour, Game
    from robloxapi import Client
    from io import BytesIO 
    from typing import Union 
    from discord import Webhook 
    from urllib.parse import urlparse
except ModuleNotFoundError:
    os.system('pip install requests psutil discord.py robloxapi aiohttp')
    os.execv(sys.executable, [sys.executable] + [sys.argv[0]] + sys.argv[1:])

scriptVersion = 0
def whichPythonCommand():
    LocalMachineOS = platform.system()
    if (
        LocalMachineOS == "win32"
        or LocalMachineOS == "win64"
        or LocalMachineOS == "Windows"
        or LocalMachineOS == "Android"
    ):
        return "python"

if whichPythonCommand() == "python":
    os.system("cls")

def get_thumbnail(item_id) -> str:
    res = requests.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={item_id}&size=420x420&format=Png').json()
    return res['data'][0]['imageUrl']

def get_itemname(item_id) -> str:
    res = requests.get(f'https://economy.roblox.com/v2/assets/{item_id}/details').json()
    return res['Name']


users_api = "https://users.roblox.com/v1/usernames/users"

def getUserId(username):
    request = {
        "usernames": [
            username
        ],
        "excludeBannedUsers": True
    }
    responseData = requests.post(users_api, json=request)
    assert responseData.status_code == 200
    userId = responseData.json()["data"][0]["id"]
    return userId

#Load Settings
with open('settings.json') as f:
    settings = json.load(f)

print("Personals Sniper Extension is now running.")

#Variables
ROBLOX_API_URL = "https://users.roblox.com/v1/users/authenticated"
webhook_color = discord.Color.from_rgb(255, 182, 193)
webhook_url = settings[0]["webhook"]
autorestart_notify_enabled = True
intents = discord.Intents.default()
intents.message_content = True    
intents.messages = True
autorestart_task = None
autorestart_minutes = None
notify_on_restart = False
start_time = None
print_cache = {}
discord_ids = settings[0]["authorized"][0]
discord_id = discord_ids

#Class
class MyBot(commands.AutoShardedBot):
    async def on_socket_response(self, msg):
        self._last_socket_response = time.time()

    async def close(self):
        if self._task:
            self._task.cancel()
        await super().close()

    async def on_ready(self):
        if not hasattr(self, "_task"):
            self._task = self.loop.create_task(self.check_socket())

    async def check_socket(self):
        while not self.is_closed():
            if time.time() - self._last_socket_response > 60:
                await self.close()
                await self.start(bot_token)
            await asyncio.sleep(5)


bot = MyBot(command_prefix="!", intents=intents)
bot._last_socket_response = time.time()

#Functions
def bot_login(token, ready_event):
    intents = discord.Intents.default()
    intents.message_content = True  
    bot = commands.Bot(command_prefix="!",
                       intents=intents)

def is_owner(): 
    async def predicate(ctx):
        settings = read_settings()
        authorized_ids = [int(x) for x in settings[0]["authorized"]]
        return ctx.author.id in authorized_ids
    return commands.check(predicate)

def read_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)
    
def testIfVariableExists(tablee, variablee):
    if tablee is dict:
        list = tablee.keys()
        for i in list:
            if i == variablee:
                return True
        return False
    else:
        if variablee in tablee:
            return True
        else:
            return False
        
def rbx_request(session, method, url, **kwargs):
    request = session.request(method, url, **kwargs)
    method = method.lower()
    if (method == "post") or (method == "put") or (method == "patch") or (method == "delete"):
        if "X-CSRF-TOKEN" in request.headers:
            session.headers["X-CSRF-TOKEN"] = request.headers["X-CSRF-TOKEN"]
            if request.status_code == 403:  # Request failed, send it again
                request = session.request(method, url, **kwargs)
    return request
    
def restart_main_py():
    global runningSession
    if runningSession:
        for proc in psutil.process_iter():
            name = proc.name()
            if name == "python.exe":
                cmdline = proc.cmdline()
                if "main.py" in cmdline[1]:
                    pid = proc.pid
                    os.kill(pid, signal.SIGTERM)
        runningSession = subprocess.Popen([sys.executable, "main.py"])
    else:
        print("Personals Process was not found! Using old restarter!")
        for proc in psutil.process_iter():
            name = proc.name()
            if name == "python.exe":
                cmdline = proc.cmdline()
                if "main.py" in cmdline[1]:
                    pid = proc.pid
                    os.kill(pid, signal.SIGTERM)
        runningSession = subprocess.Popen([sys.executable, "main.py"])

async def restart_bot(ctx):
    try:
        restart_main_py()
    except Exception as e:
        pass


async def check_cookie(cookie):
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        return True, username
    else:
        return False, None

def overwrite(new_settings):
    with open('settings.json', 'w') as file:
        json.dump(new_settings, file, indent=4)

async def get_user_id_from_cookie(cookie):
    api_url = "https://www.roblox.com/mobileapi/userinfo"
    headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data["UserID"]
    else:
        return None



#Events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        # embed = Embed(title="Error", description=" ```Only the owner can use such commands. ```", color=Colour.red())
        # await ctx.send(embed=embed)
        return


@bot.event
async def on_ready():
    global start_time
    start_time = time.time()
    os.system("cls" if os.name == "nt" else "clear")

    print("Personals Sniper Extension is now running in the background!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="timed items!"))
    print(f"Logged in as bot: {bot.user.name}")

bot.remove_command("help")

#Commands:
#help command
@bot.command()
@is_owner()
async def help(ctx):
    msg = """# COMMANDS LIST

**ITEMS**
!add / !a {item_id} {max_price} --- Add an item to watcher
!add_link / !al {item_link} {max_price} --- Add an item using its link to watcher

!remove / !r {item_id} --- Remove an item from watcher
!remove_link/ !rl {item_link} {max_price} --- Remove an item using its link from watcher

!focus / !f {item_id} {max_price} --- Removes all items and focuses on the specified item
!focus_link / !link_focus / !fl --- Removes all items and focuses on the specified item using its link

!maxprice / !mp {item_id} {new_max_price} --- Change an item's max price

**BOT CONFIG**
!token {bot_token} --- Change the bot token [idk if this works tbh lmao]
!cookie {cookie} --- Change the ROBLOX cookie [idk if this also works lmfaoaoaoa]
!speed {new_watch_speed} --- Change the watch speed to your desired value   

!adduser / !au {user_id} --- Authorize a person to use your bot
!removeuser / !ru {user_id} --- Remove an authorized person from using your bot
!authorized --- Returns a list of all authorized users

**OTHERS**
!watching / !w --- Returns a list of all the items you are currently watching.
!info / !si --- Returns info about the prefix, current ROBLOX account being used, the watch speed, items being watched, and runtime."""
    await ctx.author.send(msg)
    await ctx.reply(embed=Embed(title="A list of commands has been sent to your DMs!",description=None,color=webhook_color))

#webhook command
@bot.command() 
@is_owner()
async def webhook(ctx, webhook_url: str):
    settings = read_settings()
    settings[0]["webhook"] = webhook_url
    overwrite(settings)
    embed = discord.Embed(
        title="Success!",
        description=" ``` This webhook has been succesfully set and will be used for the next notifications! ```",
        color=webhook_color
    )
    embed_dict = embed.to_dict()
    async with aiohttp.ClientSession() as session:
        async with session.post(
            webhook_url,
            json={
                "embeds": [embed_dict],
                "username": bot.user.name,
                "avatar_url": str(bot.user.avatar.url) if bot.user.avatar else None,
            },
        ) as response:
            if response.status != 204:
                await ctx.send(f"Failed to send the embed to the webhook. HTTP status: {response.status}")
                return
            
            if await restart_main_py():
               print("Succesfully restarted mewt after updating the webhook")
            else:
               print("Error while trying to restart mewt after updating the webhook.")

#ping
@bot.command()
async def ping(ctx):
    message = f"Pong! {round(bot.latency * 1000)}ms"
    await ctx.send(message)

#speed command
@bot.command(name='speed')  
@is_owner()
async def speed(ctx, new_speed: str):
    try:
        new_speed_float = float(new_speed)
    except ValueError:
        embed = Embed(title='The watch speed must be a number.', color=Colour.from_rgb(255, 0, 0))
        await ctx.send(embed=embed)
        return

    
    settings = read_settings()
    
    if new_speed_float.is_integer():
        new_speed_value = int(new_speed_float)
    else:
        new_speed_value = new_speed_float

   
    settings[0]["watch_speed"] = new_speed_value

    
    overwrite(settings)

    await ctx.send(embed=discord.Embed(title=f"Watch speed changed to {str(new_speed_value)}.",description=None, color=webhook_color))

    if await restart_main_py():
            print("Updated speed and restarted successfully!")
    else:
            print("Error while trying to restart after updating the speed")

# view all watching items
@bot.command(name="watching")
@is_owner()
async def watching(ctx):
    settings = read_settings()
    watchlist = settings[1]["items"]
    speed = settings[0]["watch_speed"]

    try:
        cookieToUse = settings[0]["cookie"]
        dataToUse = {
            "items": [] 
        }

        for item in watchlist:
            dataToUse["items"].append(
                {"itemType": 1,"id": item}
            )

        session = requests.Session()
        session.cookies[".ROBLOSECURITY"] = cookieToUse
        session.headers["accept"] = "application/json"
        session.headers["Content-Type"] = "application/json"

        request = rbx_request(session=session, method="POST", url="https://catalog.roblox.com/v1/catalog/items/details", data=json.dumps(dataToUse))
        item = request.json()
        listOfEmbeds = []

        if request.status_code == 200 and item.get("data"):
            for item_data in item["data"]:
               print(item["data"])
               if testIfVariableExists(item_data, "price"):
                    embedToAdd =  discord.Embed(
                        title=f'Watching: {item_data["name"]}',
                        url=f"https://www.roblox.com/catalog/{str(item_data['id'])}/",
                        color=webhook_color,
                        description=f"Creator: `{item_data['creatorName']}`\nMax Price:`{str(watchlist[str(item_data['id'])])}` \nPrice: `{str(item_data['price'])}` \nID: `{str(item_data['id'])}`"
                    )
                    embedToAdd.add_field(name=f'Watcher speed:',value=f'`{speed}`')
                    embedToAdd.set_thumbnail(url=get_thumbnail(str(item_data['id'])))
                    listOfEmbeds.append(embedToAdd)
               else:
                    embedToAdd =  discord.Embed(
                        title=f'Watching: {item_data["name"]}',
                        url=f"https://www.roblox.com/catalog/{str(item_data['id'])}/",
                        color=webhook_color,
                        description=f"Creator: `{item_data['creatorName']}`\nMax Price:`{str(watchlist[str(item_data['id'])])}`  \nPrice: `Not for sale` \nID: `{str(item_data['id'])}`"
                    )
                    embedToAdd.add_field(name=f'Watcher speed:',value=f'`{speed}`')
                    embedToAdd.set_thumbnail(url=get_thumbnail(str(item_data['id'])))
                    listOfEmbeds.append(embedToAdd)

            if len(listOfEmbeds) == 0:
                listOfEmbeds.append(discord.Embed(
                    title="Error!",
                    description="No items are currently being watched!",
                    color=webhook_color,
                ))
            await ctx.send(embeds=listOfEmbeds)
        else:
            await ctx.send("Failed to get list and error has been received: " + item["errors"][0]["message"])
    except Exception as e:
        embed = Embed(
            title=f"An error occurred while trying to fetch your watch list: {str(e)}. This is most likely due to there being no items in the list or due to a wrongly input item.",
            desciption=None,
            color=Colour.red(),
        )
        await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="w")
@is_owner()
async def w(ctx):
    ctx.command = bot.get_command("watching")
    await bot.invoke(ctx)

#add owner
@bot.command()
@is_owner()
async def adduser(ctx, user_id: int):
    settings = read_settings()
    
    authorized_ids = settings[0]["authorized"]
    
    if str(user_id) not in authorized_ids:
        authorized_ids.append(str(user_id))
        settings[0]["authorized"] = authorized_ids
        
        overwrite(settings)
        
        await ctx.send(embed=discord.Embed(title="User added!",description=f"<@{user_id}> ({user_id}) can now use your bot!",color=webhook_color))
    else:
        await ctx.send(embed=discord.Embed(title="User input already authorized!",description=f"<@{user_id}> ({user_id}) is already an authorized user!", color=webhook_color))

# same as above omegalul
@bot.command(name="au")
@is_owner()
async def au(ctx):
    ctx.command = bot.get_command("adduser")
    await bot.invoke(ctx)

#remove owner
@bot.command()
@is_owner()
async def removeuser(ctx, user_id: int):
    settings = read_settings()
        
    authorized_ids = settings[0]["authorized"]
    
    if str(user_id) in authorized_ids:

        authorized_ids.remove(str(user_id))
        settings[0]["authorized"] = authorized_ids
        overwrite(settings)

        embed = discord.Embed(title="User removed!",description=f"<@{user_id}> ({user_id}) can no longer use your bot!",color=webhook_color)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="User input unauthorized!",description=f"<@{user_id}> ({user_id}) is not an authorized user!",color=webhook_color)
        await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="ru")
@is_owner()
async def ru(ctx):
    ctx.command = bot.get_command("removeuser")
    await bot.invoke(ctx)

#owners
@bot.command()
@is_owner()
async def authorized(ctx):
    settings = read_settings()
    authorized_ids = settings[0]["authorized"]

    owners_str = ""
    for ownerid in authorized_ids:
        owners_str = owners_str + f"<@{ownerid}>  ({ownerid})\n"
    
    embed = discord.Embed(title="Authorized Users",description=owners_str,color=webhook_color)

    await ctx.send(embed=embed)

#restart command
@bot.command()
@is_owner()
async def restart(ctx):
    try:
        restart_main_py()
        embed = Embed(title="Success!", description="Successfully restarted the bot.", color=Colour.from_rgb(255, 182, 193))
        await ctx.send(embed=embed)
    except Exception as e:
        embed = Embed(title="Error", description="An error occurred while trying to restart the bot: {}".format(str(e)), color=Colour.red())
        await ctx.send(embed=embed)

#More command
@bot.command(pass_context = True)
@is_owner()
async def info(ctx):
    settings = read_settings()

    
    main_cookie = settings[0]["cookie"]
    watch_speed = settings[0]["watch_speed"]
    # owners = settings[0]["authorized"]
    prefix = bot.command_prefix
    items = settings[1]["items"]
    watching = ', '.join(str(item) for item in items)

    main_cookie_valid, main_username = await check_cookie(main_cookie)

    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={main_cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_data = avatar_response.json()
        thumbnail_url = avatar_data["data"][0]["imageUrl"]

    if start_time is not None:
        runtime = int(time.time() - start_time)
        minutes, seconds = divmod(runtime, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        runtime = f"{days} days, {hours} hours, {minutes} minutes and {seconds} seconds"
    else:
        runtime = "Unknown"


    embed = discord.Embed(title=f"hi {ctx.message.author.name}!!!! (Prefix: {prefix})", color=webhook_color)
    # embed.add_field(name="Current owner ID(s):", value=owners,inline=True)
    embed.add_field(name="Current account:", value=main_username if main_cookie_valid else "Inactive (Update your cookie!)")
    embed.add_field(name="Watching:", value=watching if watching else "No Items")
    embed.add_field(name="Watch speed:", value=watch_speed)
    embed.add_field(name="Runtime:", value=runtime)
    embed.set_footer(text="hardish's extension for frames' personals sniper lol")
    embed.set_thumbnail(url=thumbnail_url)
    await ctx.reply(embed=embed)

# same as above omegalul
@bot.command(name="i")
@is_owner()
async def i(ctx):
    ctx.command = bot.get_command("info")
    await bot.invoke(ctx)


#cookie command
@bot.command()
@is_owner()
async def cookie(ctx, new_cookie: str):
    
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={new_cookie}"}
        response = await client.get(ROBLOX_API_URL, headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        username = user_data["name"]
        user_id = user_data["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_data = avatar_response.json()
        avatar_url = avatar_data["data"][0]["imageUrl"]

        
        settings = read_settings()

        
        settings[0]["cookie"] = new_cookie

        
        overwrite(settings)
        
        embed = discord.Embed(
            title="Cookie changed!",
            description=f"Registered new cookie as: {username}",
            color=webhook_color
        )

       
        embed.set_thumbnail(url=avatar_url)

        
        await ctx.send(embed=embed)

        
        if await restart_main_py():
            print("Bot restarted after updating the cookie.")
        else:
            print("Error while trying to restart the bot after updating the cookie.")

    else:
        
        embed = discord.Embed(
            title="Error",
            description=" ```The cookie you have input was invalid. ```",
            color=discord.Color.red()
        )

        
        await ctx.send(embed=embed)

#token command
@bot.command()  
@is_owner()
async def token(ctx, new_token: str):
    
    settings = read_settings()

    
    settings[0]["token"] = new_token

    
    overwrite(settings)

    embed = discord.Embed(
        title="Token Update",
        description="Successfully changed discord bot token!",
        color=webhook_color
    )

    await ctx.send(embed=embed)

    if await restart_main_py():
            print("Bot restarted after updating the token.")
    else:
            print("Error while trying to restart the bot after updating the token.")

# legacy watcher watch
@bot.command()
@is_owner()
async def focus(ctx, id: int, mp:int):
    print("Focusing on new item...")
    settings = read_settings()

    settings[1]["items"] = {str(id): mp}

    overwrite(settings)

    restart_main_py()

    await ctx.send(embed=discord.Embed(title=f"Now focusing on {get_itemname(id)} ({id}) with a max price of {mp}",description=None,color=webhook_color))

# same as above omegalul
@bot.command(name="f")
@is_owner()
async def f(ctx):
    ctx.command = bot.get_command("focus")
    await bot.invoke(ctx)

# legacy watcher watch (but with link :O)
@bot.command()
@is_owner()
async def focus_link(ctx, link: str, mp: int):
    att1 = urlparse(link).path.split('/')[-2] 
    att2 = urlparse(link).path.split('/')[-3] 
    att3 = urlparse(link).path.split('/')[2]
    id_from_link = None 
    embed_title = None
    embed_description = None

    if att1.isdigit():
        id_from_link = att1
    elif att2.isdigit():
        id_from_link = att2
    elif att3.isdigit():
        id_from_link = att3
    
    if id_from_link.isdigit():
        print("Adding new item...")

        settings = read_settings()
        
        settings[1]["items"] = {str(id_from_link): mp}

        overwrite(settings)

        restart_main_py()  

        embed_title= f"Now focusing on {get_itemname(id_from_link)} ({id_from_link}) with a max price of {mp}"
        embed_description= None
    elif id_from_link == None or not id_from_link.isdigit():
        embed_description= None
        embed_title= f"Link format is invalid. / Value entered is not a link."
        

    embed = discord.Embed(title=embed_title, description=embed_description, color=webhook_color)   

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="link_focus")
@is_owner()
async def link_focus(ctx):
    ctx.command = bot.get_command("focus_link")
    await bot.invoke(ctx)

# same as above omegalul
@bot.command(name="fl")
@is_owner()
async def fl(ctx):
    ctx.command = bot.get_command("focus_link")
    await bot.invoke(ctx)

# ladd item
@bot.command()
@is_owner()
async def add(ctx, id: str, mp: int):
    settings = read_settings()

    items = settings[1]["items"]
    
    if id.isdigit() and id != None:
        if id in items:
            await ctx.send(embed=discord.Embed(title=f"{get_itemname(int(id))} ({id}) is already being watched!",description=None,color=webhook_color))
        else:           
            print("Adding new item...")
            items[id] = mp   

            embed_title=f"{get_itemname(id)} ({id}) of max price {(mp)} has been added."
            await ctx.send (embed=discord.Embed(title=embed_title, description=None, color=webhook_color))  

        overwrite(settings)

        if await restart_main_py():
            print("Bot restarted after updating watcher")
        else:
            print("Error while trying to restart the bot after updating watcher") 
    else:
        embed_description=None
        embed_title=f"Provided item ID is not an integer"
        await ctx.send (embed=discord.Embed(title=embed_title, description=embed_description, color=webhook_color)) 

# same as above omegalul
@bot.command(name="a")
@is_owner()
async def a(ctx):
    ctx.command = bot.get_command("add")
    await bot.invoke(ctx)

#add link
@bot.command()
@is_owner()
async def add_link(ctx, link: str, mp: int):
    att1 = urlparse(link).path.split('/')[-2] 
    att2 = urlparse(link).path.split('/')[-3] 
    att3 = urlparse(link).path.split('/')[2]
    id_from_link = None 
    settings = read_settings()
    items = settings[1]["items"]

    if att1.isdigit():
        id_from_link = att1
    elif att2.isdigit():
        id_from_link = att2
    elif att3.isdigit():
        id_from_link = att3
    
    if id_from_link.isdigit() and id_from_link != None:
        if id_from_link in items or int(id_from_link) in items:
            await ctx.send(embed=discord.Embed(title=f"Item ID {id_from_link} is already being watched.",description=None,color=webhook_color))
        else:           
            print("Adding legacy id")        
            items[str(id_from_link)] = mp       
            embed_title=f"{get_itemname(int(id_from_link))} ({id_from_link}) of max price {(mp)} has been added."
            await ctx.send (embed=discord.Embed(title=embed_title, description=None, color=webhook_color))  
        
        overwrite(settings)

        if await restart_main_py():
            print("Bot restarted after updating watcher")
        else:
            print("Error while trying to restart the bot after updating watcher") 
    else:
        embed_description= None
        embed_title= f"Link format is invalid. / Value entered is not a link."
        await ctx.send (embed=discord.Embed(title=embed_title, description=embed_description, color=webhook_color)) 

# same as above omegalul
@bot.command(name="al")
@is_owner()
async def al(ctx):
    ctx.command = bot.get_command("add_link")
    await bot.invoke(ctx)

@bot.command()
@is_owner()
async def maxprice(ctx, id: int, price: int):
    settings = read_settings()

    items = settings[1]["items"]
    if str(id) in items:
        items[str(id)] = price
        overwrite(settings)
        embed_title = f"{get_itemname(int(id))} ({id})'s maximum price has been changed to {price}."
    else:
        embed_title = "The provided item is not being watched!"

    embed = discord.Embed(title=embed_title,description=None,color=webhook_color)
    restart_main_py()

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="mp")
@is_owner()
async def mp(ctx):
    ctx.command = bot.get_command("maxprice")
    await bot.invoke(ctx)

@bot.command()
@is_owner()
async def remove(ctx, id: int):
    settings = read_settings()

    items = settings[1]["items"]
    if str(id) in items:
        items.pop(str(id))
        overwrite(settings)
        embed_title = f"{get_itemname(int(id))} ({id}) has been removed."
    else:
        embed_title = "The provided item is not being watched!"

    embed = discord.Embed(title=embed_title,description=None,color=webhook_color)
    restart_main_py()

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="r")
@is_owner()
async def r(ctx):
    ctx.command = bot.get_command("remove")
    await bot.invoke(ctx)

#add link
@bot.command()
@is_owner()
async def remove_link(ctx, link: str):
    att1 = urlparse(link).path.split('/')[-2] 
    att2 = urlparse(link).path.split('/')[-3] 
    att3 = urlparse(link).path.split('/')[2]
    id_from_link = None 
    settings = read_settings()
    items = settings[1]["items"]

    if att1.isdigit():
        id_from_link = att1
    elif att2.isdigit():
        id_from_link = att2
    elif att3.isdigit():
        id_from_link = att3
    
    if id_from_link.isdigit() and id_from_link != None:
        if id_from_link in items or int(id_from_link) in items:
            print("Adding new ID...")        
            items.pop(str(id_from_link))       
            embed_title=f"{get_itemname(int(id_from_link))} ({id_from_link}) has been removed."
            await ctx.send (embed=discord.Embed(title=embed_title, description=None, color=webhook_color))  

            overwrite(settings)

            if await restart_main_py():
                print("Bot restarted after updating watcher")
            else:
                print("Error while trying to restart the bot after updating watcher") 
        else:           
            await ctx.send(embed=discord.Embed(title=f"Item ID {id_from_link} is not being watched!",description=None,color=webhook_color))
    else:
        embed_description= None
        embed_title= f"Link format is invalid. / Value entered is not a link."
        await ctx.send (embed=discord.Embed(title=embed_title, description=embed_description, color=webhook_color)) 

# same as above omegalul
@bot.command(name="rl")
@is_owner()
async def rl(ctx):
    ctx.command = bot.get_command("remove_link")
    await bot.invoke(ctx)
    
runningSession = subprocess.Popen([sys.executable, "main.py"])
bot_token = settings[0]["token"]
bot.run(bot_token)
