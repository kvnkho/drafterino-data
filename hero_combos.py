# This script assumes the usage of an API key

import pandas as pd
import requests

# User-defined modules

from heroes import getHeroes
from heroes import getHeroWinRates
from dbconn import connectToDatabase


def createHeroCombos(dbconn, matrix_size):
	# If table doesn't exist, initialize with matrix
	collection = dbconn['hero_combos']
	if collection.count_documents({}) == 0:
		initlized_data = [[0 for _ in range(matrix_size)] for i in range(matrix_size)]
		collection.insert_one({'values': initlized_data})
		print("Initialized hero counter table")
	else:
		print("Hero combo table already initialized")

	return

def queryBuilder(hero_id1, hero_id2, radiant, starttime, window, limit):

	query = '''
			SELECT
			public_matches.match_id,
			public_matches.start_time,
			public_matches.radiant_win win,
			public_player_matches.hero_id,
			second_player.hero_id as teammate
			FROM public_player_matches
			INNER JOIN public_player_matches second_player using(match_id)
			LEFT JOIN public_matches using(match_id)
			WHERE TRUE'''

	if radiant:
		query = query + '''
			AND public_player_matches.player_slot < 128
			AND second_player.player_slot < 128'''
	else:
		query = query + '''
			AND public_player_matches.player_slot > 127
			AND second_player.player_slot > 127'''

	query = query + '''
			AND public_player_matches.hero_id = ''' + str(hero_id1)

	query = query + '''
			AND second_player.hero_id = '''+ str(hero_id2)

	query = query + '''
			AND public_matches.start_time >= (extract(epoch from now()) - (86400 * ''' + str(starttime) + "))"
	query = query + '''
			AND public_matches.start_time >= (extract(epoch from now()) - (86400 * ''' + str(starttime - window) +"))"
	
	query = query + '''
			LIMIT ''' + str(limit)

	return query


def checkUpdateTime(dbconn, hero_ids, threshold = 5):
	# Returns boolean saying if the entry needs updating
	# The threshold variable is number of days since data was updated
	# If no entry, returns True

	# hero_ids is a vector of 2 hero_id values
	collection = dbconn['combosUpdateTimes']

	time = collection.find_one({'hero_ids': hero_ids})
	
	if time:
		print('Last Update Time: ' + str(time['time']))
		difftime = datetime.now() - time['time']
	else:
		print('Last Update Time: None')
		return True

	return (difftime.days > threshold)

def checkSampleCount(dbconn, hero_ids, minimum_samples):
	# Chceks if the minimum number of samples are present to calculate win rate
	# Returns boolean saying if the hero combo needs more samples

	collection = dbconn['hero_combos_matches']
	hero_ids = sorted(hero_ids)
	samples = collection.find({'hero_ids': hero_ids})
	samples = len(samples)

	print('The current count for hero_id1 = ' + 
		hero_ids[0] + ' and hero_id2 = ' + hero_ids[1] + 
		'is ' + samples)

	return(samples < minimum_samples)



def writeUpdateTime(dbconn, hero_ids):
	# Creates a table that holds the update times for each hero
	# This table will help keep track of counter rates that have been updated
	collection = dbconn['combosUpdateTimes']

	if len(hero_ids) != 2:
		print("The hero ids supplied are: ")
		print(hero_ids)
		print("len(hero_ids) must equal 2")
		return

	# For each pair of heroes, we need to update 2 combinations
	collection.find_one_and_update({'hero_ids': hero_ids},{"$set":{'hero_ids': hero_ids, 'time':datetime.now()}}, upsert= True)
	collection.find_one_and_update({'hero_ids': hero_ids},{"$set":{'hero_ids': list(reversed(hero_ids)), 'time':datetime.now()}}, upsert= True)
	print('Update time written')

	return

def getHeroCombos(dbconn):
	# Returns matrix of hero counters
	collection = dbconn['hero_combos']
	hero_combos = collection.find_one({})['values']

	return hero_combos

def calculateHeroComboRate(dbconn, hero_ids, hero_winrates):
	# Returns combo synergy rate to write in db
	collection = dbconn['hero_combos_matches']
	hero_ids = sorted(hero_ids)
	samples = collection.find({'hero_ids': hero_ids})

	wins = sum(x['win'] for x in samples)
	win_rate = wins/len(samples)

	# Use some statistics to get synergy
	expected_win_rate = (hero_winrates[0] * hero_winrates[1]) / ((hero_winrates[0] * hero_winrates[1]) + ((1 -hero_winrates[0]) * (1-hero_winrates[1])))
	combo_rate = (win_rate - expected_win_rate) * 100

	return combo_rate

def putHeroCombos(dbconn, hero_ids, update_value):
	# Counters is updated a vector at a time
	# Combos is updated one value at a time
	collection = dbconn['hero_combos']
	hero_combos = collection.find_one()['values']
	hero_combos[hero_ids[0]][hero_ids[1]] = update_value
	hero_combos[hero_ids[1]][hero_ids[0]] = update_value

	collection.find_one_and_update({},{"$set":{'values' : hero_combos}})
	return

def updateHeroComboMatches(dbconn, hero_ids, ):

	# This method adds matches for a hero combination
	hero_ids = sorted(hero_ids)
	# This table keeps track of the matches and win/loss of heroes
	collection = dbconn['hero_combos_matches']

	return

if __name__ == "__main__":

	# There are two stopping conditions for the loop
	# One is time based. Did I get all the data I could in the last day?
	# The other is sample. Did I reach 600 samples?

	# Connect to database and get hero list
	dbconn = connectToDatabase()
	heroes = getHeroes(dbconn)

	# Get maximum matrix size and instantiate if does not exist
	matrix_size = max([hero['id'] for hero in heroes]) + 1
	createHeroCombos(dbconn, matrix_size)

	# Gets a pandas dataframe containing hero win rates
	win_rates = getHeroWinRates()

	# Loop one just gets matches and the results
	# Loop two will calculate the win rate increase
	for hero in heroes:

		hero_name = hero['localized_name']
		hero_id = hero['id']
		hero_winrate = win_rates.loc[win_rates['Hero'] == hero_name]['Win Rate'].values[0]

		for hero2 in heroes:

			hero_name2 = hero2['localized_name']
			hero_id2 = hero2['id']
			hero_winrate2 = win_rates.loc[win_rates['Hero'] == hero_name2]['Win Rate'].values[0]

			print("Processing hero1 = " + hero_name + " and hero2 = " + hero_name2)

			if checkUpdateTime(dbconn, [hero_id, hero_id2]): 

				while checkSampleCount(dbonn, [hero_id, hero_id2], 1000):
					# Scrape more matches and insert into DB

					# PULL MATCHES
					# Write a controller function
					{'match ID': XXX, 'radiant': XXX, 'win': XXX}
					## Write unique matches to combo matches


					time.sleep(1)

				# Check if the number of scraped matches is over 
				hero_combo_rate = calculateHeroComboRate(dbconn, [hero_id, hero_id2], [hero_winrate, hero_winrate2])
				putHeroCombos(dbconn, [hero_id, hero_id2], hero_combo_rate)
				writeUpdateTime(dbconn, [hero_id, hero_id2])
				

			else:
				print("The combination of " + hero_name + "and " + hero_name2 
					+ " has already been processed recently. Moving on...")