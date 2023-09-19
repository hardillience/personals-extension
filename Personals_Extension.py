import pip 
try:
    import discord, json, aiohttp, httpx, os, time, subprocess, sys, requests, psutil, signal
    from discord.ext import commands
    from discord import Embed, Colour
    from urllib.parse import urlparse
except ModuleNotFoundError:
    os.system('pip install requests psutil discord.py aiohttp')
    os.execv(sys.executable, [sys.executable] + [sys.argv[0]] + sys.argv[1:])

def get_thumbnail(item_id) -> str:
    return requests.get(f'https://thumbnails.roblox.com/v1/assets?assetIds={item_id}&size=420x420&format=Png').json()['data'][0]['imageUrl']

def get_itemname(item_id) -> str:
    return requests.get(f'https://economy.roblox.com/v2/assets/{item_id}/details').json()['Name']

def getidfromurl(link):
    att1 = urlparse(link).path.split('/')[-2] 
    att2 = urlparse(link).path.split('/')[-3] 
    att3 = urlparse(link).path.split('/')[2]
    val = None

    if att1.isdigit():
        val = att1
    elif att2.isdigit():
        val = att2
    elif att3.isdigit():
        val = att3
    
    return val

#Load Settings
with open('settings.json') as f:
    settings = json.load(f)

def read_settings():
    with open('settings.json', 'r') as f:
        return json.load(f)

webhook_color = discord.Color.from_rgb(255, 182, 193)
webhook_url = settings[0]["webhook"]
start_time = None

# Setting up the bot
bot = commands.Bot(command_prefix="!",intents = discord.Intents.all())

#Events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You are not authorized to use this command!")

def is_authorized(): 
    async def predicate(ctx):
        settings = read_settings()
        return ctx.author.id in [int(x) for x in settings[0]["authorized"]]
    return commands.check(predicate)

def checkvariable(t, var):
    if t is dict:
        list = t.keys()
        for i in list:
            if i == var:
                return True
        return False
    else:
        if var in t:
            return True
        else:
            return False
        
def rbx_request(session, method, url, **kwargs):
    request = session.request(method, url, **kwargs)
    method = method.lower()
    if (method == "post") or (method == "put") or (method == "patch") or (method == "delete"):
        if "X-CSRF-TOKEN" in request.headers:
            session.headers["X-CSRF-TOKEN"] = request.headers["X-CSRF-TOKEN"]
            if request.status_code == 403:
                request = session.request(method, url, **kwargs)
    return request
    
def restart_sniper():
    global runningSession
    if runningSession:
        for proc in psutil.process_iter():
            if proc.name() == "python.exe":
                if "main.py" in proc.cmdline()[1]:
                    os.kill(proc.pid, signal.SIGTERM)
        runningSession = subprocess.Popen([sys.executable, "main.py"])
    else:
        print("Personals Process was not found! Using old restarter!")
        for proc in psutil.process_iter():
            if proc.name() == "python.exe":
                if "main.py" in proc.cmdline()[1]:
                    os.kill(proc.pid, signal.SIGTERM)
        runningSession = subprocess.Popen([sys.executable, "main.py"])

async def check(cookie):
    async with httpx.AsyncClient() as client:
        res = await client.get("https://users.roblox.com/v1/users/authenticated", headers={"Cookie": f".ROBLOSECURITY={cookie}"})

    if res.status_code == 200:
        username = res.json()["name"]
        return True, username
    else:
        return False, None

