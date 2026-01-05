import copy
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from inspect import stack
from itertools import chain
from sys import getsizeof
from termcolor import colored
from time import sleep
from urllib.parse import unquote, urlparse

# --------------------------------------------------------------------------------------------------

SECONDS_TIMEOUT_DEFAULT = 600
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
#     total=3,
#     backoff_factor=1
# )
# adapter = HTTPAdapter(max_retries=retry_strategy)
# session.mount('https://', adapter)
# session.mount('http://', adapter)

def try_requests(url, **kwargs):
    headers = kwargs.get('headers', {'User-Agent': 'OpenActive user'})
    num_tries_max = kwargs.get('num_tries_max', 10)
    seconds_wait_retry = kwargs.get('seconds_wait_retry', 1)
    verbose = kwargs.get('verbose', False)

    r = None
    num_tries = 0

    while (True):
        if (num_tries == num_tries_max):
            set_message(f'Max. tries ({num_tries_max}) reached for: {url}', 'warning')
            break
        elif (num_tries > 0):
            set_message(f'Retrying ({num_tries}/{num_tries_max-1}): {url}', 'warning')
            sleep(seconds_wait_retry)
        try:
            if (verbose):
                set_message(url, 'calling')

            num_tries += 1
            r = session.get(url, headers=headers)

            # https://docs.python-requests.org/en/latest/user/advanced/
            # "Sessions can also be used as context managers [...] This will make sure the session is closed as
            # soon as the with block is exited, even if unhandled exceptions occurred."
            # r = None
            # with requests.Session() as session:
            #     r = session.get(url)

            if (r is None):
                raise Exception(f'{url}: Call failed with no response')
            elif (r.status_code != 200):
                raise Exception(f'{url}: Call failed with status code {r.status_code}')

            break
        except Exception as error:
            set_message(str(error), 'error')
            # Continue otherwise we get kicked out of the while loop. This takes us to the top of the loop:
            continue

    return r, num_tries

# --------------------------------------------------------------------------------------------------

def get_catalogue_urls(**kwargs):
    flat = kwargs.get('flat', False)
    preview = kwargs.get('preview', False)
    verbose = kwargs.get('verbose', False)

    catalogue_urls = {}

    if (not preview):
        collection_url = 'https://openactive.io/data-catalogs/data-catalog-collection.jsonld'
    else:
        collection_url = 'https://openactive.io/data-catalogs/data-catalog-collection-preview.jsonld'

    if (verbose):
        print(stack()[0].function)

    try:
        collection_page, num_tries = try_requests(collection_url, **kwargs)

        if (    (collection_page is None)
            or  (collection_page.status_code != 200)
            or  (any([type(i) != str for i in collection_page.json()['hasPart']]))
        ):
            raise Exception()

        catalogue_urls[collection_url] = collection_page.json()['hasPart']
    except:
        set_message(f'Can\'t get collection: {collection_url}', 'error')

    if (not flat):
        return catalogue_urls
    else:
        return list(chain.from_iterable(catalogue_urls.values()))

# --------------------------------------------------------------------------------------------------

def get_dataset_urls(**kwargs):
    flat = kwargs.get('flat', False)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)
    verbose = kwargs.get('verbose', False)

    dataset_urls = {}

    catalogue_urls = get_catalogue_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for catalogue_url_idx, catalogue_url in enumerate(catalogue_urls):
        try:
            catalogue_page, num_tries = try_requests(catalogue_url, **kwargs)

            if (    (catalogue_page is None)
                or  (catalogue_page.status_code != 200)
                or  (any([type(i) != str for i in catalogue_page.json()['dataset']]))
            ):
                raise Exception()

            dataset_urls[catalogue_url] = catalogue_page.json()['dataset']
        except:
            set_message(f'Can\'t get catalogue: {catalogue_url}', 'error')
        if (catalogue_url_idx < (len(catalogue_urls)-1)):
            sleep(seconds_wait_next)

    if (not flat):
        return dataset_urls
    else:
        return list(chain.from_iterable(dataset_urls.values()))

# --------------------------------------------------------------------------------------------------

