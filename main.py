#! /usr/bin/python
#Copyright 2014 Michael Archibald

# from BeautifulSoup import SoupStrainer, BeautifulSoup as BS
import re
import urllib2
import sqlite3

# URL from which the video streams will be pulled
STREAMS_URL = 'http://cdn.tribtv.com/ake/embed.html?station=wreg&feed=1&auto=true'

# Akamia Doesn't like us pulling the m3u8 file when we don't legitimately need it.
# So we pretend that we are running Android.
USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (\
KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'

# If True, extra output will be displayed
VERBOSE = True
    
# Matches lines that contain master.m3u8 URIs, station ids, and feed ids.
# Result: 'wgn[5] = "http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8";'
REGEX_STATION_LINE = re.compile('\w*\[\d\].*master.m3u8";')

# Matches the URI for the m3u8
# Result: 'http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8'
REGEX_M3U8_URL = re.compile('http:\/\/.+m3u8')

# Matches stationName
# Result: 'wgn'
REGEX_STATION_Name = re.compile('\w+(?=\[\d\])')

# Matches feedName
# Result: 'WGNTribune3_1'
REGEX_FEED_NAME = re.compile('[^\/][\w\d_]+(?=\@\d+\/)')

# Matches feedId
# Result: '192102'
REGEX_FEED_ID = re.compile('\d+(?=\/.*m3u8)')

# Matches EXT-X-STREAM-INF line in an m3u8 file.
# Result: '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=382000,RESOLUTION=320x180,CODECS="avc1.66.30, mp4a.40.2"'
REGEX_INF_LINE = re.compile('.+EXT-X-STREAM-INF.+')

# Matches an http URL
# Result: 'http://wregtribune-lh.akamaihd.net/i/WREGTribunePrimary_1@192110/index_350_av-b.m3u8?sd=10&rebase=on'
REGEX_HTTP_URL = re.compile('http:\/\/[^\s]+')

# Matches the resolution of the video stream.
# Result: '320x180'
REGEX_INF_RESOLUTION = re.compile('[^=]+(?=,CODECS)')

# Matches the bandwidth of the video stream.
# Result: '382000'
REGEX_INF_BANDWIDTH = re.compile('[^=]+(?=,RESOLUTION)')

# Matches the codecs of a video stream.
# Result: 'avc1.66.30, mp4a.40.2'
REGEX_INF_CODECS = re.compile('[^="]+(?=\")')

# List of stations. Each station is a list consisting of one or more feeds that correspond
# to that particular station.
# Suchthat- {'stationName', 'feedId', 'feedName', 'm3u8URL'}
stations = []

def getStationLines(streamsURL):
    ''' Finds lines containing all information needed for any given channel from the URL. '''
    try: req = urllib2.urlopen(streamsURL)
    except: return None
    
    html = req.read();
    return REGEX_STATION_LINE.findall(html)

def parseStationLines(m3u8Lines):
    ''' Takes lines pulled using getStationLines() and seperates relevant data '''
    stations = []
    for line in m3u8Lines:
        station = {}
        station['stationName'] = REGEX_STATION_Name.search(line).group().upper()
        station['feedId'] = REGEX_FEED_ID.search(line).group()
        station['feedName'] = REGEX_FEED_NAME.search(line).group()
        station['m3u8URL'] = REGEX_M3U8_URL.search(line).group()
        stations.append(station)
    
    return stations

def connectDB(dbFilename):
    try:
        conn = sqlite3.connect(dbFilename)  # @UndefinedVariable
        conn.row_factory = sqlite3.Row  # @UndefinedVariable
        return conn
    except:
        return None

def getFeedM3U8(m3u8URL):
    m3u8Req = urllib2.Request(m3u8URL, None, {'User-Agent': USER_AGENT})
    try:
        response = urllib2.urlopen(m3u8Req)
        html = response.read()
        response.close()
        return html
    except Exception,e:
        print(e)
        return None
    
def insertStations(db, stations):
    for station in stations:
        success = insertStation(db, station['stationName'])  # @UnusedVariable
#         print station['stationName'] + ' successful? ' + str(success)
    
def insertStation(db, stationName, stationState='', stationCity=''):
    ''' taking care of this as to insure a pattern of best practices '''
    if db:
        try:
            db.execute("insert into stations (STATION_NAME, STATION_STATE, STATION_CITY) values (?, ?, ?)", (stationName, stationState, stationCity))
            db.commit()
            return True
        except Exception,e:
            db.rollback()
            print str(e)
            return False
    else:
        return False

def deleteStation(db, stationId):
    try:
        db.execute("DELETE FROM stations WHERE STATION_ID=?", (stationId,))
        db.commit()
        if VERBOSE: print "Deleted station %s from DB." % (stationId)
    except Exception, e:
        db.rollback()
        print str(e)
        if VERBOSE: print "Failed to delete station %s from DB." % (stationId)
        
def deleteUnusedStations(db):
    '''Deletes stations that don't have a corrosponding feed.'''
    usedStationIds = db.execute('SELECT STATION_ID FROM feeds').fetchall()
    #collapses list of tuples into a list of ints
    #converts list into a set then back into a list.
    #which removes all dupes.
    usedStationIds = list(set([x[0] for x in usedStationIds]))
    allStationIds = db.execute('SELECT STATION_ID FROM stations').fetchall()
    allStationIds = [x[0] for x in allStationIds]
    
    unusedStationIds = list(set(allStationIds) - set(usedStationIds))
    for stationId in unusedStationIds:
        deleteStation(db, stationId)
    
def updateFeed(db, feedId, stationId, feedName, feedUrl, resolution='', bandwidth='', codecs='', requiresProxy=False, extraInfo=''):
        try:
            db.execute("UPDATE feeds SET FEED_ID=?, Station_ID=?, FEED_NAME=?, FEED_RESOLUTION=?\
            , FEED_BANDWIDTH=?, FEED_CODECS=?, FEED_REQUIRES_PROXY=?, EXTRA_INFO=? WHERE FEED_URL=?",
            (feedId, stationId, feedName, resolution, int(bandwidth), codecs, int(requiresProxy), extraInfo, feedUrl))
            db.commit()
            if VERBOSE: print "Updated feed where feedUrl=%s" % (feedUrl)
        except Exception,e:
            db.rollback()
            print str(e)
            if VERBOSE: print "Failed to update feed where feedUrl=%s" % (feedUrl)


def insertFeed(db, feedId, stationId, feedName, feedUrl, resolution='', bandwidth='', codecs = '', requiresProxy=False, extraInfo=''):
    ''' kargs options are, 'resolution', 'bandwidth', 'codecs', 'requiresProxy' '''
    if db:
        try:
            db.execute("insert into feeds (FEED_ID, Station_ID, FEED_NAME, FEED_URL, FEED_RESOLUTION\
            , FEED_BANDWIDTH, FEED_CODECS, FEED_REQUIRES_PROXY, EXTRA_INFO) values (?, ?, ?, ?, ?, ?, ?\
            , ?, ?)", (feedId, stationId, feedName, feedUrl, resolution, int(bandwidth), codecs, int(requiresProxy), extraInfo))
            
            db.commit()
            return True
        except Exception,e:
            db.rollback()
            print str(e)  
            print "Attempting to update feed on failed insertion."
            updateFeed(db, feedId, stationId, feedName, feedUrl, resolution, bandwidth, codecs, requiresProxy)
            return False
    else:
        return False
    
def insertFeeds(db, feeds):
    for feed in feeds:
        success = insertFeed(db, feed['feedId'], feed['stationId'], feed['feedName'], feed['feedUrl'], feed['resolution'], feed['bandwidth'], feed['codecs'])  # @UnusedVariable

def insertFeedsTest(db):
    import pickle
    
    with open('debugFeeds.list', 'r') as f:
        debugFeeds = pickle.load(f)
        insertFeeds(db, debugFeeds)
    
def parseFeed(db, stationName, m3u8URL):
    feeds = []
    try:
        m3u8 = getFeedM3U8(m3u8URL)
        infLines = REGEX_INF_LINE.findall(m3u8)
        httpLines = REGEX_HTTP_URL.findall(m3u8)
        
        for x in range(0, len(infLines)):
            feed = {}
            feed['feedId'] = REGEX_FEED_ID.search(httpLines[x]).group()
            feed['stationId'] = _getStationId(db, stationName)
            feed['feedName'] = REGEX_FEED_NAME.search(httpLines[x]).group()
            feed['feedUrl'] = httpLines[x]
            feed['resolution'] = REGEX_INF_RESOLUTION.search(infLines[x]).group()
            feed['bandwidth'] = REGEX_INF_BANDWIDTH.search(infLines[x]).group()
            feed['codecs'] = REGEX_INF_CODECS.search(infLines[x]).group()
            feeds.append(feed)
            
        return feeds
    except:
        return None
    
def parseFeedTest(db, stations):
    matches = (x for x in stations if x['stationName'] == 'WREG')
    match = None
    for x in matches:
        match = x
        
    feeds = parseFeed(db, match['stationName'], match['m3u8URL'])
    return feeds

def parseFeeds(db, stations):
    feeds = []
    stationIndex = 1
    for station in stations:
        feed = parseFeed(db, station['stationName'], station['m3u8URL'])
        if feed != None: 
            feeds += feed
#         else:
#             deleteStation(db, _getStationId(db, station['stationName']))
#             
        if VERBOSE: print 'Parsed station %s of %s' % (stationIndex, len(stations))
        stationIndex += 1
    return feeds

def _getStationId(db, stationName):
    ''' Returns the primary key for a given station name. '''
    if db:
        return db.execute('SELECT STATION_ID FROM stations WHERE STATION_NAME=?', (stationName,)).fetchone()[0]
    else:
        return None

def main():
    db = connectDB('feeds.sqlite')
    stationLines = getStationLines(STREAMS_URL)
    stations = parseStationLines(stationLines)
    insertStations(db, stations)
    feeds = parseFeeds(db, stations)
    insertFeeds(db, feeds)
#     insertFeedsTest(db)
    deleteUnusedStations(db)
    db.close()
    
main()