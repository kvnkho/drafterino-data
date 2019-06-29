# This file scrapes the hero counters from Dotabuff.
# This collects more data and saves API requests while doing so

import requests
import pandas

from datetime import datetime
from dbconn import connectToDatabase
from heroes import getHeroes

def createURL(hero):
	# Creates and returns the URL to scrape for a hero from Dotabuff
	base_url = 'https://www.dotabuff.com/heroes/'
	url = base_url + hero.lower().replace(' ','-') + '/counters?date=week'
	return url

def getDotabuffRaw(url):
	# Uses request library to get the Dotabuff data for a hero
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
	page = requests.get(url, headers = headers)

	return page

def parseDotabuffRaw(page)
	# Converts HTML into Pandas Dataframe
	# The dataframe we want is the 3rd on the page
	df = pd.read_html(page.text)
	df = df[3]
	return df

def checkUpdateTime(dbconn, hero_id):
	# Returns boolen saying if the entry is past 5 days old
	# If no entry, returns True
	collection = dbconn['countersUpdateTimes']
	time = collection.find_one({'hero_id': hero_id})
	time = list(time)
	if len(time) > 0:
		difftime = datetime.now - time[0]['time']
	else:
		return True

	return (difftime.days > 5)

def writeUpdateTime(dbconn, hero_id):
	# Creates a table that holds the update times for each hero
	# This table will help keep track of counter rates that have been updated
	collection = dbconn['countersUpdateTimes']
	collection.find_one_and_update({'hero_id': hero_id},{"$set":{'hero_id': hero_id, 'time':datetime.now()}}, upsert= True)
	print('Update time written')
	return

def generateCounterVector(dbconn, hero, matrix_size, heroes):
	# Hero is a dictionary containing the id and localized_name
	hero_id = hero['id']
	hero_name = hero['localized_name']
	url = createURL(hero_name)
	page = getDotabuffRaw(url)

	if page.status_code == 200:
		df = parseDotabuffRaw(page)
		writeUpdateTime(dbconn, hero_name)
	else:
		print("Dotabuff page did not load")
		print('URL was: ' + url)
		return
 
	#
	counter_vector = 
	for row in df.iterrows():

def createHeroCounters(dbconn, matrix_size):
	# If table doesn't exist, initialize with matrix
	collection = dbconn['hero_counters']
	if collection.count == 0:
		initlized_data = [[0 for _ in range(matrix_size)] for i in xrange(matrix_size)]
		collection.insert_one(initlized_data)
		print("Initialized hero counter table")
	else:
		print("Hero counter table already initialized")

	return

def getHeroCounters(dbconn):
	# Returns matrix of hero counters
	collection = dbconn['hero_counters']
	hero_counters = collection.find_one()
	return hero_counters

def updateHeroCounters(dbconn, hero_id, update_vector):
	collection = dbconn['hero_counters']
	hero_counters = collection.find_one()
	hero_counters[hero_id] = update_vector

	collection.find_one_and_update({},{"$set":{hero_counters}})
	return



# Connect to database
# Get hero list
dbconn = connectToDatabase()
heroes = getHeroes(dbconn)

matrix_size = max([hero['id'] for hero in heroes])
createHeroCounters(dbconn, matrix_size)


for hero in heroes:
	hero_name = hero['localized_name']
	hero_id = hero['id']

	if checkUpdateTime(hero_id)

# For each hero
# Check update time
# If the update time is recent, skip
# Create the URL
# Get page with requests
# Update the update time table
# Use pandas to read in data
# Double matrix gets edited
# 