def get_feeds(**kwargs):
    flat = kwargs.get('flat', False)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)
    verbose = kwargs.get('verbose', False)

    feeds = {}

    dataset_urls = get_dataset_urls(**{**kwargs, **{'flat': True}})

    if (verbose):
        print(stack()[0].function)

    for dataset_url_idx, dataset_url in enumerate(dataset_urls):
        try:
            dataset_page, num_tries = try_requests(dataset_url, **kwargs)

            if (    (dataset_page is None)
                or  (dataset_page.status_code != 200)
            ):
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
                                feed_out['type'] = feed_in['name']
                            except:
                                feed_out['type'] = ''
                            try:
                                feed_out['url'] = feed_in['contentUrl']
                            except:
                                feed_out['url'] = ''
                            try:
                                feed_out['dataset_name'] = jsonld['name']
                            except:
                                feed_out['dataset_name'] = ''
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
                                feed_out['logo_url'] = jsonld['publisher']['logo']['url']
                            except:
                                feed_out['logo_url'] = ''
                            try:
                                feed_out['publisher_name'] = jsonld['publisher']['name']
                            except:
                                feed_out['publisher_name'] = ''

                            if (dataset_url not in feeds.keys()):
                                feeds[dataset_url] = []
                            feeds[dataset_url].append(feed_out)
        except:
            set_message(f'Can\'t get dataset: {dataset_url}', 'error')
        if (dataset_url_idx < (len(dataset_urls)-1)):
            sleep(seconds_wait_next)

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
        'individual-facility-use/slots',
        'individual-facility-use/slot',
        'individual-facility-use-slots',
        'individual-facility-use-slot',
        'facility-uses/events',
        'facility-uses/event',
        'facility-uses-events',
        'facility-uses-event',
        'facility-use/events',
        'facility-use/event',
        'facility-use-events',
        'facility-use-event',
        'facility-uses/slots',
        'facility-uses/slot',
        'facility-uses-slots',
        'facility-uses-slot',
        'facility-use/slots',
        'facility-use/slot',
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

    for feed1_url_parts_type, feed1_url_parts in feed_url_parts_groups.items():
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

# On the first call to this function the opportunities dictionary will be empty and so will be initialised.
# On subsequent automated internal calls to the helper function, the opportunities dictionary will
# already exist and have content to be added to. If a call fails for some reason when running in some
# other code (i.e. when not running on a server), then the returned dictionary can be manually resubmitted
# as the argument instead of a starting URL string, and the code will continue from the 'next_url'
# in the opportunities dictionary.

opportunities_template = {
    'items': {},
    'num_urls': 0,
    'first_url_origin': '',
    'next_url': '',
    'status': '',
}

def get_opportunities(arg, **kwargs):
    log_memory = kwargs.get('log_memory', False)
    seconds_timeout = kwargs.get('seconds_timeout', SECONDS_TIMEOUT_DEFAULT)
    seconds_wait_next = kwargs.get('seconds_wait_next', SECONDS_WAIT_NEXT_DEFAULT)
    verbose = kwargs.get('verbose', False)

    if (    (verbose)
        and (stack()[0].function != stack()[1].function)
    ):
        print(stack()[0].function)

    if (type(arg) == str):
        if (len(arg) == 0):
            set_message('Invalid input, feed URL must be a string of non-zero length', 'warning')
            if (log_memory):
                return None, 0
            else:
                return None
        opportunities = copy.deepcopy(opportunities_template)
        opportunities['next_url'] = get_opportunities_next_url(arg, opportunities)
    elif (type(arg) == dict):
        # Note that we allow for extra keys in the incoming opportunities dictionary which aren't in the template,
        # in case the user has added custom fields. These don't affect the processing herein, and so aren't
        # restricted:
        if (    (any([((key not in arg.keys()) or (type(arg[key]) != type(opportunities_template[key]))) for key in opportunities_template.keys()]))
            or  (len(arg['first_url_origin']) == 0)
            or  (len(arg['next_url']) == 0)
        ):
            set_message('Invalid input, opportunities must be a dictionary with the expected content', 'warning')
            if (log_memory):
                return None, 0
            else:
                return None
        opportunities = arg
        opportunities['status'] = opportunities_template['status']
    else:
        set_message('Invalid input, must be a feed URL string or an opportunities dictionary', 'warning')
        if (log_memory):
            return None, 0
        else:
            return None

    if (log_memory):
        sum_bytesize_item_deltas = 0

    try:
        time_start = datetime.now()
        while (True):
            feed_url = opportunities['next_url']

            if (log_memory):
                opportunities, get_opportunities_helper_done, sum_bytesize_item_deltas_current = get_opportunities_helper(opportunities, **kwargs)
                sum_bytesize_item_deltas += sum_bytesize_item_deltas_current
            else:
                opportunities, get_opportunities_helper_done = get_opportunities_helper(opportunities, **kwargs)

            if (get_opportunities_helper_done):
                opportunities['status'] = 'COMPLETE'
                break
            elif ((datetime.now() - time_start).seconds >= seconds_timeout):
                opportunities['status'] = 'TIMEOUT'
                break
            else:
                sleep(seconds_wait_next)

    except:
        opportunities['status'] = 'ERROR'
        set_message(f'Can\'t get feed: {feed_url}', 'error')

    if (log_memory):
        return opportunities, sum_bytesize_item_deltas
    else:
        return opportunities

