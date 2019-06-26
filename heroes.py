# Grabs hero list and stores them in database so that 
# we don't need to waste API calls on it anymore.

import requests
import json

from pymongo import MongoClient

# User-Defined modules
from dbconn import connectToDatabase


def getOpenDotaHeroes():
    # Just calls the API endpoint for heroes
    heroes = requests.get("https://api.opendota.com/api/heroes").json()     
    return(heroes)

def postHeroesToDatabase(heroes, dbconn):
    # Create collection if none exist. Collection is created lazily
    # It only exists when data is added to it
    db = dbconn['heroes']
    db.delete_many({})
    db.create_index("id")

    # Perform bulk insert onn heroes to database
    db.insert_many(heroes)
    return()

def getHeroes(dbconn):
    # Retrieves the hero dump from the database

    db = dbconn['heroes']
    return([hero for hero in db.find()])


if __name__ == "__main__":

	heroes = getOpenDotaHeroes()
	dbconn = connectToDatabase()
	print("Connected to database")

	postHeroesToDatabase(heroes, dbconn)
	print("Posted heroes to database")