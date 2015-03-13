import os
import xbmcaddon, xbmc, xbmcgui
import urllib, re
from elementtree import ElementTree as ET


def obj2u(obj):
    if isinstance (obj, unicode):
        return obj
    else:
        s = obj
        if not isinstance (obj, str):
            s = str(obj).encode('utf-8')
        return s.decode('utf-8')

def dict2u(obj):
    newDict = {}
    for key, item in obj.items():
        if isinstance (item, str):
            newDict[key] = obj2u(item)
        else:
            newDict[key] = item
    return newDict
        
__addonID__= "script.watched.states"
__addon__ = xbmcaddon.Addon( __addonID__ )
__addon_path__ = obj2u(__addon__.getAddonInfo('path'))
__lang__ = __addon__.getLocalizedString

def __language__(string):
    return __lang__(string).encode('utf-8','ignore')

watchedFile = xbmc.translatePath(__addon__.getSetting( "path" )) + "watched.xml"

def log(msg, loglevel=xbmc.LOGDEBUG):
    u = u"%s: %s" % (__addonID__, obj2u(msg))
    xbmc.log(u.encode('utf-8'), loglevel)

class WatchedWindow(xbmcgui.Window):
    def getMode(self):
        menuItems = [__language__(30200),__language__(30201),__language__(30203)]
        dialog = xbmcgui.Dialog()
        action = dialog.select(__language__(30202),menuItems)
        return action

    def confirm(self,message,text):
        dialog = xbmcgui.Dialog()
        return dialog.yesno(message,text)

def setEpisodeDetails(id, playcount, lastplayed):
    episodeDetailRes = eval(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %d, "playcount" : %s, "lastplayed" : "%s" }, "id": 1}' % (id, playcount, lastplayed)))
    log("Response to SetEpisodeDetails: %s" % episodeDetailRes)

def setMovieDetails(id, playcount, lastplayed):
    movDetailRes = eval(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %d, "playcount" : %s, "lastplayed" : "%s" }, "id": 1}' % (id, playcount, lastplayed)))
    log("Response to SetMovieDetails: %s" % movDetailRes)

def buildUniqueStrMovie(movie):
    return movie['label'] + obj2u(movie['year'])

def buildUniqueStrEpisode(episode):
    return episode['showtitle'] + "S" + obj2u(episode['season']) + "E" + obj2u(episode['episode'])
    
def queryAllMovies():
    moviesRpc = eval(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"properties": ["title", "file", "playcount", "lastplayed", "year"]}, "id": 1}'))
    log("Response to queryAllMovies: %s" % moviesRpc)
    
    if (not 'movies' in moviesRpc['result']):
        return {}
        
    movies = {}
    for m in (moviesRpc['result']['movies']):
        uMov = dict2u(m)
        movies[buildUniqueStrMovie(uMov)] = uMov
        
    log("queryAllMovies ID database: %s" % (movies))
        
    return movies

def queryAllEpisodes():
    episodesRpc = eval(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"properties": ["showtitle", "season", "episode", "title", "playcount", "lastplayed"]}, "id": 1}'))
    log("Response to queryAllEpisodes: %s" % (episodesRpc))

    if (not 'episodes' in episodesRpc['result']):
        return {}

    episodes = {}
    for e in (episodesRpc['result']['episodes']):
        eMov = dict2u(e)
        episodes[buildUniqueStrEpisode(eMov)] = eMov

    log("queryAllEpisodes ID database: %s" % (episodes))
    
    return episodes
    
def writeWatchedFile(strFileName):
    movies = queryAllMovies()
    episodes = queryAllEpisodes()
    xmlObj = ET.Element("watched")
    
    exportCount=0
    for key, item in movies.items():
        if item['playcount'] == 0:
            continue
            
        child = ET.SubElement(xmlObj, "movie")
        child.text = item['label']
        child.set('playcount', obj2u(item['playcount']))
        child.set('lastplayed', item['lastplayed'])
        child.set('year', obj2u(item['year']))
        exportCount+=1
        
    for key, item in episodes.items():
        if item['playcount'] == 0:
            continue
            
        child = ET.SubElement(xmlObj, "episode")
        child.text = item['label']
        child.set('playcount', obj2u(item['playcount']))
        child.set('lastplayed', item['lastplayed'])
        child.set('showtitle', item['showtitle'])
        child.set('season', obj2u(item['season']))
        child.set('episode', obj2u(item['episode']))
        exportCount+=1
        
    episodeFileObj = open(strFileName, 'w')
    expStr = ET.tostring(xmlObj, 'utf-8')
    expStr = expStr.replace('</movie>', '</movie>\n')
    expStr = expStr.replace('</episode>', '</episode>\n')
    episodeFileObj.write(expStr)
    episodeFileObj.close()

    return len(movies) + len(episodes), exportCount

def exportWatched(gui):
    count=0
    countExported=0
    fileExists = os.path.isfile(watchedFile)
    if not fileExists or (fileExists and gui.confirm(__language__(30300), __language__(30301) + '\n' + __language__(30302))):
        count, countExported=writeWatchedFile(watchedFile)

    xbmcgui.Dialog().ok(__language__(30310), str(count) + __language__(30311), str(countExported) + __language__(30314))