# --------------------------------------------------------------------------------------------------

def get_opportunities_helper(opportunities, **kwargs):
    log_memory = kwargs.get('log_memory', False)
    verbose = kwargs.get('verbose', False)

    feed_url = opportunities['next_url']
    feed_page, num_tries = try_requests(feed_url, **kwargs)

    if (    (feed_page is None)
        or  (feed_page.status_code != 200)
    ):
        raise Exception()

    if (log_memory):
        sum_bytesize_item_deltas = 0

    for item in feed_page.json()['items']:
        if (all([key in item.keys() for key in ['id', 'state', 'modified']])):
            if (log_memory):
                bytesize_item_delta = 0
            if (item['state'] == 'updated'):
                if (    (item['id'] not in opportunities['items'].keys())
                    or  (item['modified'] > opportunities['items'][item['id']]['modified'])
                ):
                    if (log_memory):
                        bytesize_item_old = get_bytesize(opportunities['items'][item['id']]) if (item['id'] in opportunities['items'].keys()) else 0
                        bytesize_item_new = get_bytesize(item)
                        bytesize_item_delta = bytesize_item_new - bytesize_item_old
                    opportunities['items'][item['id']] = item
            elif (  (item['state'] == 'deleted')
                and (item['id'] in opportunities['items'].keys())
            ):
                if (log_memory):
                    bytesize_item_delta = -get_bytesize(opportunities['items'][item['id']])
                del(opportunities['items'][item['id']])

            if (log_memory):
                sum_bytesize_item_deltas += bytesize_item_delta
                if (verbose):
                    print(f"Item ID: {item['id']}; Bytesize item delta: {bytesize_item_delta}; Sum of bytesize item deltas: {sum_bytesize_item_deltas}")

    if (    ('next' in feed_page.json().keys())
        and (type(feed_page.json()['next']) == str)
        and (len(feed_page.json()['next']) > 0)
    ):
        opportunities['next_url'] = get_opportunities_next_url(feed_page.json()['next'], opportunities)
    else:
        opportunities['next_url'] = ''

    if (opportunities['next_url'] != feed_url):
        opportunities['num_urls'] += 1

    get_opportunities_helper_done = opportunities['next_url'] in [feed_url, '']

    if (log_memory):
        return opportunities, get_opportunities_helper_done, sum_bytesize_item_deltas
    else:
        return opportunities, get_opportunities_helper_done

# --------------------------------------------------------------------------------------------------

def get_opportunities_next_url(next_url_original, opportunities):
    next_url = ''

    next_url_original_unquoted = unquote(next_url_original)
    next_url_original_parsed = urlparse(next_url_original_unquoted)

    if (    (next_url_original_parsed.scheme != '')
        and (next_url_original_parsed.netloc != '')
    ):
        if (opportunities['num_urls'] == 0):
            opportunities['first_url_origin'] = '://'.join([next_url_original_parsed.scheme, next_url_original_parsed.netloc])
        next_url = next_url_original_unquoted
    elif (  (next_url_original_parsed.path != '')
        or  (next_url_original_parsed.query != '')
    ):
        next_url = opportunities['first_url_origin']
        if (next_url_original_parsed.path != ''):
            next_url += ('/' if (next_url_original_parsed.path[0] != '/') else '') + next_url_original_parsed.path
        if (next_url_original_parsed.query != ''):
            next_url += ('?' if (next_url_original_parsed.query[0] != '?') else '') + next_url_original_parsed.query

    return next_url

# --------------------------------------------------------------------------------------------------

def get_bytesize(arg):
    bytesize = 0

    if (type(arg) == list):
        bytesize = sum([get_bytesize(val) for val in arg])
    elif (type(arg) == dict):
        bytesize = sum([get_bytesize(val) for val in arg.values()])
    else:
        bytesize = getsizeof(arg)

    return bytesize

# --------------------------------------------------------------------------------------------------

def get_item_kinds(opportunities):
    item_kinds = {}

    for item in opportunities['items'].values():
        item_kind = None

        if ('kind' in item.keys()):
            item_kind = item['kind']

        if (item_kind not in item_kinds.keys()):
            item_kinds[item_kind] = 1
        else:
            item_kinds[item_kind] += 1

    return item_kinds

# --------------------------------------------------------------------------------------------------

