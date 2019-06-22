# Grabs hero list and stores them in database so that 
# we don't need to waste API calls on it anymore.

import requests
import json
import pymongo # MongoDB connection

from dbconn import connectToDatabase
from pymongo import MongoClient


def getHeroList():
    # Just calls the API endpoint for 
    
    heroes = requests.get("https://api.opendota.com/api/heroes").json()
            
    return(heroes)

def postToDatabase(heroes, dbconn):
    # Create collection if none exist. Collection is created lazily
    # It only exists when data is added to it
    if 'heroes' not in dbconn.list_collection_names():
        db = dbconn['heroes']
        db.create_index("id")
    else:
        db = dbconn['heroes']

    # Perform bulk insert onn heroes to database
    db.insert_many(heroes)

    return()

if __name__ == "__main__":

	heroes = getHeroList()
	dbconn = connectToDatabase()
	print("Connected to database")

	postToDatabase(heroes, dbconn)
	print("Posted heroes to database")