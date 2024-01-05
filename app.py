import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
from inspect import stack
from termcolor import colored
from time import sleep

# ----------------------------------------------------------------------------------------------------

application = Flask(__name__)

# ----------------------------------------------------------------------------------------------------

def set_message(message, messageType=None):
    if (messageType == 'warning'):
        print(colored('WARNING: ' + message, 'yellow'))
    elif (messageType == 'error'):
        print(colored('ERROR: ' + message, 'red'))
    else:
        print(message)

# ----------------------------------------------------------------------------------------------------

def try_requests(url, numTriesMax=10, timeWaitSeconds=1):
    r = None
    numTries = 0

    while (True):
        if (numTries == numTriesMax):
            message = 'Max. tries ({}) reached for: {}'.format(numTriesMax, url)
            set_message(message, 'warning')
            break
        elif (numTries > 0):
            sleep(timeWaitSeconds)
        r = requests.get(url)
        numTries += 1
        if (r.status_code == 200):
            break

    return r, numTries

# ----------------------------------------------------------------------------------------------------

@application.route('/catalogue-urls')
def get_catalogue_urls():
    catalogueUrls = []

    collectionUrl = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'
    collectionPage, numTries = try_requests(collectionUrl)

    try:
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
def get_dataset_urls():
    datasetUrls = []

    catalogueUrls = get_catalogue_urls()

    for catalogueUrl in catalogueUrls:
        cataloguePage, numTries = try_requests(catalogueUrl)

        try:
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
def get_feeds():
    feeds = []

    datasetUrls = get_dataset_urls()

    for datasetUrl in datasetUrls:
        datasetPage, numTries = try_requests(datasetUrl)

        try:
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

@application.route('/opportunities')
def get_opportunities(feedUrl=None):
    opportunities = {}

    if (stack()[1].function == 'dispatch_request'):
        feedUrl = request.args.get('url')

    if (not feedUrl):
        if (stack()[1].function == 'dispatch_request'):
            message = 'Feed URL must be given as a parameter via "/opportunities?url=your-feed-url"'
            set_message(message, 'warning')
            return message
        else:
            message = 'Feed URL must be given as a parameter via "get_opportunities(\'your-feed-url\')"'
            set_message(message, 'warning')
            return

    set_opportunities(feedUrl, opportunities)

    return list(opportunities.values())

# ----------------------------------------------------------------------------------------------------

def set_opportunities(feedUrl, opportunities):
    feedPage, numTries = try_requests(feedUrl)

    try:
        for item in feedPage.json()['items']:
            if (    'id' in item.keys()
                and 'state' in item.keys()
                and 'modified' in item.keys()
            ):
                if (item['state'] == 'updated'):
                    if (    item['id'] not in opportunities.keys()
                        or  item['modified'] > opportunities[item['id']]['modified']
                    ):
                        opportunities[item['id']] = item
                elif (  item['state'] == 'deleted'
                    and item['id'] in opportunities.keys()
                ):
                    del(opportunities[item['id']])
        if (feedPage.json()['next'] != feedUrl):
            set_opportunities(feedPage.json()['next'], opportunities)
    except:
        message = 'Can\'t get feed at: {}'.format(feedUrl)
        set_message(message, 'error')

# ----------------------------------------------------------------------------------------------------

if (__name__ == '__main__'):
    application.run()
