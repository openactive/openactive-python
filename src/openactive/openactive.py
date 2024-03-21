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

SECONDS_WAIT_NEXT_DEFAULT = 0.2

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
    verbose = kwargs.get('verbose', False)
    seconds_wait_retry = kwargs.get('seconds_wait_retry', 1)
    num_tries_max = kwargs.get('num_tries_max', 10)

    r = None
    num_tries = 0

    while (True):
        if (num_tries == num_tries_max):
            set_message('Max. tries ({}) reached for: {}'.format(num_tries_max, url), 'warning')
            break
        elif (num_tries > 0):
            set_message('Retrying ({}/{}): {}'.format(num_tries, num_tries_max-1, url), 'warning')
            sleep(seconds_wait_retry)
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
        if (any([type(i) != str for i in collection_page.json()['hasPart']])):
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
    flat = kwargs.get('flat', False)
    verbose = kwargs.get('verbose', False)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)

    dataset_urls = {}

    catalogue_urls = get_catalogue_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for catalogue_url_idx,catalogue_url in enumerate(catalogue_urls):
        try:
            if (catalogue_url_idx != 0):
                sleep(seconds_wait_next)
            catalogue_page, num_tries = try_requests(catalogue_url, **kwargs)
            if (catalogue_page.status_code != 200):
                raise Exception()
            if (any([type(i) != str for i in catalogue_page.json()['dataset']])):
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
    flat = kwargs.get('flat', False)
    verbose = kwargs.get('verbose', False)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)

    feeds = {}

    dataset_urls = get_dataset_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for dataset_url_idx,dataset_url in enumerate(dataset_urls):
        try:
            if (dataset_url_idx != 0):
                sleep(seconds_wait_next)
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
                                feed_out['datasetUrl'] = dataset_url
                            except:
                                feed_out['datasetUrl'] = ''
                            try:
                                feed_out['discussionUrl'] = jsonld['discussionUrl']
                            except:
                                feed_out['discussionUrl'] = ''
                            try:
                                feed_out['licenseUrl'] = jsonld['license']
                            except:
                                feed_out['licenseUrl'] = ''
                            try:
                                feed_out['publisherName'] = jsonld['publisher']['name']
                            except:
                                feed_out['publisherName'] = ''

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

feed_url_parts_groups = {
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
feed_url_parts_type_map = {
    'SessionSeries': 'ScheduledSession',
    'ScheduledSession': 'SessionSeries',
    'FacilityUse': 'Slot',
    'Slot': 'FacilityUse',
}

def get_partner_feed_url(feed1_url, feed2_url_options):
    feed2_url = None

    for feed1_url_parts_type,feed1_url_parts in feed_url_parts_groups.items():
        for feed1_url_part in feed1_url_parts:
            if (feed1_url_part in feed1_url):
                feed2_url_parts_type = feed_url_parts_type_map[feed1_url_parts_type]
                feed2_url_parts = feed_url_parts_groups[feed2_url_parts_type]
                for feed2_url_part in feed2_url_parts:
                    feed2_url_attempt = feed1_url.replace(feed1_url_part, feed2_url_part)
                    if (feed2_url_attempt in feed2_url_options):
                        feed2_url = feed2_url_attempt
                        break
            if (feed2_url is not None):
                break
        if (feed2_url is not None):
            break

    return feed2_url

# --------------------------------------------------------------------------------------------------

# This is a recursive function. On the first call the opportunities dictionary will be empty and so
# will be initialised. On subsequent automated internal calls it will have content to be added to.
# Also, if a call fails for some reason when running in some other code (i.e. when not running on a
# server), then the returned dictionary can be manually resubmitted as the argument instead of a starting
# URL string, and the code will continue from the 'nextUrl' in the dictionary.

opportunities_template = {
    'items': {},
    'urls': [],
    'firstUrlOrigin': '',
    'nextUrl': '',
}

def get_opportunities(arg, **kwargs):
    verbose = kwargs.get('verbose', False)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)

    if (    (verbose)
        and (stack()[0].function != stack()[1].function)
    ):
        print(stack()[0].function)

    if (type(arg) == str):
        if (len(arg) == 0):
            set_message('Invalid input, feed URL must be a string of non-zero length', 'warning')
            return
        opportunities = copy.deepcopy(opportunities_template)
        opportunities['nextUrl'] = get_opportunities_next_url(arg, opportunities)
    elif (type(arg) == dict):
        if (    (sorted(arg.keys()) != sorted(opportunities_template.keys()))
            or  (any([type(arg[key]) != type(opportunities_template[key]) for key in arg.keys()]))
            or  (len(arg['firstUrlOrigin']) == 0)
            or  (len(arg['nextUrl']) == 0)
        ):
            set_message('Invalid input, opportunities must be a dictionary with the expected content', 'warning')
            return
        opportunities = arg
    else:
        set_message('Invalid input, must be a feed URL string or an opportunities dictionary', 'warning')
        return

    try:
        feed_url = opportunities['nextUrl']
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
        if (    ('next' in feed_page.json().keys())
            and (type(feed_page.json()['next']) == str)
            and (len(feed_page.json()['next']) > 0)
        ):
            opportunities['nextUrl'] = get_opportunities_next_url(feed_page.json()['next'], opportunities)
        else:
            opportunities['nextUrl'] = ''
        if (opportunities['nextUrl'] != feed_url):
            opportunities['urls'].append(feed_url)
        if (    (opportunities['nextUrl'])
            and (opportunities['nextUrl'] != feed_url)
        ):
            sleep(seconds_wait_next)
            opportunities = get_opportunities(opportunities, **kwargs)
    except:
        set_message('Can\'t get feed: {}'.format(feed_url), 'error')

    return opportunities