def xmlobject2py(xmlobj):
    movies = {}
    for subelement in xmlobj.findall('movie'):
        label = obj2u(subelement.text)
        playcount = int(subelement.get("playcount")) 
        lastplayed = obj2u(subelement.get("lastplayed"))
        year = int(subelement.get("year"))
        pyObj = {'label' : label, 'playcount' : playcount, 'lastplayed' : lastplayed, 'year' : year}
        movies[buildUniqueStrMovie(pyObj)] = pyObj
        
    episodes = {}
    for subelement in xmlobj.findall('episode'):
        label = obj2u(subelement.text)
        playcount = int(subelement.get("playcount"))
        lastplayed = obj2u(subelement.get("lastplayed"))
        episode = int(subelement.get("episode"))
        season = int(subelement.get("season"))
        showtitle = obj2u(subelement.get("showtitle"))
        pyObj = {'label' : label, 'playcount' : playcount, 'lastplayed' : lastplayed, 'episode' : episode, 'season' : season, 'showtitle' : showtitle}
        episodes[buildUniqueStrEpisode(pyObj)] = pyObj
        
    return movies, episodes

def importWatched(gui):
    #If file missing exit with prompt.
    if not (os.path.isfile(watchedFile)):
        xbmcgui.Dialog().ok(__language__(30500), __language__(30510) + '\n' + __language__(30520), '\n' + __language__(30530))
        return
    
    #Read the watched xml file
    watchedXMLObj = ET.parse(watchedFile)
    
    watchedMovies, watchedEpisodes = xmlobject2py(watchedXMLObj)
    count = len(watchedMovies) + len(watchedEpisodes)
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(__language__(30400), __language__(30401))

    allMovies = queryAllMovies()
    allEpisodes = queryAllEpisodes()
    
    i=0
    notFoundCount=0
    skipCount=0
    importCount=0
    for key,item in watchedMovies.items():
        if (int(item['playcount']) == 0):
            continue

        uniqueKey = buildUniqueStrMovie(item)
        if uniqueKey in allMovies:
            if (allMovies[uniqueKey]['playcount'] == item['playcount']) and (allMovies[uniqueKey]['lastplayed'] == item['lastplayed']):
                log("Skipped. Correct watched count and lastplayed already present in current database: %s" % uniqueKey)
                skipCount+=1
            else:
                log("Setting watched count: %s" % uniqueKey)
                movieid = allMovies[uniqueKey]['movieid']
                setMovieDetails(movieid, item['playcount'], item['lastplayed'])
                importCount+=1
        else:
            log("Did not find match for: %s" % key, xbmc.LOGNOTICE)
            notFoundCount+=1
        
        pDialog.update(int(i*100/count), __language__(30410) + str(i) + ' / ' + str(count))
        if (pDialog.iscanceled()):
            break
        i+=1
        
    for key,item in watchedEpisodes.items():
        if (int(item['playcount']) == 0):
            continue

        uniqueKey = buildUniqueStrEpisode(item)
        if uniqueKey in allEpisodes:
            if (allEpisodes[uniqueKey]['playcount'] == item['playcount']) and (allEpisodes[uniqueKey]['lastplayed'] == item['lastplayed']):
                log("Skipped. Correct watched count and lastplayed already present in current database: %s" % uniqueKey)
                skipCount+=1
            else:
                log("Setting watched count: %s" % uniqueKey)
                episodeid = allEpisodes[uniqueKey]['episodeid']
                setEpisodeDetails(episodeid, item['playcount'], item['lastplayed'])
                importCount+=1
        else:
            log("Did not find match for: %s" % key, xbmc.LOGNOTICE)
            notFoundCount+=1
        
        pDialog.update(int(i*100/count), __language__(30410) + str(i) + ' / ' + str(count))
        if (pDialog.iscanceled()):
            break
        i+=1

    pDialog.close()
    xbmcgui.Dialog().ok(__language__(30420), str(importCount) + __language__(30421), str(notFoundCount) + __language__(30422), str(skipCount) + __language__(30423))

def resetWatchStates(gui):
    if not gui.confirm(__language__(30600), __language__(30601)):
        return

    pDialog = xbmcgui.DialogProgress()
    pDialog.create(__language__(30610), __language__(30401))
    
    movies = queryAllMovies()
    episodes = queryAllEpisodes()

    #find items to reset
    resetCount=0
    moviesToReset = {}
    episodesToReset = {}
    for key, item in movies.items():
        if not item['playcount'] == 0:
            moviesToReset[item['movieid']] = {'playcount' : 0, 'lastplayed' : ''}
            resetCount+=1
        
    for key, item in episodes.items():
        if not item['playcount'] == 0:
            episodesToReset[item['episodeid']] = {'playcount' : 0, 'lastplayed' : ''}
            resetCount+=1
            
    log(episodesToReset)
            
    #execute resets
    i=0
    for key, item in episodesToReset.items():
        setEpisodeDetails(key, item['playcount'], item['lastplayed'])
        
        pDialog.update(int(i*100/resetCount), __language__(30410) + str(i) + ' / ' + str(resetCount))
        if (pDialog.iscanceled()):
            break
        i+=1

    for key, item in moviesToReset.items():
        setMovieDetails(key, item['playcount'], item['lastplayed'])
        
        pDialog.update(int(i*100/resetCount), __language__(30410) + str(i) + ' / ' + str(resetCount))
        if (pDialog.iscanceled()):
            break
        i+=1
        
    pDialog.close()
    xbmcgui.Dialog().ok(__language__(30611), str(i) + __language__(30612))

mydisplay = WatchedWindow()
mode = mydisplay.getMode();

if (mode == 0):
    exportWatched(mydisplay)
elif (mode == 1):
    importWatched(mydisplay)
elif (mode == 2):
    resetWatchStates(mydisplay)
else:
    log("Unknown action: %d" % mode, xbmc.LOGERROR)

del mydisplay