def get_item_types(opportunities):
    item_types = {}

    for item in opportunities['items'].values():
        item_type = None

        if ('data' in item.keys()):
            if ('type' in item['data'].keys()):
                item_type = item['data']['type']
            elif ('@type' in item['data'].keys()):
                item_type = item['data']['@type']

        if (item_type not in item_types.keys()):
            item_types[item_type] = 1
        else:
            item_types[item_type] += 1

    return item_types

# --------------------------------------------------------------------------------------------------

superevent_labels = \
        ['SessionSeries'] \
    +   ['FacilityUse', 'IndividualFacilityUse'] \
    +   ['EventSeries'] \
    +   ['league']
subevent_labels = \
        ['ScheduledSession', 'ScheduledSessions', 'Session', 'Sessions', 'session', 'sessions', 'ScheduledSession.SessionSeries'] \
    +   ['Slot', 'Slot for FacilityUse', 'FacilityUse/Slot', 'FacilityUse.Slot', 'IndividualFacilityUse/Slot', 'IndividualFacilityUse.Slot'] \
    +   ['Event', 'event', 'HeadlineEvent', 'OnDemandEvent'] \
    +   ['CourseInstance']

def get_event_type(label):
    if (label in superevent_labels):
        return 'superevent'
    elif (label in subevent_labels):
        return 'subevent'
    else:
        return None

# --------------------------------------------------------------------------------------------------

def get_superevents(subevent, superevent_opportunities, skip_superevent_ids=[]):
    superevents = []

    subevent_superevent_modified_id = get_subevent_superevent_modified_id(subevent)

    if (subevent_superevent_modified_id is not None):
        for superevent_id, superevent in superevent_opportunities['items'].items():
            if (superevent_id not in skip_superevent_ids):
                superevent_modified_ids = get_item_modified_ids(superevent)
                if (subevent_superevent_modified_id in superevent_modified_ids):
                    superevents.append(superevent)

    return superevents

# --------------------------------------------------------------------------------------------------

def get_subevents(superevent, subevent_opportunities, skip_subevent_ids=[]):
    subevents = []

    superevent_modified_ids = get_item_modified_ids(superevent)

    if (any(superevent_modified_ids)):
        for subevent_id, subevent in subevent_opportunities['items'].items():
            if (subevent_id not in skip_subevent_ids):
                subevent_superevent_modified_id = get_subevent_superevent_modified_id(subevent)
                if (    (subevent_superevent_modified_id is not None)
                    and (subevent_superevent_modified_id in superevent_modified_ids)
                ):
                    subevents.append(subevent)

    return subevents

# --------------------------------------------------------------------------------------------------