# --------------------------------------------------------------------------------------------------

def get_opportunities_next_url(next_url_original, opportunities):
    next_url = ''

    next_url_original_unquoted = unquote(next_url_original)
    next_url_original_parsed = urlparse(next_url_original_unquoted)

    if (    (next_url_original_parsed.scheme != '')
        and (next_url_original_parsed.netloc != '')
    ):
        if (len(opportunities['urls']) == 0):
            opportunities['firstUrlOrigin'] = '://'.join([next_url_original_parsed.scheme, next_url_original_parsed.netloc])
        next_url = next_url_original_unquoted
    elif (  (next_url_original_parsed.path != '')
        or  (next_url_original_parsed.query != '')
    ):
        next_url = opportunities['firstUrlOrigin']
        if (next_url_original_parsed.path != ''):
            next_url += ('/' if (next_url_original_parsed.path[0] != '/') else '') + next_url_original_parsed.path
        if (next_url_original_parsed.query != ''):
            next_url += ('?' if (next_url_original_parsed.query[0] != '?') else '') + next_url_original_parsed.query

    return next_url

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
    item_data_types = {}

    for item in opportunities['items'].values():
        if ('data' in item.keys()):
            for key in ['type', '@type']:
                if (key in item['data'].keys()):
                    if (item['data'][key] not in item_data_types.keys()):
                        item_data_types[item['data'][key]] = 1
                    else:
                        item_data_types[item['data'][key]] += 1
                    break

    return item_data_types

# --------------------------------------------------------------------------------------------------

superevent_labels = \
        ['SessionSeries'] \
    +   ['FacilityUse', 'IndividualFacilityUse'] \
    +   ['EventSeries', 'HeadlineEvent'] \
    +   ['CourseInstance']
subevent_labels = \
        ['ScheduledSession', 'ScheduledSessions', 'session', 'sessions'] \
    +   ['Slot', 'Slot for FacilityUse'] \
    +   ['Event', 'OnDemandEvent']

def get_event_type(label):
    if (label in superevent_labels):
        return 'superevent'
    elif (label in subevent_labels):
        return 'subevent'
    else:
        return None

# --------------------------------------------------------------------------------------------------

def get_superevents(subevent, superevent_opportunities):
    superevents = []

    superevent_id_in_subevent = get_superevent_id_in_subevent(subevent)

    if (superevent_id_in_subevent is not None):
        for superevent in superevent_opportunities['items'].values():
            superevent_id, superevent_data_id = get_superevent_ids(superevent)
            if (superevent_id_in_subevent in [superevent_id, superevent_data_id]):
                superevents.append(superevent)

    return superevents

# --------------------------------------------------------------------------------------------------

def get_subevents(superevent, subevent_opportunities):
    subevents = []

    superevent_id, superevent_data_id = get_superevent_ids(superevent)

    if (    (superevent_id is not None)
        or  (superevent_data_id is not None)
    ):
        for subevent in subevent_opportunities['items'].values():
            superevent_id_in_subevent = get_superevent_id_in_subevent(subevent)
            if (    (superevent_id_in_subevent is not None)
                and (superevent_id_in_subevent in [superevent_id, superevent_data_id])
            ):
                subevents.append(subevent)

    return subevents

# --------------------------------------------------------------------------------------------------

def get_superevent_id_in_subevent(subevent):
    superevent_id_in_subevent = None

    if ('data' in subevent.keys()):
        for key in ['superEvent', 'facilityUse']:
            if (    (key in subevent['data'].keys())
                and (type(subevent['data'][key]) in [str, int])
            ):
                superevent_id_in_subevent = str(subevent['data'][key]).split('/')[-1]
                break

    return superevent_id_in_subevent

# --------------------------------------------------------------------------------------------------

def get_superevent_ids(superevent):
    superevent_id = None
    superevent_data_id = None

    for key in ['id', '@id']:
        if (    (key in superevent.keys())
            and (type(superevent[key]) in [str, int])
        ):
            superevent_id = str(superevent[key]).split('/')[-1]
            break

    if ('data' in superevent.keys()):
        for key in ['id', '@id']:
            if (    (key in superevent['data'].keys())
                and (type(superevent['data'][key]) in [str, int])
            ):
                superevent_data_id = str(superevent['data'][key]).split('/')[-1]
                break

    return superevent_id, superevent_data_id
