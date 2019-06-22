import requests
import json
import pymongo # MongoDB connection
import time

from dbconn import connectToDatabase
from pymongo import MongoClient

# Extracts draft data for each team and posts it to MongoDB
# The MongoDB will be keyed by team then match ID

# Dota Patches
# Converted to epoch time using: https://www.epochconverter.com/
# Dates taken from: https://dota2.gamepedia.com/Patches
# Patch: 7.21 / Date: 29 Jan 2019 / Time: 1548720000
# Patch: 7.22 / Date: 24 May 2019 / Time: 1558656000 


def filterTeamIds(team_info):
    # Accepts JSON object of team information and removes duplicate
    # The duplicate will have a much lower win count (below 5 games)
    win_counts = {}
    del_indices = []
    for i in range(len(team_info)):
        team = team_info[i]['name']
        
        if team not in win_counts.keys():
            win_counts[team] = {}
            win_counts[team]['wins'] = team_info[i]['wins']
            win_counts[team]['index'] = i
            
        elif team_info[i]['wins'] > win_counts[team]['wins']:
            # Delete entry from team_info
            del_indices.append(team_info[win_counts[team]['index']])
            
            # Update win_counts
            win_counts[team]['wins'] = team_info[i]['wins']
            win_counts[team]['index'] = i
            
        else:
            # This means the existing entry had the higher win count
            # Just delete the newer entry
            del_indices.append(i)
    
    for i in reversed(del_indices):
        del team_info[i]
        
    return team_info

#def filterMatchIds(matches, start_time = 1548720000):
def filterMatchIds(team_name ,matches, dbconn, start_time = 1548720000):
    # Current Default is Patch 7.21
    # Filter on time to get patches
    matches = [x['match_id'] for x in matches if x['start_time'] > start_time]
    # Take out marxhes already in database
    existing_matches = getDatabaseMatches(team_name, dbconn)

    matches = list(set(matches) - set(existing_matches))
    print("Filtered")
    print(len(matches))

    return(matches)

def getTeamIds(team_names):
    # Accepts list of team_names to iterate and get the ids
    # Returns list of dictionaries with team info
    
    teams = requests.get("https://api.opendota.com/api/teams").json()
    
    team_info = []

    for team in teams:
        if team['name'] in team_names:
            team_info.append(team)

    team_info = filterTeamIds(team_info)
    team_ids = [x['team_id'] for x in team_info]
            
    return team_ids

def getTeamMatches(team_id, team_name, dbconn):
    matches = requests.get('https://api.opendota.com/api/teams/'+str(team_id)+'/matches').json()
    matches = filterMatchIds(team_name, matches, dbconn)
    return(matches)

def getMatchDraft(match_id):
    # For now, we'll return 
    match = requests.get('https://api.opendota.com/api/matches/'+str(match_id)) .json()
    draft_timings = match['draft_timings']
    start_time = match['start_time']
    # Commented out lines here are present in the team match history API but not in match API
    # opponent = match['opposing_team_name']
    # win = (draft['radiant'] == draft['radiant_win'])
    # draft = {'match_id': match_id, 'draft_timings': draft_timings, 'start_time': start_time,
    #         'opposing_team_name': opponent, 'win': win}
    draft = {'match_id': match_id, 'draft_timings': draft_timings, 'start_time': start_time}
    return(draft)

def getDatabaseMatches(team_name, dbconn):
    # Returns list of existing matches in database for a given team
    db = dbconn['match_history']

    existing_drafts = db.find_one({"team_name": team_name})

    # Prevent error from None type
    if existing_drafts:
        existing_drafts = existing_drafts['drafts']
        existing_drafts = [x['match_id'] for x in existing_drafts]
    else:
        existing_drafts = []

    return(existing_drafts)

def postToDatabase(team_name, drafts, dbconn):
    # Create collection if none exist. Collection is created lazily
    # It only exists when data is added to it
    if 'match_history' not in dbconn.list_collection_names():
        db = dbconn['match_history']
        db.create_index("team_name")
    else:
        db = dbconn['match_history']

    # Check if team name exists
    # If it does, we edit the entry. If not, we create and insert
    # Upsert parameter inserts a new entry to database if no current match

    db_entry = db.find_one({"team_name": team_name})
    if db_entry:
        # Update the matches with the ones not in the database
        # Add new drafts to list
        db_entry = db_entry['drafts']
        db_entry.extend(drafts)
    else:
        db_entry = drafts
    db.find_one_and_update({'team_name': team_name}, {'$set': {'drafts': db_entry}}, upsert = True)

    return()

# Connect to db
print("Connecting to database")
dbconn = connectToDatabase()

team_name = 'Evil Geniuses'
team_id = getTeamIds([team_name])
team_id = team_id[0]
print("Team ID is: " + str(team_id))
print("Team name is: " + team_name)

matches = getTeamMatches(team_id, team_name, dbconn)
print("Got team matches")

drafts = []
for match in matches:
    print("Getting Match " + str(match))
    time.sleep(1) # Prevent API Throttle of 60 requests/min
    draft = getMatchDraft(match)
    drafts.append(draft)

print("Posting to database")
postToDatabase(team_name, drafts, dbconn)


