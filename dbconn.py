# Contains connectors to the database.

from pymongo import MongoClient

def connectToDatabase():
    # Database currently lives in a Heroku App
    # Returns the database connection

    database_name = 'heroku_p0ncspzj'

    connection_params = {
    'user': 'kvnkho',
    'password': 'drafter123',
    'host': 'ds231207.mlab.com',
    'port': 31207,
    'namespace': database_name,
    }

    connection = MongoClient(
        'mongodb://{user}:{password}@{host}:'
        '{port}/{namespace}'.format(**connection_params)
    )

    dbconn = connection[database_name]

    return dbconn

