import sqlite3

class LocalNewsDB:
    def __init__(self, dbFileName):
        self.dbFileName = dbFileName
        self.db = self.connectDB(self.dbFileName)
        self.verbose = True
        
    def connectDB(self, dbFilename):
        try:
            conn = sqlite3.connect(self.dbFileName)  # @UndefinedVariable
            conn.row_factory = sqlite3.Row  # @UndefinedVariable
            return conn
        except Exception, e:
            print(e)
            return None
        
    def insertCity(self, cityName, cityState):
        try:
            self.db.execute('INSERT INTO cities (CITY_NAME, CITY_STATE_ values (?, ?)', (cityName, cityState))
            return True
        except Exception, e:
            print(e)
            return False
        
    def _getStationId(self,stationName):
        ''' Returns the primary key for a given station name. '''
        if self.db:
            return self.db.execute('SELECT STATION_ID FROM stations WHERE STATION_NAME=?', (stationName,)).fetchone()[0]
        else:
            return None
        
    def _getCityId(self, cityName, cityState):
        try:
            return self.db.execute('SELECT CITY_ID FROM cities WHERE CITY_NAME=? AND CITY_STATE=?', (cityName, cityState)).fetchone()[0]
        except Exception:
            print("inserting new city: %s, %s" % (cityName, cityState))
            self.insertCity(cityName, cityState)
            return self._getCityId(cityName, cityState)
        
    def insertStations(self, stations):
        for station in stations:
            success = self.insertStation(station['stationName'])  # @UnusedVariable
    #         print station['stationName'] + ' successful? ' + str(success)
        
    def insertStation(self, stationName, stationState='Unsorted', stationCity='Unsorted'):
        ''' taking care of this as tmport Plugin o insure a pattern of best practices '''
        if self.db:
            try:
                self.db.execute("insert into stations (STATION_NAME, CITY_ID) values (?, ?)", (stationName, self._getCityId(stationCity, stationState)))
                self.db.commit()
                return True
            except Exception,e:
                self.db.rollback()
                print str(e)
                return False
        else:
            return False
    
    def deleteStation(self, stationId):
        try:
            self.db.execute("DELETE FROM stations WHERE STATION_ID=?", (stationId,))
            self.db.commit()
            if self.verbose: print "Deleted station %s from DB." % (stationId)
        except Exception, e:
            self.db.rollback()
            print str(e)
            if self.verbose: print "Failed to delete station %s from DB." % (stationId)
            
    def deleteUnusedStations(self):
        '''Deletes stations that don't have a corrosponding feed.'''
        usedStationIds = self.db.execute('SELECT STATION_ID FROM feeds').fetchall()
        #collapses list of tuples into a list of ints
        #converts list into a set then back into a list.
        #which removes all dupes.
        usedStationIds = list(set([x[0] for x in usedStationIds]))
        allStationIds = self.db.execute('SELECT STATION_ID FROM stations').fetchall()
        allStationIds = [x[0] for x in allStationIds]
        
        unusedStationIds = list(set(allStationIds) - set(usedStationIds))
        for stationId in unusedStationIds:
            self.deleteStation(stationId)
        
    def updateFeed(self, feedId, stationId, feedName, feedUrl, resolution='', bandwidth='', codecs='', requiresProxy=False, extraInfo=''):
            try:
                self.db.execute("UPDATE feeds SET FEED_ID=?, Station_ID=?, FEED_NAME=?, FEED_RESOLUTION=?\
                , FEED_BANDWIDTH=?, FEED_CODECS=?, FEED_REQUIRES_PROXY=?, EXTRA_INFO=? WHERE FEED_URL=?",
                (feedId, stationId, feedName, resolution, int(bandwidth), codecs, int(requiresProxy), extraInfo, feedUrl))
                self.db.commit()
                if self.verbose: print "Updated feed where feedUrl=%s" % (feedUrl)
            except Exception,e:
                self.db.rollback()
                print str(e)
                if self.verbose: print "Failed to update feed where feedUrl=%s" % (feedUrl)
    
    
    def insertFeed(self, feedId, stationId, feedName, feedUrl, resolution='', bandwidth='', codecs = '', requiresProxy=False, extraInfo=''):
        ''' kargs options are, 'resolution', 'bandwidth', 'codecs', 'requiresProxy' '''
        if self.db:
            try:
                self.db.execute("insert into feeds (FEED_ID, Station_ID, FEED_NAME, FEED_URL, FEED_RESOLUTION\
                , FEED_BANDWIDTH, FEED_CODECS, FEED_REQUIRES_PROXY, EXTRA_INFO) values (?, ?, ?, ?, ?, ?, ?\
                , ?, ?)", (feedId, stationId, feedName, feedUrl, resolution, int(bandwidth), codecs, int(requiresProxy), extraInfo))
                
                self.db.commit()
                return True
            except Exception,e:
                self.db.rollback()
                print str(e)  
                print "Attempting to update feed on failed insertion."
                self.updateFeed(feedId, stationId, feedName, feedUrl, resolution, bandwidth, codecs, requiresProxy)
                return False
        else:
            return False
        
    def insertFeeds(self, feeds):
        for feed in feeds:
            success = self.insertFeed(feed['feedId'], feed['stationId'], feed['feedName'], feed['feedUrl'], feed['resolution'], feed['bandwidth'], feed['codecs'])  # @UnusedVariable
    
    def insertFeedsTest(self):
        import pickle
        
        with open('debugFeeds.list', 'r') as f:
            debugFeeds = pickle.load(f)
            self.insertFeeds(debugFeeds)
            
    
    def close(self):
        try:
            self.db.close()
        except Exception, e:
            print(e)