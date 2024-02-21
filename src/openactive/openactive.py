import copy
import json
import requests
from bs4 import BeautifulSoup
from inspect import stack
from itertools import chain
from termcolor import colored
from time import sleep
from urllib.parse import unquote, urlparse

# --------------------------------------------------------------------------------------------------

def set_message(message, message_type=None):
    if (message_type == 'calling'):
        print(colored('CALLING: ' + message, 'blue'))
    elif (message_type == 'warning'):
        print(colored('WARNING: ' + message, 'yellow'))
    elif (message_type == 'error'):
        print(colored('ERROR: ' + message, 'red'))
    else:
        print(message)

# --------------------------------------------------------------------------------------------------

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

def try_requests(url, **kwargs):
    num_tries_max = kwargs.get('num_tries_max', 10)
    time_wait_seconds_retry = kwargs.get('time_wait_seconds_retry', 1)
    verbose = kwargs.get('verbose', False)

    r = None
    num_tries = 0

    while (True):
        if (num_tries == num_tries_max):
            set_message('Max. tries ({}) reached for: {}'.format(num_tries_max, url), 'warning')
            break
        elif (num_tries > 0):
            set_message('Retrying ({}/{}): {}'.format(num_tries, num_tries_max-1, url), 'warning')
            sleep(time_wait_seconds_retry)
        try:
            if (verbose):
                set_message(url, 'calling')
            num_tries += 1
            r = session.get(url)
            if (r.status_code == 200):
                break
        except Exception as error:
            set_message(str(error), 'error')
            # Continue otherwise we get kicked out of the while loop. This takes us to the top of the loop:
            continue

    return r, num_tries

# --------------------------------------------------------------------------------------------------

def get_catalogue_urls(**kwargs):
    flat = kwargs.get('flat', False)
    verbose = kwargs.get('verbose', False)

    catalogue_urls = {}

    collection_url = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'

    if (verbose):
        print(stack()[0].function)

    try:
        collection_page, num_tries = try_requests(collection_url, **kwargs)
        if (collection_page.status_code != 200):
            raise Exception()
        if (any([type(i)!=str for i in collection_page.json()['hasPart']])):
            raise Exception()
        catalogue_urls[collection_url] = collection_page.json()['hasPart']
    except:
        set_message('Can\'t get collection: {}'.format(collection_url), 'error')

    if (not flat):
        return catalogue_urls
    else:
        return list(chain.from_iterable(catalogue_urls.values()))

# --------------------------------------------------------------------------------------------------

def get_dataset_urls(**kwargs):
    time_wait_seconds = kwargs.get('time_wait_seconds', 0.2)
    flat = kwargs.get('flat', False)
    verbose = kwargs.get('verbose', False)

    dataset_urls = {}

    catalogue_urls = get_catalogue_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for catalogue_url_idx,catalogue_url in enumerate(catalogue_urls):
        try:
            if (catalogue_url_idx != 0):
                sleep(time_wait_seconds)
            catalogue_page, num_tries = try_requests(catalogue_url, **kwargs)
            if (catalogue_page.status_code != 200):
                raise Exception()
            if (any([type(i)!=str for i in catalogue_page.json()['dataset']])):
                raise Exception()
            dataset_urls[catalogue_url] = catalogue_page.json()['dataset']
        except:
            set_message('Can\'t get catalogue: {}'.format(catalogue_url), 'error')

    if (not flat):
        return dataset_urls
    else:
        return list(chain.from_iterable(dataset_urls.values()))

# --------------------------------------------------------------------------------------------------

