<img src='https://openactive.io/brand-assets/openactive-logo-large.png' width='500'>

[![License](http://img.shields.io/:license-mit-blue.svg)](https://opensource.org/license/mit/)

This is a Python package for reading feeds of sports and activity data published in the OpenActive format. Note that this is an experimental package, and although care has been taken to cater for many typical OpenActive situations, there may still be those that don't work as expected. It is therefore recommended to not directly use this package for critical pipelines or automations, but to treat it as a toolset for exploration and education. The underlying code is relatively short and can be consulted for informing your own approach if needed.

# Installation

It is recommended to first set up a virtual environment for your `openactive` project, to ensure that it's isolated from your base environment and runs as intended. The only thing that must be installed in your base environment is some package for generating virtual environments, such as `virtualenv`:

```
$ pip install virtualenv
```

Then, in a new project folder, create and initialise a new virtual environment as follows (`virt` and `venv` are typical names, but you can choose something else if needed):

```
$ virtualenv virt
$ source virt/bin/activate
(virt) $
```

Now install the `openactive` package in the virtual environment, and you're good to go:

```
(virt) $ pip install openactive
```

When you're done working in the virtual environment, deactivate it by:

```
(virt) $ deactivate
```

# Usage

In a Python session running in an environment with the `openactive` package installed, let's import the package under the proxy name `oa`:

```
>>> import openactive as oa
```

In order to effectively use the package, we must first understand the OpenActive ecosystem. OpenActive data is decentralised, so there is no single owner or location that stores and serves the data. Instead, data is released by multiple data publishers as separate Realtime Paged Data Exchange (RPDE) feeds, which are described in more detail later. There can also be multiple feeds from a given publisher, and in fact we often have complimentary pairs of feeds, such as having one for super-event data (e.g. various series of fitness classes) and one for sub-event data (e.g. various sessions in the various series). In such cases, both feeds must be read in order to get a complete picture, and items in one feed will reference items in the other feed. The alternative to this would be to copy each super-event data item into each associated sub-event data item, resulting in one feed with a lot of duplication.

A group of feeds from a data publisher is bundled together in a "dataset", a group of datasets from different data publishers is bundled together in a "catalogue", and a group of catalogues is bundled together in a "collection". There is only one collection, which is therefore the starting point for everything else. Given a list of all feed information, you will not often want to see the exact path by which the information was gathered, but there are functions in the `openactive` package that break down the journey from the source collection if needed. So let's just start at the very beginning to be clear on how things work. First, let's define a printer function to give us a clear indented output display for what follows:

```
>>> import json
>>> def printer(arg):
...     print(json.dumps(arg,indent=4))
```

## Get feeds

Now let's get the catalogue URLs in the collection, which should take about a second:

```
>>> catalogue_urls = oa.get_catalogue_urls()
>>> printer(catalogue_urls)
{
    "https://openactive.io/data-catalogs/data-catalog-collection.jsonld": [
        "https://opendata.leisurecloud.live/api/datacatalog",
        "https://openactivedatacatalog.legendonlineservices.co.uk/api/DataCatalog",
        "https://openactive.io/data-catalogs/singular.jsonld",
        "https://app.bookteq.com/api/openactive/catalogue"
    ]
}
```

We see that this returns a dictionary with a single key, the collection URL, which has a value that is the list of catalogue URLs. Unless otherwise stated, all data gathering functions have two optional boolean keywords which weren't used above. The first keyword is `flat`, which causes a function to return a flat list structure rather than a dictionary, so losing the key-level information. The second keyword is `verbose`, which causes a function to print its name and the URLs that it calls during execution. Note that, regardless of the `verbose` keyword, warning and error messages are printed as standard, and we typically have such messages when a page to be read is unavailable or not set up correctly. Let's run the above again with both keywords set to `True`:

```
>>> catalogue_urls = oa.get_catalogue_urls(flat=True, verbose=True)
get_catalogue_urls
CALLING: https://openactive.io/data-catalogs/data-catalog-collection.jsonld
>>> printer(catalogue_urls)
[
    "https://opendata.leisurecloud.live/api/datacatalog",
    "https://openactivedatacatalog.legendonlineservices.co.uk/api/DataCatalog",
    "https://openactive.io/data-catalogs/singular.jsonld",
    "https://app.bookteq.com/api/openactive/catalogue"
]
```

Now for each of these catalogue URLs let's get the dataset URLs they contain, which should take a few seconds. Note that `get_dataset_urls` calls `get_catalogue_urls` internally, the above was just for illustration of the process:

```
Note: Output is truncated at 'etc.'

>>> dataset_urls = oa.get_dataset_urls()
>>> printer(dataset_urls)
{
    "https://opendata.leisurecloud.live/api/datacatalog": [
        "https://activeleeds-oa.leisurecloud.net/OpenActive/",
        etc.
    ],
    "https://openactivedatacatalog.legendonlineservices.co.uk/api/DataCatalog": [
        "https://halo-openactive.legendonlineservices.co.uk/OpenActive",
        etc.
    ],
    "https://openactive.io/data-catalogs/singular.jsonld": [
        "http://data.better.org.uk/",
        etc.
    ],
    "https://app.bookteq.com/api/openactive/catalogue": [
        "https://actihire.bookteq.com/api/open-active",
        etc.
    ]
}
```

We again see an output dictionary, with keys that are catalogue URLs and values that are lists of dataset URLs. The above output display is truncated, and you will see many more dataset URLs if you run the command yourself.

Now for each of these dataset URLs let's get the feed information they contain, which should take a couple of minutes. Note that `get_feeds` calls `get_dataset_urls` internally, the above was just for illustration of the process:

```
Note: Output is truncated at 'etc.'

>>> feeds = oa.get_feeds()
WARNING: Retrying (1/9): https://gll-openactive.legendonlineservices.co.uk/OpenActive
WARNING: Retrying (1/9): https://sllandinspireall-openactive.legendonlineservices.co.uk/OpenActive
WARNING: Retrying (1/9): https://data.bookwhen.com/
WARNING: Retrying (2/9): https://data.bookwhen.com/
WARNING: Retrying (3/9): https://data.bookwhen.com/
WARNING: Retrying (4/9): https://data.bookwhen.com/
WARNING: Retrying (5/9): https://data.bookwhen.com/
WARNING: Retrying (6/9): https://data.bookwhen.com/
WARNING: Retrying (7/9): https://data.bookwhen.com/
WARNING: Retrying (8/9): https://data.bookwhen.com/
WARNING: Retrying (9/9): https://data.bookwhen.com/
WARNING: Max. tries (10) reached for: https://data.bookwhen.com/
ERROR: Can't get dataset: https://data.bookwhen.com/
ERROR: Can't get dataset: https://www.participant.co.uk/participant/openactive/
>>> printer(feeds)
{
    "https://activeleeds-oa.leisurecloud.net/OpenActive/": [
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "CourseInstance",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-course-instance",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        },
        etc.
    ],
    "https://brimhamsactive.gs-signature.cloud/OpenActive/": [
        {
            "name": "Brimhams Active Sessions and Facilities",
            "type": "CourseInstance",
            "url": "https://opendata.leisurecloud.live/api/feeds/BrimhamsActive-live-course-instance",
            "datasetUrl": "https://brimhamsactive.gs-signature.cloud/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Brimhams Active"
        },
        etc.
    ],
    etc.
}
```

Once again we see an output dictionary, with keys that are dataset URLs and values that are lists of feed information dictionaries. The above output display is truncated, and you will see many more feed information dictionaries if you run the command yourself. Also note the warning messages in the above, which, as mentioned previously, occur if a URL cannot be correctly accessed due to some issue. The `openactive` package will automatically retry a problematic URL up to 10 times with a 1 second wait time between tries, and these defaults can be overridden via the `num_tries_max` and `seconds_wait_retry` keywords, respectively. Additionally there is a default wait time of 0.2 seconds between subsequent URLs being called in a list even if no issue occurs, to ensure that servers aren't overburdened with an unrestricted call rate, and this default can be overridden via the `seconds_wait_next` keyword. Any of these keywords can be given to any data gathering function and they will be passed through to other data gathering functions they call internally. So, for example, the `get_feeds` function could be called as follows, which will adjust the settings not only for the `get_feeds` function itself but also for the `get_dataset_urls` function and the `get_catalogue_urls` function which are internally called in a chain:

```
>>> feeds = oa.get_feeds(seconds_wait_next=0.4, seconds_wait_retry=2, num_tries_max=5)
```

The list of all feed information is usually where you'll want to start your project work, but it's useful to be aware of the full journey illustrated above in getting to this point.

## Get opportunities

What we ultimately want to work with is the activity "opportunity" data served via a given feed starting URL, which is the entry point for data transferred via Realtime Paged Data Exchange (RPDE). In essence, this is just like what we have returned from a search engine, which breaks result items over a chain of pages rather than showing them all on a single page. As described earlier, feeds often come in pairs for efficiency of data storage and delivery, with one feed for super-event data and one feed for sub-event data. Inspecting the full output from the `get_feeds` function, we have the following for the first dataset:

```
Note: Output is truncated at 'etc.'

>>> printer(feeds)
{
    "https://activeleeds-oa.leisurecloud.net/OpenActive/": [
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "CourseInstance",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-course-instance",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        },
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "SessionSeries",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        },
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "ScheduledSession",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        },
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "FacilityUse",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-facility-uses",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        },
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "Slot",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-slots",
            "datasetUrl": "https://activeleeds-oa.leisurecloud.net/OpenActive/",
            "discussionUrl": "",
            "licenseUrl": "https://creativecommons.org/licenses/by/4.0/",
            "publisherName": "Active Leeds"
        }

    ],
    etc.
}
```

Extracting the feed starting URLs for this dataset, we have:

```
>>> feed_urls = [feed['url'] for feed in feeds['https://activeleeds-oa.leisurecloud.net/OpenActive/']]
>>> printer(feed_urls)
[
    "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-course-instance",
    "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series",
    "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions",
    "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-facility-uses",
    "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-slots"
]
```

To help automate workflows, there is a function called `get_partner_feed_url` that takes a single feed starting URL to find a partner for, and a list of feed starting URLs in which there may be a partner. It's a simple search-and-replace function using typical URL parts and their variants, such as swapping `session-series` or `sessionseries` for `scheduled-sessions` or `scheduledsessions`, until a match is found. If no match is found, then `None` is returned instead. Looping through the list of feed starting URLs for the above dataset, and using the list itself as the set of matching options, we have:

```
>>> for feed_url in feed_urls:
...     partner_feed_url = oa.get_partner_feed_url(feed_url, feed_urls)
...     print('Feed-1 URL:', feed_url)
...     print('Feed-2 URL:', partner_feed_url, '\n')
...
Feed-1 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-course-instance
Feed-2 URL: None

Feed-1 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series
Feed-2 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions

Feed-1 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions
Feed-2 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series

Feed-1 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-facility-uses
Feed-2 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-slots

Feed-1 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-slots
Feed-2 URL: https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-facility-uses
```

The `course-instance` feed is the only standalone feed in this case, with the remaining four feeds being two pairs, namely the `session-series` super-event feed with the `scheduled-sessions` sub-event feed, and the `facility-uses` super-event feed with the `slots` sub-event feed. Note that it doesn't matter if the single feed starting URL provided to `get_partner_feed_url` is for a super-event feed or a sub-event feed, it will find whatever partner URL matches.

Let's look at the paired `session-series` and `scheduled-sessions` feeds from the above dataset. As mentioned, a feed consists of a list of opportunity items split over a number of pages. Some items are in fact not live and are marked as deleted, and some items may supersede other items with more up-to-date values. To get all of the data for a given feed, we must visit each page one-by-one and retain only the most up-to-date live items, which is done by the `get_opportunities` function. Note that the number of pages in a given feed is not known in advance, and so the time required to read all associated pages can vary greatly between one feed and another, from a number of seconds to a number of minutes. The `verbose` keyword may be particularly useful here to monitor progress. The feeds in this example should only take a few seconds each:

```
>>> superevent_opportunities = oa.get_opportunities('https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series')
>>> subevent_opportunities = oa.get_opportunities('https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions')
```

For the super-event data we have:

```
Note: Output is truncated at 'etc.'

>>> printer(superevent_opportunities)
{
    "items": {
        "HO1ONDL23501021": {
            "id": "HO1ONDL23501021",
            "modified": 14554552,
            "kind": "SessionSeries",
            "state": "updated",
            "data": {
                "@context": [
                    "https://openactive.io/",
                    "https://openactive.io/ns-beta"
                ],
                "@type": "SessionSeries",
                "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/session-series/HO1ONDL23501021",
                etc.
            }
        },
        etc.
    },
    "urls": [
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series",
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series?afterTimestamp=24571209&afterId=SH5CLPI13300124"
    ],
    "firstUrlOrigin": "https://opendata.leisurecloud.live",
    "nextUrl": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series?afterTimestamp=26002956&afterId=KL2CLPL11001121"
}
```

For the sub-event data we have:

```
Note: Output is truncated at 'etc.'

>>> printer(subevent_opportunities)
{
    "items": {
        "00000000000170005743": {
            "id": "00000000000170005743",
            "modified": 34213402,
            "kind": "ScheduledSession",
            "state": "updated",
            "data": {
                "@context": [
                    "https://openactive.io/",
                    "https://openactive.io/ns-beta"
                ],
                "@type": "ScheduledSession",
                "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/scheduled-sessions/170005743",
                etc.
            }
        },
        etc.
    }
    "urls": [
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions",
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions?afterTimestamp=34383479&afterId=00000000000060031844",
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions?afterTimestamp=34385051&afterId=00000000000130035754",
        "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions?afterTimestamp=34386561&afterId=00000000000010053619"
    ],
    "firstUrlOrigin": "https://opendata.leisurecloud.live",
    "nextUrl": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions?afterTimestamp=34387745&afterId=00000000000080031177"
}
```

The returned outputs are, once again, in dictionary form, and the main content of interest is found under the `items` key. The above output display is truncated, and you will see many more items if you run the command yourself. This output cannot be flattened via the `flat` keyword, as its structure is essential to maintain for potential later use. All URLs that were visited in the feed chain are also returned in the output, as well as the first URL "origin" component, and the next URL to be visited when the feed is updated by the publisher, in order to continue the read at this point in the feed chain at a later time. To do this, which can also be done if we encounter an issue and only receive output from a partial read of the feed chain, we give the output dictionary to the function as argument rather than the feed starting URL. Using the super-event feed to illustrate, we would do:

```
>>> superevent_opportunities_new = oa.get_opportunities(superevent_opportunities)
```

## Assess opportunities

After obtaining a set of opportunity items, we can scan through all of them and count the various "kind" and "type" values that appear, using the functions `get_item_kinds` and `get_item_data_types`. Usually there is only one kind and one type for a given feed, and usually these are the same as each other too, but there can be differences and this is useful to keep in mind. Let's take a look for the opportunities obtained above.

For the super-event data we have:

```
>>> len(superevent_opportunities['items'].keys())
916
>>> printer(oa.get_item_kinds(superevent_opportunities))
{
    "SessionSeries": 916
}
>>> printer(oa.get_item_data_types(superevent_opportunities))
{
    "SessionSeries": 916
}
```

For the sub-event data we have:

```
>>> len(subevent_opportunities['items'].keys())
1476
>>> printer(oa.get_item_kinds(subevent_opportunities))
{
    "ScheduledSession": 1476
}
>>> printer(oa.get_item_data_types(subevent_opportunities))
{
    "ScheduledSession": 1476
}
```

In this case, all 916 super-event items have a kind and a type of `SessionSeries`, and all 1476 sub-event items have a kind and a type of `ScheduledSession`. So it's safe to say that these are pure feeds of only one of the OpenActive data variants each, and we can treat them as such in further analysis. Note that you will likely see different values to the above if you're following through, as OpenActive feeds are dynamically changing.

Even though we have commented that the `SessionSeries` feed is super-event data and the `ScheduledSession` feed is sub-event data, these judgements were made simply by observation and knowledge of the OpenActive data model. In order to automate an analysis that relies on knowing whether we're dealing with super-event data or sub-event data, the `get_event_type` function is useful. This takes an item kind or type label and returns `'superevent'`, `'subevent'` or `None`, accordingly:

```
>>> oa.get_event_type('SessionSeries')
'superevent'
>>> oa.get_event_type('ScheduledSession')
'subevent'
>>> oa.get_event_type('blah')
>>> oa.get_event_type('blah') is None
True
```

Finally, let's look at the relationship between the items in a pair of super-event and sub-event feeds. For any single sub-event item, there will be a single related super-event item i.e. a single class belongs to a single series of classes. For any single super-event item, there will be a number of related sub-event items i.e. a single series of classes has a number of classes. The functions `get_superevents` and `get_subevents` help with these two situations, respectively. Let's take a look at each in turn. First, let's observe a single sub-event item from the full list of sub-event items:

```
>>> printer(list(subevent_opportunities['items'].values())[0])
{
    "id": "00000000000170005743",
    "modified": 34213402,
    "kind": "ScheduledSession",
    "state": "updated",
    "data": {
        "@context": [
            "https://openactive.io/",
            "https://openactive.io/ns-beta"
        ],
        "@type": "ScheduledSession",
        "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/scheduled-sessions/170005743",
        "startDate": "2024-02-23T10:00:00+00:00",
        "identifier": 170005743,
        "endDate": "2024-02-23T11:00:00+00:00",
        "superEvent": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/session-series/WE5CLKM10000723",
        "duration": "PT1H",
        "maximumAttendeeCapacity": 20,
        "remainingAttendeeCapacity": 0,
        "beta:sportsActivityLocation": [
            {
                "@type": "SportsActivityLocation",
                "name": "Activity Room"
            }
        ]
    }
}
```

Note that there is a field called "superEvent" in the above, the value of which contains what looks like a unique ID, namely "WE5CLKM10000723". We can see that this exists within the full list of super-event items:

```
>>> 'WE5CLKM10000723' in superevent_opportunities['items'].keys()
True
```

Now let's select that super-event item itself, by giving the sub-event item and the full list of super-event items to `get_superevents`:

```
Note: Output is truncated at 'etc.'

>>> superevent_opportunities_selection = oa.get_superevents(
...     list(subevent_opportunities['items'].values())[0],
...     superevent_opportunities
... )
>>> printer(superevent_opportunities_selection)
[
    {
        "id": "WE5CLKM10000723",
        "modified": 34053122,
        "kind": "SessionSeries",
        "state": "updated",
        "data": {
            "@context": [
                "https://openactive.io/",
                "https://openactive.io/ns-beta"
            ],
            "@type": "SessionSeries",
            "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/session-series/WE5CLKM10000723",
            "eventSchedule": [
                {
                    "@type": "PartialSchedule",
                    "byDay": [
                        "https://schema.org/Friday"
                    ],
                    "duration": "PT1H",
                    "endTime": "11:00",
                    "startDate": "2023-07-21",
                    "endDate": "2025-02-14",
                    "startTime": "10:00"
                }
            ],
            "identifier": "WE5CLKM10000723",
            "name": "Keep Moving",
            "attendeeInstructions": "Low level, low impact exercise for people with health conditions that want to become more active and improve their wellbeing",
            etc.
        }
    }
]
```

Note that the super-event ID we identified in the sub-event item appears in both the "id" and "data:@id" fields of the super-event item itself. The unique part of "id" and "data:@id" should be the same for a given super-event item, and all super-event items should be different in this respect, so there should be only one super-event for a given sub-event, as mentioned. However, hypothetically this may not always be so in spurious cases, and the output from `get_superevents` is a list which could contain more than one item if multiple matches are indeed found. It is worth checking that there is only one item in the list before any further analysis is done, and, if not, then establishing exactly why not.

Now let's go the other way around, from a given super-event item to a group of sub-event items. We can use the single super-event item as found above:

```
>>> subevent_opportunities_selection = oa.get_subevents(
...     superevent_opportunities_selection[0],
...     subevent_opportunities
... )
>>> printer(subevent_opportunities_selection)
[
    {
        "id": "00000000000170005743",
        "modified": 34213402,
        "kind": "ScheduledSession",
        "state": "updated",
        "data": {
            "@context": [
                "https://openactive.io/",
                "https://openactive.io/ns-beta"
            ],
            "@type": "ScheduledSession",
            "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/scheduled-sessions/170005743",
            "startDate": "2024-02-23T10:00:00+00:00",
            "identifier": 170005743,
            "endDate": "2024-02-23T11:00:00+00:00",
            "superEvent": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/session-series/WE5CLKM10000723",
            "duration": "PT1H",
            "maximumAttendeeCapacity": 20,
            "remainingAttendeeCapacity": 0,
            "beta:sportsActivityLocation": [
                {
                    "@type": "SportsActivityLocation",
                    "name": "Activity Room"
                }
            ]
        }
    },
    {
        "id": "00000000000170005744",
        "modified": 34365346,
        "kind": "ScheduledSession",
        "state": "updated",
        "data": {
            "@context": [
                "https://openactive.io/",
                "https://openactive.io/ns-beta"
            ],
            "@type": "ScheduledSession",
            "@id": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/scheduled-sessions/170005744",
            "startDate": "2024-03-01T10:00:00+00:00",
            "identifier": 170005744,
            "endDate": "2024-03-01T11:00:00+00:00",
            "superEvent": "https://activeleeds-oa.leisurecloud.net/OpenActive/api/session-series/WE5CLKM10000723",
            "duration": "PT1H",
            "maximumAttendeeCapacity": 20,
            "remainingAttendeeCapacity": 10,
            "beta:sportsActivityLocation": [
                {
                    "@type": "SportsActivityLocation",
                    "name": "Activity Room"
                }
            ]
        }
    }
]
```

We have a list of two sub-event items, one of which was the original input to `get_superevents`, as expected, and the other is the only other sub-event in the same super-event series. Such a list could contain many more items, but the above provides a complete and compact full example.

The functions for assessing opportunities described in this section are a good starting point for further analysis, providing the user with a set of tools to find basic but important information about feed content. The user can then more confidently work with that content, including automations that may depend on knowing the item kind or type, and whether or not those labels indicate a pure super-event feed or sub-event feed.

## Function summary

The following table summarises the inputs and outputs of all functions described above:

Function|Input|Output (not using `flat`)
:---|:---|:---
`get_catalogue_urls`|-|dict: catalogue URLs in the collection
`get_dataset_urls`|-|dict: dataset URLs for each catalogue
`get_feeds`|-|dict: feed info for each dataset
`get_partner_feed_url`|str: `feed1_url`<br>and<br>[str]: [`feed2_url_options`]|str: `feed2_url` that best partners with `feed1_url`
`get_opportunities`|str: `feed_url`<br>or<br>dict: `opportunities`|dict: `opportunities` info for a given feed
`get_item_kinds`|dict: `opportunities`|dict: Item kinds and counts
`get_item_data_types`|dict: `opportunities`|dict: Item data types and counts
`get_event_type`|str: item kind<br>or<br>str: item data type|str: "superevent" or "subevent"<br>or<br>None
`get_superevents`|dict: sub-event item<br>and<br>dict: super-event `opportunities`|[dict]: [super-event items]
`get_subevents`|dict: super-event item<br>and<br>dict: sub-event `opportunities`|[dict]: [sub-event items]

Additionally, the data gathering functions accept the following keywords:

Function|`flat`<br>bool|`verbose`<br>bool|`seconds_wait_next`<br>num|`seconds_wait_retry`<br>num|`num_tries_max`<br>int
:---|:---|:---|:---|:---|:---
`get_catalogue_urls`|&#10003;|&#10003;|&#10007;|&#10003;|&#10003;
`get_dataset_urls`|&#10003;|&#10003;|&#10003;|&#10003;|&#10003;
`get_feeds`|&#10003;|&#10003;|&#10003;|&#10003;|&#10003;
`get_opportunities`|&#10007;|&#10003;|&#10003;|&#10003;|&#10003;

# References

The main locations:
- [Initiative homepage](https://openactive.io/)
- [Developer homepage](https://developer.openactive.io/)
- [GitHub](https://github.com/openactive)

The complete set of OpenActive specifications:
- [Realtime Paged Data Exchange (RPDE) data transfer protocol](https://openactive.io/realtime-paged-data-exchange/EditorsDraft/)
- [Opportunity data primer](https://openactive.io/opportunity-data-primer/)
- [Opportunity data model](https://openactive.io/modelling-opportunity-data/EditorsDraft/)
- [Dataset model](https://openactive.io/dataset-api-discovery/EditorsDraft/)
- [Route model](https://openactive.io/route-guide/EditorsDraft/)
- [Booking system model](https://openactive.io/open-booking-api/EditorsDraft/1.0CR3/)

Tools:
- [Feed status](https://status.openactive.io/)
- [Data visualiser](https://visualiser.openactive.io/) - for those curious about the data and for data publishers checking their feed quality
- [Data validator](https://validator.openactive.io/) - a more involved tool for drilling into feed details and checking content

Community and communications:
- [W3C](https://w3c.openactive.io/)
- [Slack](https://slack.openactive.io/)
- [LinkedIn](https://www.linkedin.com/company/openactiveio/)
- [Twitter](https://twitter.com/openactiveio)
- [Medium](https://openactiveio.medium.com/)
- [YouTube](https://www.youtube.com/@openactive)