def get_superevent_id_v_subevent_ids(superevent_opportunities, subevent_opportunities, **kwargs):
    verbose = kwargs.get('verbose', False)

    if (verbose):
        print(stack()[0].function)

    superevent_modified_id_v_superevent_id = {}
    superevent_data_modified_id_v_superevent_id = {}
    subevent_id_v_subevent_superevent_modified_id = {}
    superevent_id_v_subevent_ids = {}

    # --------------------------------------------------------------------------------------------------

    num_superevents = len(superevent_opportunities['items'].keys())
    num_subevents = len(subevent_opportunities['items'].keys())

    if (    (num_superevents == 0)
        or  (num_subevents == 0)
    ):
        if (    (num_superevents == 0)
            and (num_subevents > 0)
        ):
            print('\tNo superevents - merging not possible')
        elif (  (num_superevents > 0)
            and (num_subevents == 0)
        ):
            print('\tNo subevents - merging not possible')
        elif (  (num_superevents == 0)
            and (num_subevents == 0)
        ):
            print('\tNo superevents and no subevents - merging not possible')
        return superevent_id_v_subevent_ids

    # --------------------------------------------------------------------------------------------------

    # superevent_id is identical to how it appears in a feed and its opportunities dictionary, and can be a string or an integer.
    # superevent_modified_id and superevent_data_modified_id are both strings.

    if (verbose):
        print('\tDetermining superevent modified IDs for superevents:')
    for idx, (superevent_id, superevent) in enumerate(superevent_opportunities['items'].items()):
        superevent_modified_id, superevent_data_modified_id = get_item_modified_ids(superevent)
        if (superevent_modified_id is not None):
            superevent_modified_id_v_superevent_id[superevent_modified_id] = superevent_id
        if (superevent_data_modified_id is not None):
            superevent_data_modified_id_v_superevent_id[superevent_data_modified_id] = superevent_id
        if (    (verbose)
            and ((num_superevents <= 10) or ((idx + 1) % 10 == 0) or (idx == num_superevents - 1))
        ):
            print(f"\t\t{datetime.now()} {idx+1}/{num_superevents} superevents processed", end=('\r' if (idx < num_superevents - 1) else '\n'))

    # --------------------------------------------------------------------------------------------------

    # subevent_id is identical to how it appears in a feed and its opportunities dictionary, and can be a string or an integer.
    # subevent_superevent_modified_id is a string.

    if (verbose):
        print('\tDetermining superevent modified IDs for subevents:')
    for idx, (subevent_id, subevent) in enumerate(subevent_opportunities['items'].items()):
        subevent_superevent_modified_id = get_subevent_superevent_modified_id(subevent)
        if (subevent_superevent_modified_id is not None):
            subevent_id_v_subevent_superevent_modified_id[subevent_id] = subevent_superevent_modified_id
        if (    (verbose)
            and ((num_subevents <= 10) or ((idx + 1) % 10 == 0) or (idx == num_subevents - 1))
        ):
            print(f"\t\t{datetime.now()} {idx+1}/{num_subevents} subevents processed", end=('\r' if (idx < num_subevents - 1) else '\n'))

    num_subevents_with_superevent_modified_id = len(subevent_id_v_subevent_superevent_modified_id.keys())

    if (num_subevents_with_superevent_modified_id == 0):
        if (verbose):
            print('\t\tNo subevents with superevent modified ID - merging not possible')
        return superevent_id_v_subevent_ids

    # --------------------------------------------------------------------------------------------------

    # Search for matching modified superevent IDs (which are always strings and so can always be compared)
    # between superevents and subevents, and use to make lists of subevent IDs corresponding to unmodified
    # superevent IDs (both of which may be strings or integers, the same as how they appear in a feed and
    # its opportunities dictionary).

    if (verbose):
        print('\tDetermining subevent IDs for superevents:')
    for idx, (subevent_id, subevent_superevent_modified_id) in enumerate(subevent_id_v_subevent_superevent_modified_id.items()):
        superevent_id = None
        if (subevent_superevent_modified_id in superevent_modified_id_v_superevent_id.keys()):
            superevent_id = superevent_modified_id_v_superevent_id[subevent_superevent_modified_id]
        elif (subevent_superevent_modified_id in superevent_data_modified_id_v_superevent_id.keys()):
            superevent_id = superevent_data_modified_id_v_superevent_id[subevent_superevent_modified_id]
        if (superevent_id is not None):
            if (superevent_id not in superevent_id_v_subevent_ids.keys()):
                superevent_id_v_subevent_ids[superevent_id] = []
            superevent_id_v_subevent_ids[superevent_id].append(subevent_id)
        if (    (verbose)
            and ((num_subevents_with_superevent_modified_id <= 10) or ((idx + 1) % 10 == 0) or (idx == num_subevents_with_superevent_modified_id - 1))
        ):
            print(f"\t\t{datetime.now()} {idx+1}/{num_subevents_with_superevent_modified_id} subevents with superevent modified ID processed", end=('\r' if (idx < num_subevents_with_superevent_modified_id - 1) else '\n'))

    num_superevents_with_subevent_ids = len(superevent_id_v_subevent_ids.keys())

    if (num_superevents_with_subevent_ids == 0):
        if (verbose):
            print('\t\tNo superevents with subevent IDs - merging not possible')
        return superevent_id_v_subevent_ids

    # --------------------------------------------------------------------------------------------------

    return superevent_id_v_subevent_ids

# --------------------------------------------------------------------------------------------------

def get_subevent_superevent_modified_id(subevent):
    subevent_superevent_modified_id = None

    if ('data' in subevent.keys()):
        for key in ['superEvent', 'facilityUse']:
            if (    (key in subevent['data'].keys())
                and (type(subevent['data'][key]) in [str, int])
            ):
                subevent_superevent_modified_id = str(subevent['data'][key]).split('/')[-1]
                break

    return subevent_superevent_modified_id

# --------------------------------------------------------------------------------------------------

def get_item_modified_ids(item):
    item_modified_id = None
    item_data_modified_id = None

    for key in ['id', '@id']:
        if (    (key in item.keys())
            and (type(item[key]) in [str, int])
        ):
            item_modified_id = str(item[key]).split('/')[-1]
            break

    if ('data' in item.keys()):
        for key in ['id', '@id']:
            if (    (key in item['data'].keys())
                and (type(item['data'][key]) in [str, int])
            ):
                item_data_modified_id = str(item['data'][key]).split('/')[-1]
                break

    return item_modified_id, item_data_modified_id