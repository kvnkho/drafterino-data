# Combo Checker

# Not all combos return results from the OpenDota API in less than 10 seconds
# We can only get the combos that appear frequently enough

# This script loops through all hero combinations and keeps the ones that return 
# results. The ones that do not return results will not be included in the script
# that loops through all results and calculates the win rate. This will save us API calls

# Runtime is around 2 hrs

import requests
import json
import itertools # combinations
import time

from pymongo import MongoClient

#User defined modules
from dbconn import connectToDatabase
from heroes import getHeroes

def queryBuilder(hero_id1, hero_id2, limit):
	query = ('''
		SELECT
		public_matches.match_id,
		public_matches.start_time,
		public_matches.radiant_win win,
		public_player_matches.hero_id,
		second_player.hero_id as teammate
		FROM public_player_matches
		INNER JOIN public_player_matches second_player using(match_id)
		LEFT JOIN public_matches using(match_id)
		WHERE TRUE
		AND public_player_matches.player_slot < 128
		AND second_player.player_slot < 128
		AND public_player_matches.hero_id = ''' 
		+ str(hero_id1) + 
		'''AND second_player.hero_id = '''
		+ str(hero_id2) + 
		'''
		AND public_matches.start_time >= (extract(epoch from now()) - (86400 * 2))
		AND public_matches.start_time <= (extract(epoch from now()) - (86400 * 1.5))
		LIMIT '''
		+ str(limit) 
		)
	return(query)

def postComboToDatabase(viable_combo, dbconn):
    # Create collection if none exist. Collection is created lazily
    # It only exists when data is added to it
    collection = dbconn['combo_check']

    # Perform bulk insert on heroes to database
    collection.insert_one(viable_combo)
    return()


if __name__ == "__main__":

	dbconn = connectToDatabase()
	heroes = getHeroes(dbconn)
	hero_ids = sorted([x['id'] for x in heroes])

	limit = 40

	existing = dbconn['combo_check'].find()
	existing = [x['heroes'] for x in existing]

	for combo in itertools.combinations(hero_ids, 2):

		if [combo[0], combo[1]] not in existing:
			
			print("Checking hero combination " + str(combo))
			query = queryBuilder(combo[0],combo[1], limit)

			viability = requests.get('https://api.opendota.com/api/explorer', params = {'sql': query}).json()

			if viability['err'] is not None:
				viable_combo = {'heroes': combo, 'value':0}
				print(viability['err'])
			else:
				viable_combo = {'heroes': combo, 'value':1}

			postComboToDatabase(viable_combo, dbconn)

			# Just to avoid API free-tier limit
			time.sleep(5)

	