import copy
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from inspect import stack
from termcolor import colored
from time import sleep
from urllib.parse import unquote, urlparse

# ----------------------------------------------------------------------------------------------------

application = Flask(__name__)
session = requests.Session()

# ----------------------------------------------------------------------------------------------------

def set_message(message, messageType=None):
    if (messageType == 'warning'):
        print(colored('WARNING: ' + message, 'yellow'))
    elif (messageType == 'error'):
        print(colored('ERROR: ' + message, 'red'))
    else:
        print(message)

# ----------------------------------------------------------------------------------------------------

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

def try_requests(url, verbose=False, numTriesMax=10, timeWaitSeconds=1):
    r = None
    numTries = 0

    while (True):
        if (numTries == numTriesMax):
            message = 'Max. tries ({}) reached for: {}'.format(numTriesMax, url)
            set_message(message, 'warning')
            break
        elif (numTries > 0):
            message = 'Retrying ({}/{}): {}'.format(numTries, numTriesMax-1, url)
            set_message(message, 'warning')
            sleep(timeWaitSeconds)
        try:
            if (verbose):
                print(url)
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

@application.route('/catalogue-urls')
def get_catalogue_urls(verbose=False):

    # For function calls when running on a server:
    if (stack()[1].function == 'dispatch_request'):
        verbose = str(request.args.get('verbose')).lower() == 'true'

    catalogueUrls = []

    collectionUrl = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'

    try:
        collectionPage, numTries = try_requests(collectionUrl, verbose)
        if (all([type(i)==str for i in collectionPage.json()['hasPart']])):
            catalogueUrls.extend(collectionPage.json()['hasPart'])
        else:
            raise Exception()
    except:
        message = 'Can\'t get collection at: {}'.format(collectionUrl)
        set_message(message, 'error')

    return catalogueUrls

# ----------------------------------------------------------------------------------------------------

@application.route('/dataset-urls')
def get_dataset_urls(verbose=False):

    # For function calls when running on a server:
    if (stack()[1].function == 'dispatch_request'):
        verbose = str(request.args.get('verbose')).lower() == 'true'

    datasetUrls = []

    catalogueUrls = get_catalogue_urls()

    for catalogueUrl in catalogueUrls:
        try:
            cataloguePage, numTries = try_requests(catalogueUrl, verbose)
            if (all([type(i)==str for i in cataloguePage.json()['dataset']])):
                datasetUrls.extend(cataloguePage.json()['dataset'])
            else:
                raise Exception()
        except:
            message = 'Can\'t get catalogue at: {}'.format(catalogueUrl)
            set_message(message, 'error')

    return datasetUrls

# ----------------------------------------------------------------------------------------------------

@application.route('/feeds')
def get_feeds(verbose=False):

    # For function calls when running on a server:
    if (stack()[1].function == 'dispatch_request'):
        verbose = str(request.args.get('verbose')).lower() == 'true'

    feeds = []

    datasetUrls = get_dataset_urls()

    for datasetUrl in datasetUrls:
        try:
            datasetPage, numTries = try_requests(datasetUrl, verbose)
            if (datasetPage.status_code == 200):
                soup = BeautifulSoup(datasetPage.text, 'html.parser')
            else:
                raise Exception()
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
                                feeds.append(feedOut)
        except:
            message = 'Can\'t get dataset at: {}'.format(datasetUrl)
            set_message(message, 'error')

    return feeds

# ----------------------------------------------------------------------------------------------------

# This is a recursive function. On the first call the opportunities dictionary will be empty and so
# will be initialised. On subsequent automated internal calls it will have content to be added to.
# Also, if a call fails for some reason when running in some other code (i.e. when not running on a
# server), then the returned dictionary can be manually resubmitted as the argument instead of a starting
# URL string, and the code will determine the page in the RPDE stream to continue from.

opportunitiesTemplate = {
    'items': {},
    'urls': [],
    'firstPageOrigin': '',
    'nextPage': '',
}
@application.route('/opportunities')
def get_opportunities(arg=None, verbose=False):

    # For function calls when running on a server:
    if (stack()[1].function == 'dispatch_request'):
        verbose = str(request.args.get('verbose')).lower() == 'true'
        if (len(request.args.get('url')) == 0):
            message = 'Invalid input, feed URL must be given as a parameter via "/opportunities?url=your-feed-url"'
            set_message(message, 'warning')
            return message
        opportunities = copy.deepcopy(opportunitiesTemplate)
        opportunities['nextPage'] = set_url(request.args.get('url'), opportunities)
    # For function calls when running in some other code:
    elif (stack()[1].function == '<module>'):
        if (type(arg) == str):
            if (len(arg) == 0):
                message = 'Invalid input, feed URL must be a string of non-zero length'
                set_message(message, 'warning')
                return
            opportunities = copy.deepcopy(opportunitiesTemplate)
            opportunities['nextPage'] = set_url(arg, opportunities)
        elif (type(arg) == dict):
            if (sorted(arg.keys()) != sorted(opportunitiesTemplate.keys())
                or type(arg['nextPage'] != str)
                or len(arg['nextPage']) == 0
            ):
                message = 'Invalid input, opportunities must be a dictionary with the expected content'
                set_message(message, 'warning')
                return
            opportunities = arg
        else:
            message = 'Invalid input, must be a feed URL string or an opportunities dictionary'
            set_message(message, 'warning')
            return
    # For function calls when running recursively:
    elif (stack()[1].function == stack()[0].function):
        opportunities = arg

    try:
        feedUrl = opportunities['nextPage']
        feedPage, numTries = try_requests(feedUrl, verbose)
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
        opportunities['nextPage'] = set_url(feedPage.json()['next'], opportunities)
        if (opportunities['nextPage'] != feedUrl):
            opportunities['urls'].append(feedUrl)
            opportunities = get_opportunities(opportunities)
    except:
        message = 'Can\'t get feed at: {}'.format(feedUrl)
        set_message(message, 'error')

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
            opportunities['firstPageOrigin'] = '://'.join([urlParsed.scheme, urlParsed.netloc])
        url = urlUnquoted
    elif (  urlParsed.path != ''
        or  urlParsed.query != ''
    ):
        url = opportunities['firstPageOrigin']
        if (urlParsed.path != ''):
            url += ('/' if urlParsed.path[0] != '/' else '') + urlParsed.path
        if (urlParsed.query != ''):
            url += ('?' if urlParsed.query[0] != '?' else '') + urlParsed.query

    return url

# ----------------------------------------------------------------------------------------------------

if (__name__ == '__main__'):
    application.run()
