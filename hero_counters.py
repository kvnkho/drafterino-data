# This file scrapes the hero counters from Dotabuff.
# This collects more data and saves API requests while doing so

import requests
import pandas as pd
import time

from datetime import datetime
from dbconn import connectToDatabase
from heroes import getHeroes

def createURL(hero):
	# Creates and returns the URL to scrape for a hero from Dotabuff
	base_url = 'https://www.dotabuff.com/heroes/'
	hero = hero.replace('\'','')
	url = base_url + hero.lower().replace(' ','-') + '/counters?date=week'

	return url

def getDotabuffRaw(url):
	# Uses request library to get the Dotabuff data for a hero
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
	page = requests.get(url, headers = headers)

	return page

def parseDotabuffRaw(page):
	# Converts HTML into Pandas Dataframe
	# The dataframe we want is the 3rd on the page
	df = pd.read_html(page.text)
	df = df[3]
	df.drop(['Hero'], axis = 1, inplace = True)
	df.columns = ['Hero', 'Disadvantage', 'Win Rate', 'Matches Played']

	return df

def checkUpdateTime(dbconn, hero_id):
	# Returns boolen saying if the entry is past 5 days old
	# If no entry, returns True
	collection = dbconn['countersUpdateTimes']
	time = collection.find_one({'hero_id': hero_id})
	
	if time:
		print('Last Update Time: ' + str(time['time']))
		difftime = datetime.now() - time['time']
	else:
		print('Last Update Time: None')
		return True

	return (difftime.days > 5)

def writeUpdateTime(dbconn, hero_id):
	# Creates a table that holds the update times for each hero
	# This table will help keep track of counter rates that have been updated
	collection = dbconn['countersUpdateTimes']
	collection.find_one_and_update({'hero_id': hero_id},{"$set":{'hero_id': hero_id, 'time':datetime.now()}}, upsert= True)
	print('Update time written')

	return

def generateCounterVector(hero, matrix_size, heroes):
	# Hero is a dictionary containing the id and localized_name
	hero_id = hero['id']
	hero_name = hero['localized_name']
	url = createURL(hero_name)
	page = getDotabuffRaw(url)

	if page.status_code == 200:
		df = parseDotabuffRaw(page)
	else:
		print("Dotabuff page did not load")
		print('URL was: ' + url)

		return
 	
	hero_ids = [x['id'] for x in heroes]
	hero_names = [x['localized_name'] for x in heroes]

	counter_vector = [0] * matrix_size

	for index, row in df.iterrows():

		ind = hero_names.index(row['Hero'])
		counter_vector[hero_ids[ind]] = row['Disadvantage']

	writeUpdateTime(dbconn, hero_id)

	return counter_vector

def createHeroCounters(dbconn, matrix_size):
	# If table doesn't exist, initialize with matrix
	collection = dbconn['hero_counters']
	if collection.count_documents({}) == 0:
		initlized_data = [[0 for _ in range(matrix_size)] for i in range(matrix_size)]
		collection.insert_one({'values': initlized_data})
		print("Initialized hero counter table")
	else:
		print("Hero counter table already initialized")

	return

def getHeroCounters(dbconn):
	# Returns matrix of hero counters
	collection = dbconn['hero_counters']
	hero_counters = collection.find_one()['values']

	return hero_counters

def updateHeroCounters(dbconn, hero_id, update_vector):
	collection = dbconn['hero_counters']
	hero_counters = collection.find_one()['values']
	hero_counters[hero_id] = update_vector

	collection.find_one_and_update({},{"$set":{'values' : hero_counters}})
	return



# Connect to database
# Get hero list
dbconn = connectToDatabase()
heroes = getHeroes(dbconn)

matrix_size = max([hero['id'] for hero in heroes]) + 1
createHeroCounters(dbconn, matrix_size)


for hero in heroes:
	hero_name = hero['localized_name']
	print("Processing " + hero_name)
	hero_id = hero['id']

	if checkUpdateTime(dbconn, hero_id):
		hero_counters = generateCounterVector(hero, matrix_size, heroes)
		updateHeroCounters(dbconn, hero_id, hero_counters)
		time.sleep(10)
	else:
		print(hero_name + " has already been scraped recently. Passing.")

	

# For each hero
# Check update time
# If the update time is recent, skip
# Create the URL
# Get page with requests
# Update the update time table
# Use pandas to read in data
# Double matrix gets edited
# 