def overwrite(new_settings):
    with open('settings.json', 'w') as file:
        json.dump(new_settings, file, indent=4)


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
@is_authorized()
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
@is_authorized()
async def webhook(ctx, webhook_url: str):
    settings = read_settings()
    settings[0]["webhook"] = webhook_url
    overwrite(settings)
    embed = discord.Embed(
        title=f"Webhook has been updated successfully!",
        description=None,
        color=webhook_color
    )
    embed_dict = embed.to_dict()
    async with aiohttp.ClientSession() as s:
        async with s.post(
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
            
            if await restart_sniper():
               print("Webhook updated; restarted successfully.")
            else:
               print("Webhook updated; error encountered while restarted.")

#ping
@bot.command()
async def ping(ctx):
    message = f"Pong! {round(bot.latency * 1000)}ms"
    await ctx.send(message)

#speed command
@bot.command(name='speed')  
@is_authorized()
async def speed(ctx, new_speed: str):
    try:
        new_speed_float = float(new_speed)
    except ValueError:
        await ctx.send(embed=Embed(title='The watch speed must be a number.', color=Colour.from_rgb(255, 0, 0)))
        return

    settings = read_settings()
    if new_speed_float.is_integer():
        newest = int(new_speed_float)
    else:
        newest = new_speed_float

    settings[0]["watch_speed"] = newest
    overwrite(settings)
    await ctx.send(embed=discord.Embed(title=f"Watch speed changed to {str(newest)}.",description=None, color=webhook_color))

    if await restart_sniper():
            print("Watch speed updated; restarted successfully.")
    else:
            print("Watch speed updated; restarted successfully.")

# view all watching items
@bot.command(name="watching")
@is_authorized()
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
               if checkvariable(item_data, "price"):
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
@is_authorized()
async def w(ctx):
    ctx.command = bot.get_command("watching")
    await bot.invoke(ctx)

#add owner
@bot.command()
@is_authorized()
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
@is_authorized()
async def au(ctx):
    ctx.command = bot.get_command("adduser")
    await bot.invoke(ctx)

#remove owner
@bot.command()
@is_authorized()
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
@is_authorized()
async def ru(ctx):
    ctx.command = bot.get_command("removeuser")
    await bot.invoke(ctx)

#owners
@bot.command()
@is_authorized()
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
@is_authorized()
async def restart(ctx):
    try:
        restart_sniper()
        embed = Embed(title="Success!", description="Successfully restarted the bot.", color=Colour.from_rgb(255, 182, 193))
        await ctx.send(embed=embed)
    except Exception as e:
        embed = Embed(title="Error", description="An error occurred while trying to restart the bot: {}".format(str(e)), color=Colour.red())
        await ctx.send(embed=embed)

#More command
@bot.command(pass_context = True)
@is_authorized()
async def info(ctx):
    settings = read_settings()

    
    cookie = settings[0]["cookie"]
    watch_speed = settings[0]["watch_speed"]
    # owners = settings[0]["authorized"]
    prefix = bot.command_prefix
    items = settings[1]["items"]
    watching = ', '.join(str(item) for item in items)

    valid, username = await check(cookie)

    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
        res = await client.get("https://users.roblox.com/v1/users/authenticated", headers=headers)

    if res.status_code == 200:
        user_id = res.json()["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        thumbnail_url = avatar_response.json()["data"][0]["imageUrl"]

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
    embed.add_field(name="Current account:", value=username if valid else "Inactive (Update your cookie!)")
    embed.add_field(name="Watching:", value=watching if watching else "No Items")
    embed.add_field(name="Watch speed:", value=watch_speed)
    embed.add_field(name="Runtime:", value=runtime)
    embed.set_footer(text="hardish's extension for frames' personals sniper lol")
    embed.set_thumbnail(url=thumbnail_url)
    await ctx.reply(embed=embed)

# same as above omegalul
@bot.command(name="i")
@is_authorized()
async def i(ctx):
    ctx.command = bot.get_command("info")
    await bot.invoke(ctx)

#cookie command
@bot.command()
@is_authorized()
async def cookie(ctx, new_cookie: str):
    
    async with httpx.AsyncClient() as client:
        headers = {"Cookie": f".ROBLOSECURITY={new_cookie}"}
        res = await client.get("https://users.roblox.com/v1/users/authenticated", headers=headers)

    if res.status_code == 200:
        username = res.json()["name"]
        user_id = res.json()["id"]

        
        avatar_api_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
        async with httpx.AsyncClient() as client:
            avatar_response = await client.get(avatar_api_url)
        avatar_url = avatar_response.json()["data"][0]["imageUrl"]

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

        
        if await restart_sniper():
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
@is_authorized()
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

    if await restart_sniper():
            print("Bot restarted after updating the token.")
    else:
            print("Error while trying to restart the bot after updating the token.")

# legacy watcher watch
@bot.command()
@is_authorized()
async def focus(ctx, id: int, mp:int):
    print("Focusing on new item...")
    settings = read_settings()

    settings[1]["items"] = {str(id): mp}

    overwrite(settings)

    restart_sniper()

    await ctx.send(embed=discord.Embed(title=f"Now focusing on {get_itemname(id)} ({id}) with a max price of {mp}",description=None,color=webhook_color))

# same as above omegalul
@bot.command(name="f")
@is_authorized()
async def f(ctx):
    ctx.command = bot.get_command("focus")
    await bot.invoke(ctx)

# legacy watcher watch (but with link :O)
@bot.command()
@is_authorized()
async def focus_link(ctx, link: str, mp: int):
    id_from_link = getidfromurl(link)
    embed_title = None
    embed_description = None
    
    if id_from_link.isdigit():
        print("Adding new item...")

        settings = read_settings()
        settings[1]["items"] = {str(id_from_link): mp}
        overwrite(settings)
        restart_sniper()  

        embed_title= f"Now focusing on {get_itemname(id_from_link)} ({id_from_link}) with a max price of {mp}"
        embed_description= None
    elif id_from_link == None or not id_from_link.isdigit():
        embed_description= None
        embed_title= f"Link format is invalid. / Value entered is not a link."
        

    embed = discord.Embed(title=embed_title, description=embed_description, color=webhook_color)   

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="link_focus")
@is_authorized()
async def link_focus(ctx):
    ctx.command = bot.get_command("focus_link")
    await bot.invoke(ctx)

# same as above omegalul
@bot.command(name="fl")
@is_authorized()
async def fl(ctx):
    ctx.command = bot.get_command("focus_link")
    await bot.invoke(ctx)

# ladd item
@bot.command()
@is_authorized()
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

        if await restart_sniper():
            print("Bot restarted after updating watcher")
        else:
            print("Error while trying to restart the bot after updating watcher") 
    else:
        embed_description=None
        embed_title=f"Provided item ID is not an integer"
        await ctx.send (embed=discord.Embed(title=embed_title, description=embed_description, color=webhook_color)) 

# same as above omegalul
@bot.command(name="a")
@is_authorized()
async def a(ctx):
    ctx.command = bot.get_command("add")
    await bot.invoke(ctx)

#add link
@bot.command()
@is_authorized()
async def add_link(ctx, link: str, mp: int):
    id_from_link = getidfromurl(link)
    settings = read_settings()
    items = settings[1]["items"]
    
    if id_from_link.isdigit() and id_from_link != None:
        if id_from_link in items or int(id_from_link) in items:
            await ctx.send(embed=discord.Embed(title=f"Item ID {id_from_link} is already being watched.",description=None,color=webhook_color))
        else:           
            print("Adding legacy id")        
            items[str(id_from_link)] = mp       
            embed_title=f"{get_itemname(int(id_from_link))} ({id_from_link}) of max price {(mp)} has been added."
            await ctx.send (embed=discord.Embed(title=embed_title, description=None, color=webhook_color))  
        
        overwrite(settings)

        if await restart_sniper():
            print("Bot restarted after updating watcher")
        else:
            print("Error while trying to restart the bot after updating watcher") 
    else:
        embed_description= None
        embed_title= f"Link format is invalid. / Value entered is not a link."
        await ctx.send (embed=discord.Embed(title=embed_title, description=embed_description, color=webhook_color)) 

# same as above omegalul
@bot.command(name="al")
@is_authorized()
async def al(ctx):
    ctx.command = bot.get_command("add_link")
    await bot.invoke(ctx)

@bot.command()
@is_authorized()
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
    restart_sniper()

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="mp")
@is_authorized()
async def mp(ctx):
    ctx.command = bot.get_command("maxprice")
    await bot.invoke(ctx)

