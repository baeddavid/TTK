import discord
from discord.ext import commands
import pymongo
from pymongo import MongoClient

client = discord.Client()

cluster = MongoClient(mongo_url)
db = cluster["dos"]
collection = db["ttk"]


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # $tk Killer Victim
    # Adds killer/victim to database and initializes them with 1 kill and 1 death
    # If they already exists updates accordingly
    if message.content.startswith("$tk"):
        players = get_players(message.content)
        killer = {"_id": players[1]}
        victim = {"_id": players[2]}

        if collection.count_documents(killer) == 0:
            victims = [players[2]]
            killers = []
            post1 = {
                "_id": players[1],
                "teamKill": 1,
                "killedBy": killers,
                "victims": victims,
                "death": 0
            }
            collection.insert_one(post1)
        else:
            query = {"_id": players[1]}
            user = collection.find(query)
            old_kills = 0
            old_victims = []

            for result in user:
                old_kills = result["teamKill"]
                old_victims = result["victims"]
            updated_kills = old_kills + 1
            old_victims.append(players[2])
            collection.update_one({"_id": players[1]}, {"$set": {"teamKill": updated_kills, "victims": old_victims}})
        if collection.count_documents(victim) == 0:
            killers = [players[1]]
            victims = []
            post2 = {
                "_id": players[2],
                "teamKill": 0,
                "killedBy": killers,
                "victims": victims,
                "death": 1,
            }
            collection.insert_one(post2)
        else:
            query = {"_id": players[2]}
            user = collection.find(query)
            old_deaths = 0
            old_killers = []

            for result in user:
                old_deaths = result["death"]
                old_killers = result["killedBy"]
            updated_deaths = old_deaths + 1
            old_killers.append(players[1])
            collection.update_one({"_id": players[2]}, {"$set": {"killedBy": old_killers, "death": updated_deaths}})
        await message.channel.send('```Team Kill Logged.```')

    # $killCount Victim Killer
    # Returns number of times killer killed victim
    elif message.content.startswith("$killCount"):
        players = get_players(message.content)
        query = {"_id": players[1]}
        user = collection.find(query)
        killers = []

        for result in user:
            killers = result["killedBy"]
        count = get_count(players[2], killers)
        await message.channel.send("```" + players[1] + " has been killed by " + players[2] + " "
                                   + str(count) + " times. ```")
    # $remove Killer Victim
    # Removes a kill from the killer and a death from the victim
    elif message.content.startswith("$remove"):
        players = get_players(message.content)
        query1 = {"_id": players[1]}
        query2 = {"_id": players[2]}

        # Make sure both users exist
        if collection.count_documents(query1) == 0 or collection.count_documents(query2) == 0:
            print(True)
            await message.channel.send("```Please ensure that both players are spelled correctly or have been"
                                       "previously added to the TeamKill Tracker (case sensitive)```")
            return

        user1 = collection.find(query1)
        user2 = collection.find(query2)

        old_kills = 0
        old_victims = []
        for result in user1:
            old_kills = result["teamKill"]
            old_victims = result["victims"]
        # Check if killer has killed anyone
        if len(old_victims) == 0:
            await message.channel.send("```" + players[1] + " has not killed any players...```")
            return
        updated_kills = old_kills - 1
        old_victims.pop()
        collection.update_one({"_id": players[1]}, {"$set": {"teamKill": updated_kills, "victims": old_victims}})

        old_deaths = 0
        old_killers = []
        for result in user2:
            old_deaths = result["death"]
            old_killers = result["killedBy"]
        # Check if victim has died
        if len(old_killers) == 0:
            await message.channel.send("```" + players[2] + " has not been killed by anyone yet...```")
            return
        updated_deaths = old_deaths - 1
        old_killers.pop()
        collection.update_one({"_id": players[2]}, {"$set": {"killedBy": old_killers, "death": updated_deaths}})
        await message.channel.send("```One kill has been removed from " + players[1] +
                                   " and one death has been removed from " + players[2] + "```")
    # $serialKiller Killer
    # Returns the total amount of team kills of the player
    elif message.content.startswith("$serialKiller"):
        players = get_players(message.content)
        query = {"_id": players[1]}
        if collection.count_documents(query) == 0:
            await message.channel.send("```No such player exists.```")
            return
        user = collection.find(query)

        kills = []
        for result in user:
            kills = result["victims"]
        kill_count = len(kills)
        await message.channel.send("```" + players[1] + " has killed " + str(kill_count) + "players```")
    # $deathCount Victim
    # Returns the total number of deaths
    elif message.content.startswith("$deathCount"):
        players = get_players(message.content)
        query = {"_id": players[1]}
        if collection.count_documents(query) == 0:
            await message.channel.send("```No such player exists.```")
            return
        user = collection.find(query)

        deaths = []
        for result in user:
            deaths = result["killedBy"]
        death_count = len(deaths)
        await message.channel.send("```" + players[1] + " has died " + str(death_count) + " times```")
    # $stalker Victim
    # Returns the name of person that has killed victim most
    elif message.content.startswith("$stalker"):
        players = get_players(message.content)
        query = {"_id": players[1]}
        if collection.count_documents(query) == 0:
            await message.channel.send("```No such player exists.```")
            return
        user = collection.find(query)

        deaths = []
        for result in user:
            deaths = result["killedBy"]
        stalker = get_stalker(deaths)
        await message.channel.send("```" + stalker + " has killed " + players[1] + " the most.```")
    # $help
    # Returns commands for how to use bot
    elif message.content.startswith("$help"):
        await message.channel.send(
            "```List of commands for TTK. Everything after the first dollarsign command are the parameters\n" +
            "$tk Killer Victim - Logs a kill for the killer and death for the victim\n" +
            "$remove Killer Victim - Removes a kill from the Killer and death from the Victim if both users are valid\n" +
            "$killCount Victim Killer - Returns the number of time Killer has killed Victim\n" +
            "$deathCount Victim - Returns the number of times the Victim has died\n" +
            "$serialKiller Killer - Returns the the total number of teamkills by the killer\n" +
            "$stalker Victim - Returns the player that has killed the Victim the most\n```"
        )


def get_stalker(deaths):
    Hash = dict()
    for i in range(len(deaths)):
        if deaths[i] in Hash.keys():
            Hash[deaths[i]] += 1
        else:
            Hash[deaths[i]] = 1

    max_count = 0
    res = -1
    for i in Hash:
        if max_count < Hash[i]:
            res = i
            max_count = Hash[i]
    return res


def get_players(players):
    return players.split(" ")


def get_count(killer, list_killers):
    count = 0
    for kills in list_killers:
        if kills == killer:
            count = count + 1
    return count


