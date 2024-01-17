import copy
import json
import requests
from bs4 import BeautifulSoup
from inspect import stack
from itertools import chain
from termcolor import colored
from time import sleep
from urllib.parse import unquote, urlparse

# ----------------------------------------------------------------------------------------------------

def set_message(message, messageType=None):
    if (messageType == 'calling'):
        print(colored('CALLING: ' + message, 'blue'))
    elif (messageType == 'warning'):
        print(colored('WARNING: ' + message, 'yellow'))
    elif (messageType == 'error'):
        print(colored('ERROR: ' + message, 'red'))
    else:
        print(message)

# ----------------------------------------------------------------------------------------------------

session = requests.Session()

# https://stackoverflow.com/a/65576055
# https://stackoverflow.com/a/72666365

# When making several requests to the same host, requests.get() can result in errors. For more robust
# behaviour, requests.Session().get() is used herein. If there are further issues, then try uncommenting
# the following code for even more supportive behaviour:

# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry
# retry_strategy = Retry(
#   total=3,
#   backoff_factor=1
# )
# adapter = HTTPAdapter(max_retries=retry_strategy)
# session.mount('https://', adapter)
# session.mount('http://', adapter)

def try_requests(url, numTriesMax=10, timeWaitSeconds=1, verbose=False):
    r = None
    numTries = 0

    while (True):
        if (numTries == numTriesMax):
            set_message('Max. tries ({}) reached for: {}'.format(numTriesMax, url), 'warning')
            break
        elif (numTries > 0):
            set_message('Retrying ({}/{}): {}'.format(numTries, numTriesMax-1, url), 'warning')
            sleep(timeWaitSeconds)
        try:
            if (verbose):
                set_message(url, 'calling')
            numTries += 1
            r = session.get(url)
            if (r.status_code == 200):
                break
        except Exception as error:
            set_message(str(error), 'error')
            # Continue otherwise we get kicked out of the while loop. This takes us to the top of the loop:
            continue

    return r, numTries

# ----------------------------------------------------------------------------------------------------

def get_catalogue_urls(flat=False, verbose=False):
    catalogueUrls = {}

    collectionUrl = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'

    if (verbose):
        print(stack()[0].function)

    try:
        collectionPage, numTries = try_requests(collectionUrl, verbose=verbose)
        if (collectionPage.status_code != 200):
            raise Exception()
        if (any([type(i)!=str for i in collectionPage.json()['hasPart']])):
            raise Exception()
        catalogueUrls[collectionUrl] = collectionPage.json()['hasPart']
    except:
        set_message('Can\'t get collection: {}'.format(collectionUrl), 'error')

    if (not flat):
        return catalogueUrls
    else:
        return list(chain.from_iterable(catalogueUrls.values()))

# ----------------------------------------------------------------------------------------------------

def get_dataset_urls(flat=False, verbose=False):
    datasetUrls = {}

    catalogueUrls = get_catalogue_urls(flat=True, verbose=verbose)

    if (verbose):
        print(stack()[0].function)

    for catalogueUrl in catalogueUrls:
        try:
            cataloguePage, numTries = try_requests(catalogueUrl, verbose=verbose)
            if (cataloguePage.status_code != 200):
                raise Exception()
            if (any([type(i)!=str for i in cataloguePage.json()['dataset']])):
                raise Exception()
            datasetUrls[catalogueUrl] = cataloguePage.json()['dataset']
        except:
            set_message('Can\'t get catalogue: {}'.format(catalogueUrl), 'error')

    if (not flat):
        return datasetUrls
    else:
        return list(chain.from_iterable(datasetUrls.values()))

# ----------------------------------------------------------------------------------------------------

