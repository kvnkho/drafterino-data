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

def getHeroWinRates():
    # Collects hero rates from a request to Dotabuff for last week
    url = 'https://www.dotabuff.com/heroes/winning?date=week'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    page = requests.get(url, headers = headers)

    # Get first table from the website
    df = pd.read_html(page.text)
    df = df[0]

    df.drop('Hero', axis = 1, inplace = True)
    df.columns = ['Hero', 'Win Rate', 'Pick Rate', 'KDA']
    df = df[['Hero', 'Win Rate']]

    df['Win Rate'] = df['Win Rate'].str.replace('%','')
    df['Win Rate'] = df['Win Rate'].astype(float)

    return df

if __name__ == "__main__":

	heroes = getOpenDotaHeroes()
	dbconn = connectToDatabase()
	print("Connected to database")

	postHeroesToDatabase(heroes, dbconn)
	print("Posted heroes to database")