def get_feeds(**kwargs):
    time_wait_seconds = kwargs.get('time_wait_seconds', 0.2)
    flat = kwargs.get('flat', False)
    verbose = kwargs.get('verbose', False)

    feeds = {}

    dataset_urls = get_dataset_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for dataset_url_idx,dataset_url in enumerate(dataset_urls):
        try:
            if (dataset_url_idx != 0):
                sleep(time_wait_seconds)
            dataset_page, num_tries = try_requests(dataset_url, **kwargs)
            if (dataset_page.status_code != 200):
                raise Exception()
            soup = BeautifulSoup(dataset_page.text, 'html.parser')
            for script in soup.head.find_all('script'):
                if (    ('type' in script.attrs.keys())
                    and (script['type'] == 'application/ld+json')
                ):
                    jsonld = json.loads(script.string)
                    if ('distribution' in jsonld.keys()):
                        for feed_in in jsonld['distribution']:
                            feed_out = {}

                            try:
                                feed_out['name'] = jsonld['name']
                            except:
                                feed_out['name'] = ''
                            try:
                                feed_out['type'] = feed_in['name']
                            except:
                                feed_out['type'] = ''
                            try:
                                feed_out['url'] = feed_in['contentUrl']
                            except:
                                feed_out['url'] = ''
                            try:
                                feed_out['dataset_url'] = dataset_url
                            except:
                                feed_out['dataset_url'] = ''
                            try:
                                feed_out['discussion_url'] = jsonld['discussionUrl']
                            except:
                                feed_out['discussion_url'] = ''
                            try:
                                feed_out['license_url'] = jsonld['license']
                            except:
                                feed_out['license_url'] = ''
                            try:
                                feed_out['publisher_name'] = jsonld['publisher']['name']
                            except:
                                feed_out['publisher_name'] = ''

                            if (len(feed_out.keys()) > 1):
                                if (dataset_url not in feeds.keys()):
                                    feeds[dataset_url] = []
                                feeds[dataset_url].append(feed_out)
        except:
            set_message('Can\'t get dataset: {}'.format(dataset_url), 'error')

    if (not flat):
        return feeds
    else:
        return list(chain.from_iterable(feeds.values()))

# --------------------------------------------------------------------------------------------------

# This is a recursive function. On the first call the opportunities dictionary will be empty and so
# will be initialised. On subsequent automated internal calls it will have content to be added to.
# Also, if a call fails for some reason when running in some other code (i.e. when not running on a
# server), then the returned dictionary can be manually resubmitted as the argument instead of a starting
# URL string, and the code will determine the page in the RPDE stream to continue from.

opportunities_template = {
    'items': {},
    'urls': [],
    'first_url_origin': '',
    'next_url': '',
}
def get_opportunities(arg, **kwargs):
    time_wait_seconds = kwargs.get('time_wait_seconds', 0.2)
    verbose = kwargs.get('verbose', False)

    if (    (verbose)
        and (stack()[0].function != stack()[1].function)
    ):
        print(stack()[0].function)

    if (type(arg) == str):
        if (len(arg) == 0):
            set_message('Invalid input, feed URL must be a string of non-zero length', 'warning')
            return
        opportunities = copy.deepcopy(opportunities_template)
        opportunities['next_url'] = set_url(arg, opportunities)
    elif (type(arg) == dict):
        if (    (sorted(arg.keys()) != sorted(opportunities_template.keys()))
            or  (type(arg['next_url']) != str)
            or  (len(arg['next_url']) == 0)
        ):
            set_message('Invalid input, opportunities must be a dictionary with the expected content', 'warning')
            return
        opportunities = arg
    else:
        set_message('Invalid input, must be a feed URL string or an opportunities dictionary', 'warning')
        return

    try:
        feed_url = opportunities['next_url']
        feed_page, num_tries = try_requests(feed_url, **kwargs)
        if (feed_page.status_code != 200):
            raise Exception()
        for item in feed_page.json()['items']:
            if (all([key in item.keys() for key in ['id', 'state', 'modified']])):
                if (item['state'] == 'updated'):
                    if (    (item['id'] not in opportunities['items'].keys())
                        or  (item['modified'] > opportunities['items'][item['id']]['modified'])
                    ):
                        opportunities['items'][item['id']] = item
                elif (  (item['state'] == 'deleted')
                    and (item['id'] in opportunities['items'].keys())
                ):
                    del(opportunities['items'][item['id']])
        opportunities['next_url'] = set_url(feed_page.json()['next'], opportunities)
        if (opportunities['next_url'] != feed_url):
            opportunities['urls'].append(feed_url)
            sleep(time_wait_seconds)
            opportunities = get_opportunities(opportunities, **kwargs)
    except:
        set_message('Can\'t get feed: {}'.format(feed_url), 'error')

    return opportunities

# --------------------------------------------------------------------------------------------------

def set_url(url_original, opportunities):
    url = ''

    url_unquoted = unquote(url_original)
    url_parsed = urlparse(url_unquoted)

    if (    (url_parsed.scheme != '')
        and (url_parsed.netloc != '')
    ):
        if (len(opportunities['urls']) == 0):
            opportunities['first_url_origin'] = '://'.join([url_parsed.scheme, url_parsed.netloc])
        url = url_unquoted
    elif (  (url_parsed.path != '')
        or  (url_parsed.query != '')
    ):
        url = opportunities['first_url_origin']
        if (url_parsed.path != ''):
            url += ('/' if (url_parsed.path[0] != '/') else '') + url_parsed.path
        if (url_parsed.query != ''):
            url += ('?' if (url_parsed.query[0] != '?') else '') + url_parsed.query

    return url