def get_feeds(flat=False, verbose=False):
    feeds = {}

    datasetUrls = get_dataset_urls(flat=True, verbose=verbose)

    if (verbose):
        print(stack()[0].function)

    for datasetUrl in datasetUrls:
        try:
            datasetPage, numTries = try_requests(datasetUrl, verbose=verbose)
            if (datasetPage.status_code != 200):
                raise Exception()
            soup = BeautifulSoup(datasetPage.text, 'html.parser')
            for script in soup.head.find_all('script'):
                if (    'type' in script.attrs.keys()
                    and script['type'] == 'application/ld+json'
                ):
                    jsonld = json.loads(script.string)
                    if ('distribution' in jsonld.keys()):
                        for feedIn in jsonld['distribution']:
                            feedOut = {}

                            try:
                                feedOut['name'] = jsonld['name']
                            except:
                                feedOut['name'] = ''
                            try:
                                feedOut['type'] = feedIn['name']
                            except:
                                feedOut['type'] = ''
                            try:
                                feedOut['url'] = feedIn['contentUrl']
                            except:
                                feedOut['url'] = ''
                            try:
                                feedOut['datasetUrl'] = datasetUrl
                            except:
                                feedOut['datasetUrl'] = ''
                            try:
                                feedOut['discussionUrl'] = jsonld['discussionUrl']
                            except:
                                feedOut['discussionUrl'] = ''
                            try:
                                feedOut['licenseUrl'] = jsonld['license']
                            except:
                                feedOut['licenseUrl'] = ''
                            try:
                                feedOut['publisherName'] = jsonld['publisher']['name']
                            except:
                                feedOut['publisherName'] = ''

                            if (len(feedOut.keys()) > 1):
                                if (datasetUrl not in feeds.keys()):
                                    feeds[datasetUrl] = []
                                feeds[datasetUrl].append(feedOut)
        except:
            set_message('Can\'t get dataset: {}'.format(datasetUrl), 'error')

    if (not flat):
        return feeds
    else:
        return list(chain.from_iterable(feeds.values()))

# ----------------------------------------------------------------------------------------------------

# This is a recursive function. On the first call the opportunities dictionary will be empty and so
# will be initialised. On subsequent automated internal calls it will have content to be added to.
# Also, if a call fails for some reason when running in some other code (i.e. when not running on a
# server), then the returned dictionary can be manually resubmitted as the argument instead of a starting
# URL string, and the code will determine the page in the RPDE stream to continue from.

opportunitiesTemplate = {
    'items': {},
    'urls': [],
    'firstUrlOrigin': '',
    'nextUrl': '',
}
def get_opportunities(arg=None, verbose=False):

    if (type(arg) == str):
        if (len(arg) == 0):
            set_message('Invalid input, feed URL must be a string of non-zero length', 'warning')
            return
        opportunities = copy.deepcopy(opportunitiesTemplate)
        opportunities['nextUrl'] = set_url(arg, opportunities)
    elif (type(arg) == dict):
        if (    sorted(arg.keys()) != sorted(opportunitiesTemplate.keys())
            or  type(arg['nextUrl']) != str
            or  len(arg['nextUrl']) == 0
        ):
            set_message('Invalid input, opportunities must be a dictionary with the expected content', 'warning')
            return
        opportunities = arg
    else:
        set_message('Invalid input, must be a feed URL string or an opportunities dictionary', 'warning')
        return

    try:
        feedUrl = opportunities['nextUrl']
        feedPage, numTries = try_requests(feedUrl, verbose=verbose)
        if (feedPage.status_code != 200):
            raise Exception()
        for item in feedPage.json()['items']:
            if (all([key in item.keys() for key in ['id', 'state', 'modified']])):
                if (item['state'] == 'updated'):
                    if (    item['id'] not in opportunities['items'].keys()
                        or  item['modified'] > opportunities['items'][item['id']]['modified']
                    ):
                        opportunities['items'][item['id']] = item
                elif (  item['state'] == 'deleted'
                    and item['id'] in opportunities['items'].keys()
                ):
                    del(opportunities['items'][item['id']])
        opportunities['nextUrl'] = set_url(feedPage.json()['next'], opportunities)
        if (opportunities['nextUrl'] != feedUrl):
            opportunities['urls'].append(feedUrl)
            opportunities = get_opportunities(opportunities)
    except:
        set_message('Can\'t get feed: {}'.format(feedUrl), 'error')

    return opportunities

