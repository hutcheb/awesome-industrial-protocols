# Turn/IP
# Claire-lex - 2023
# MongoDB database manager

"""Interface with MongoDB database

The database has two collections:
- protocols
- links

Each collection contains one document per protocol/link.
Each document contains varying fields with values.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
# Internal
from config import mongodb, p
from . import search

#-----------------------------------------------------------------------------#
# Constants                                                                   #
#-----------------------------------------------------------------------------#

# Errors
ERR_DBCONNECT = "Connection to database failed."
ERR_UNKPROTO = "Protocol '{0}' not found."
ERR_MULTIPROTO = "Multiple match found, please choose between {0}."

#-----------------------------------------------------------------------------#
# MongoDB classes                                                             #
#-----------------------------------------------------------------------------#

# Error handling
class DBException(Exception):
    pass

class MongoDB(object):
    """MongoDB manager as a singleton class."""
    client = None
    db = None

    # Singleton stuff
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MongoDB, cls).__new__(cls)
            # Setting only one MongoDB Client
            cls.instance.client = MongoClient(mongodb.host, mongodb.port,
                                              serverSelectionTimeoutMS=mongodb.timeout)
            cls.instance.db = cls.instance.client[mongodb.database]
        return cls.instance

    def __init__(self):
        # We want to check that the connection is OK every time.
        self.__check_connection()
    
    #-------------------------------------------------------------------------#
    # Public                                                                  #
    #-------------------------------------------------------------------------#
    
    def get_protocol(self, name: str=None) -> dict:
        """Return the document associated to the protocol "name" as a dict.

        The research is case-insensitive. The name also be one of the aliases.

        :raises DBException: If the protocol does not exist.
        """
        # No argument == return all protocols :)
        if not name:
            return [x for x in self.protocols.find()]
        # We cannot just use find_one() / find(): we want case insensitive search
        match = []
        for proto in self.protocols.find():
            all_names = [x for x in self.__get_all_names(proto)]
            if len(search(name, all_names)):
                match.append(proto)
        if len(match) == 1:
            return match[0]
        if len(match) > 1:
            match = [x[p.name] for x in match]
            raise DBException(ERR_MULTIPROTO.format(", ".join(match)))
        raise DBException(ERR_UNKPROTO.format(name))

    @property
    def protocols(self):
        return self.db[mongodb.protocols]

    @property
    def links(self):
        return self.db[mongodb.links]
    
    #-------------------------------------------------------------------------#
    # Private                                                                 #
    #-------------------------------------------------------------------------#

    def __check_connection(self):
        try:
            self.client.admin.command('ping')
        except ConnectionFailure:
            raise DBException(ERR_DBCONNECT)
    
    def __get_all_names(self, protocol: dict) -> list:
        names = [protocol[p.name]]
        names += protocol[p.alias] if isinstance(protocol[p.alias], list) else \
                 [protocol[p.alias]]
        return list(filter(None, names)) # Removing empty items

        