@bot.command()
@is_authorized()
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
    restart_sniper()

    await ctx.send(embed=embed)

# same as above omegalul
@bot.command(name="r")
@is_authorized()
async def r(ctx):
    ctx.command = bot.get_command("remove")
    await bot.invoke(ctx)

#add link
@bot.command()
@is_authorized()
async def remove_link(ctx, link: str):
    id_from_link = getidfromurl(link)
    settings = read_settings()
    items = settings[1]["items"]
    
    if id_from_link.isdigit() and id_from_link != None:
        if id_from_link in items or int(id_from_link) in items:
            print("Adding new ID...")        
            items.pop(str(id_from_link))       
            embed_title=f"{get_itemname(int(id_from_link))} ({id_from_link}) has been removed."
            await ctx.send (embed=discord.Embed(title=embed_title, description=None, color=webhook_color))  

            overwrite(settings)

            if await restart_sniper():
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
@is_authorized()
async def rl(ctx):
    ctx.command = bot.get_command("remove_link")
    await bot.invoke(ctx)

# mslink
@bot.command(pass_context = True)
# @is_owner()
async def mslink(ctx, *, link: str):
    id_from_link = getidfromurl(link)
    
    if id_from_link.isdigit():
        msg=f"""Either link will open Microsoft ROBLOX: 
- https://enchoral.me/?placeid={id_from_link}
- https://www.roblox.com/games/start?launchData=hichat&placeId={id_from_link} (may launch default roblox, set default to uwp if it does)"""
    elif id_from_link == None or not id_from_link.isdigit():
        msg=f"```Link format is invalid. / Value entered is not a link.```"

    await ctx.reply(msg)

# same as above omegalul
@bot.command(name="msl", pass_context = True)
# @is_owner()
async def msl(ctx):
    ctx.command = bot.get_command("mslink")
    await bot.invoke(ctx)

# same as above omegalul
@bot.command(name="ms", pass_context = True)
# @is_owner()
async def ms(ctx):
    ctx.command = bot.get_command("mslink")
    await bot.invoke(ctx)

# same as above omegalul
@bot.command(name="uwp", pass_context = True)
# @is_owner()
async def uwp(ctx):
    ctx.command = bot.get_command("mslink")
    await bot.invoke(ctx)

# id from link
@bot.command(pass_context = True)
# @is_owner()
async def id(ctx, *, link: str):
    id_from_link = getidfromurl(link)
    
    if id_from_link.isdigit():
        msg=str(id_from_link)
    elif id_from_link == None or not id_from_link.isdigit():
        msg=f"```Link format is invalid. / Value entered is not a link.```"

    await ctx.reply(msg)
    
runningSession = subprocess.Popen([sys.executable, "main.py"])
bot_token = settings[0]["token"]
bot.run(bot_token)