# --------------------------------------------------------------------------------------------------

def get_item_kinds(opportunities):
    item_kinds = {}

    for item in opportunities['items'].values():
        if ('kind' in item.keys()):
            if (item['kind'] not in item_kinds.keys()):
                item_kinds[item['kind']] = 1
            else:
                item_kinds[item['kind']] += 1

    return item_kinds

# --------------------------------------------------------------------------------------------------

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

# --------------------------------------------------------------------------------------------------

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
      'facility-uses/events',
      'facility-uses/event',
      'facility-use-slots',
      'facility-use-slot',
      'slots',
      'slot',
    ],
}
urlPartsTypeMap = {
    'SessionSeries': 'ScheduledSession',
    'ScheduledSession': 'SessionSeries',
    'FacilityUse': 'Slot',
    'Slot': 'FacilityUse',
}
def get_partner_url(url1, urls):
    url2 = None

    for url1PartsType,url1Parts in urlPartsGroups.items():
        for url1Part in url1Parts:
            if (url1Part in url1):
                url2PartsType = urlPartsTypeMap[url1PartsType]
                url2Parts = urlPartsGroups[url2PartsType]
                for url2Part in url2Parts:
                    url2Attempt = url1.replace(url1Part, url2Part)
                    if (url2Attempt in urls):
                        url2 = url2Attempt
                        break
            if (url2 is not None):
                break
        if (url2 is not None):
            break

    return url2

# --------------------------------------------------------------------------------------------------

def get_superevent_id_in_subevent(subevent):
    supereventIdInSubevent = None

    if (subevent.get('data') is not None):
        if (    (subevent['data'].get('superEvent') is not None)
            and (type(subevent['data']['superEvent']) in [str, int])
        ):
            supereventIdInSubevent = str(subevent['data']['superEvent']).split('/')[-1]
        elif (  (subevent['data'].get('facilityUse') is not None)
            and (type(subevent['data']['facilityUse']) in [str, int])
        ):
            supereventIdInSubevent = str(subevent['data']['facilityUse']).split('/')[-1]

    return supereventIdInSubevent

# --------------------------------------------------------------------------------------------------

def get_superevent_ids(superevent):
    supereventId = None
    supereventDataId = None

    if (    (superevent.get('id') is not None)
        and (type(superevent['id']) in [str, int])
    ):
        supereventId = str(superevent['id']).split('/')[-1]

    if (superevent.get('data') is not None):
        if (    (superevent['data'].get('id') is not None)
            and (type(superevent['data']['id']) in [str, int])
        ):
            supereventDataId = str(superevent['data']['id']).split('/')[-1]
        elif (  (superevent['data'].get('@id') is not None)
            and (type(superevent['data']['@id']) in [str, int])
        ):
            supereventDataId = str(superevent['data']['@id']).split('/')[-1]

    return supereventId, supereventDataId

# --------------------------------------------------------------------------------------------------

def get_superevents(subevent, supereventOpportunities):
    superevents = []

    supereventIdInSubevent = get_superevent_id_in_subevent(subevent)

    if (supereventIdInSubevent is not None):
        for superevent in supereventOpportunities['items'].values():
            supereventId, supereventDataId = get_superevent_ids(superevent)
            if (   (    (supereventId is not None)
                    and (supereventId == supereventIdInSubevent) )
                or (    (supereventDataId is not None)
                    and (supereventDataId == supereventIdInSubevent) )
            ):
                superevents.append(superevent)

    return superevents

# --------------------------------------------------------------------------------------------------

def get_subevents(superevent, subeventOpportunities):
    subevents = []

    supereventId, supereventDataId = get_superevent_ids(superevent)

    if (    (supereventId is not None)
        or  (supereventDataId is not None)
    ):
        for subevent in subeventOpportunities['items'].values():
            supereventIdInSubevent = get_superevent_id_in_subevent(subevent)
            if (   (    (supereventId is not None)
                    and (supereventId == supereventIdInSubevent) )
                or (    (supereventDataId is not None)
                    and (supereventDataId == supereventIdInSubevent) )
            ):
                subevents.append(subevent)

    return subevents