# ----------------------------------------------------------------------------------------------------

def set_url(urlOriginal, opportunities):
    url = ''

    urlUnquoted = unquote(urlOriginal)
    urlParsed = urlparse(urlUnquoted)

    if (    urlParsed.scheme != ''
        and urlParsed.netloc != ''
    ):
        if (len(opportunities['urls']) == 0):
            opportunities['firstUrlOrigin'] = '://'.join([urlParsed.scheme, urlParsed.netloc])
        url = urlUnquoted
    elif (  urlParsed.path != ''
        or  urlParsed.query != ''
    ):
        url = opportunities['firstUrlOrigin']
        if (urlParsed.path != ''):
            url += ('/' if urlParsed.path[0] != '/' else '') + urlParsed.path
        if (urlParsed.query != ''):
            url += ('?' if urlParsed.query[0] != '?' else '') + urlParsed.query

    return url

# ----------------------------------------------------------------------------------------------------

def get_item_kinds(opportunities):
    itemKinds = {}

    for item in opportunities['items'].values():
        if ('kind' in item.keys()):
            if (item['kind'] not in itemKinds.keys()):
                itemKinds[item['kind']] = 1
            else:
                itemKinds[item['kind']] += 1

    return itemKinds

# ----------------------------------------------------------------------------------------------------

def get_item_data_types(opportunities):
    itemDataTypes = {}

    for item in opportunities['items'].values():
        if ('data' in item.keys()):
            for type in ['type', '@type']:
                if (type in item['data'].keys()):
                    if (item['data'][type] not in itemDataTypes.keys()):
                        itemDataTypes[item['data'][type]] = 1
                    else:
                        itemDataTypes[item['data'][type]] += 1
                    break

    return itemDataTypes

# ----------------------------------------------------------------------------------------------------

urlPartsGroups = {
    'SessionSeries': [
      'session-series',
      'sessionseries',
    ],
    'ScheduledSession': [
      'scheduled-sessions',
      'scheduledsessions',
      'scheduled-session',
      'scheduledsession',
    ],
    'FacilityUse': [
      'individual-facility-uses',
      'individual-facilityuses',
      'individualfacility-uses',
      'individualfacilityuses',
      'individual-facility-use',
      'individual-facilityuse',
      'individualfacility-use',
      'individualfacilityuse',
      'facility-uses',
      'facilityuses',
      'facility-use',
      'facilityuse',
    ],
    'Slot': [
      'slots',
      'slot',
      'facility-use-slots',
      'facility-use-slot',
      'facility-uses/events',
      'facility-uses/event',
    ],
}
def get_partner_url(feedUrl1, feedUrls):
    feedUrl2 = None

    urlPart1 = None
    urlParts2 = None

    for urlPartsType,urlParts in urlPartsGroups.items():
        for urlPart in urlParts:
            if (urlPart in feedUrl1):
                urlPart1 = urlPart
                if (urlPartsType == 'SessionSeries'):
                    urlParts2 = urlPartsGroups['ScheduledSession']
                elif (urlPartsType == 'ScheduledSession'):
                    urlParts2 = urlPartsGroups['SessionSeries']
                elif (urlPartsType == 'FacilityUse'):
                    urlParts2 = urlPartsGroups['Slot']
                elif (urlPartsType == 'Slot'):
                    urlParts2 = urlPartsGroups['FacilityUse']
                break
        if (urlPart1):
            break

    if (urlPart1 and urlParts2):
        for urlPart2 in urlParts2:
            feedUrl2Attempt = feedUrl1.replace(urlPart1, urlPart2)
            if (feedUrl2Attempt in feedUrls):
                feedUrl2 = feedUrl2Attempt
                break

    return feedUrl2
