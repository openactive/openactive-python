<img src='https://openactive.io/brand-assets/openactive-logo-large.png' width='500'>

[![License](http://img.shields.io/:license-mit-blue.svg)](https://opensource.org/license/mit/)

This is a Python package for reading feeds of sports and activity data published in the OpenActive format.

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

In order to effectively use the package, we must first understand the OpenActive data model. OpenActive data is released by a data publisher as a Realtime Paged Data Exchange (RPDE) feed, which is described in more detail later. There can be multiple feeds from a given publisher, and in fact we often have complimentary pairs of feeds, such as having one for super-event data (e.g. a series of fitness class sessions) and one for sub-event data (e.g. particular scheduled sessions in the series). In such cases, both feeds must be read in order to get a complete picture, and items in one feed will reference items in the other feed. The alternative to this would have been a system that only has one feed for all of this data, with the super-event data copied into every item in the sub-event data, which would be a lot of duplication.

A group of feeds from a data publisher is bundled together in a "dataset", a group of datasets from different data publishers is bundled together in a "catalogue", and a group of catalogues is bundled together in a "collection". There is only one collection, which is therefore the starting point for everything else. Given a list of feed information, you will not often want to see the exact path by which the feeds were gathered, but there are functions in `openactive` that show the journey from the source collection if needed. So let's just start at the very beginning to be clear on how things work in the ecosystem. First, let's define a printer function to give us a clear indented output display for what follows:

```
>>> import json
>>> def printer(arg):
...     print(json.dumps(arg,indent=4))
```

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
>>> catalogue_urls = oa.get_catalogue_urls(flat=True,verbose=True)
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

Now for each of these catalogue URLs let's get the dataset URLs they contain, which should take a few seconds (note that `get_dataset_urls` calls `get_catalogue_urls` internally):

```
>>> dataset_urls = oa.get_dataset_urls()
>>> printer(dataset_urls)
{
    "https://opendata.leisurecloud.live/api/datacatalog": [
        "https://activeleeds-oa.leisurecloud.net/OpenActive/",
        "https://brimhamsactive.gs-signature.cloud/OpenActive/",
        etc.
    ],
    "https://openactivedatacatalog.legendonlineservices.co.uk/api/DataCatalog": [
        "https://halo-openactive.legendonlineservices.co.uk/OpenActive",
        "https://blackburnwithdarwen-openactive.legendonlineservices.co.uk/OpenActive",
        etc.
    ],
    "https://openactive.io/data-catalogs/singular.jsonld": [
        "http://data.better.org.uk/",
        "https://data.bookwhen.com/",
        etc.
    ],
    "https://app.bookteq.com/api/openactive/catalogue": [
        "https://actihire.bookteq.com/api/open-active",
        "https://awesomecic.bookteq.com/api/open-active",
        etc.
    ]
}
```

We again see an output dictionary, with keys that are catalogue URLs and values that are lists of dataset URLs. The above output display is truncated, and you will see many more dataset URLs if you run the command yourself.

Now for each of these dataset URLs let's get the feed information they contain, which should take about a minute (note that `get_feeds` calls `get_dataset_urls` internally):

```
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
        {
            "name": "Active Leeds Sessions and Facilities",
            "type": "SessionSeries",
            "url": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series",
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
        {
            "name": "Brimhams Active Sessions and Facilities",
            "type": "SessionSeries",
            "url": "https://opendata.leisurecloud.live/api/feeds/BrimhamsActive-live-session-series",
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

Once again we see an output dictionary, with keys that are dataset URLs and values that are lists of feed information dictionaries. The above output display is truncated, and you will see many more feed information dictionaries if you run the command yourself.

The list of feeds is usually where you'll want to start your project work, but it's useful to be aware of the above journey in getting to this point, which internally happens automatically. What we ultimately want is the data served via a given starting feed URL, which is the entry point for data transferred via Realtime Paged Data Exchange (RPDE). In essence, this is just like what we have returned from a search engine, which breaks results over a chain of pages rather than showing them all on a single page. To get all of the data, we must visit each page in the chain one-by-one. This is done for us automatically by the next function in the series, so let's take a look at what we get for a given starting feed URL. Note that the time required for this function to complete can vary greatly depending on the feed being read, from a few seconds to a few minutes, and the `verbose` keyword may be particularly useful here to monitor progress. The feed in this example should only take a few seconds:

```
>>> opportunities = oa.get_opportunities('https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series')
>>> printer(opportunities)
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

The returned output is, once again, a dictionary. The main content of interest is found under the `items` key, which has a dictionary of "opportunity" items, these being the activity items for this particular feed, cleaned of those flagged for removal and older duplicates. The above output display is truncated, and you will see many more items if you run the command yourself. This output cannot be flattened via the `flat` keyword, as its structure is essential to maintain, but the `verbose` keyword is still applicable. All URLs that were visited in the feed chain are also returned in the output, as well as the "origin" of the first URL, and the next URL to be visited when the feed is updated by the publisher, in order to continue the read at this point in the feed chain at a later time. To do this, which can also be done if we encounter an issue and only receive output from a partial read of the feed chain, we give the output dictionary to the function as argument rather than the starting feed URL:

```
>>> opportunities_new = oa.get_opportunities(opportunities)
```

After obtaining a set of opportunity items, we can scan through all of them and count the various "kind" and "type" values that appear. Usually there is only one version of each of these fields, which are most often the same as each other too. Let's take a look for the opportunities obtained above:

```
>>> len(opportunities['items'])
919
>>> item_kinds = oa.get_item_kinds(opportunities)
>>> printer(item_kinds)
{
    "SessionSeries": 919
}
>>> item_data_types = oa.get_item_data_types(opportunities)
>>> printer(item_data_types)
{
    "SessionSeries": 919
}
```

We see that, in this case, all 919 items have a kind and a type of `SessionSeries`. So it's safe to say that this is a pure feed of one of the OpenActive data variants, and we can treat it as such in further analysis.

Finally, as mentioned above there are many cases in which a data publisher releases paired feeds in a dataset, one for super-event data and one for sub-event data. To help automate workflows, there is one more function in the `openactive` package that takes a single starting feed URL to find a partner for, and a list of starting feed URLs in which there may be a partner. It's a simple search-and-replace function using typical URL parts and their variants, such as swapping `session-series` or `sessionseries` for `scheduled-sessions` or `scheduledsessions`, until a match is found. If no match is found, then `None` is returned instead. Using the starting feed URL that we used to get the above `opportunities` dictionary, and the list of all starting feed URLs from the associated dataset in the `feeds` dictionary, we have:

```
>>> feed_url_1 = 'https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series'
>>> feed_url_2_options = [feed['url'] for feed in feeds['https://activeleeds-oa.leisurecloud.net/OpenActive/']]
>>> feed_url_2 = oa.get_partner_url(feed_url_1, feed_url_2_options)
>>> feed_url_2
'https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-scheduled-sessions'
```

As expected, for the super-event data (session series) we have a partner URL of sub-event data (scheduled sessions). We can now read in the data from the latter feed via `oa.get_opportunities`, and explore the two sets of mutually supportive data together.

The following table summarises the inputs and outputs of all functions described above:

Function             |Arguments|Keywords|Output (not using `flat`)
:---                 |:---     |:---    |:---
`get_catalogue_urls` |-|bool:`flat`<br>bool:`verbose`|dict: catalogue URLs in the collection
`get_dataset_urls`   |-|bool:`flat`<br>bool:`verbose`|dict: dataset URLs for each catalogue
`get_feeds`          |-|bool:`flat`<br>bool:`verbose`|dict: feed info for each dataset
`get_opportunities`  |str: `feed_url`<br>or<br>dict: `opportunities`|bool:`verbose`|dict: `opportunities` info for a given `feed_url`
`get_item_kinds`     |dict: `opportunities`|-|dict: Item kinds and counts for a given set of `opportunities`
`get_item_data_types`|dict: `opportunities`|-|dict: Item data types and counts for a given set of `opportunities`
`get_partner_url`    |str: `feed_url_1`<br>and<br>[str]: [`feed_url_2_options`]|-|str: `feed_url_2` that best partners with `feed_url_1`

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
- [YouTube](https://www.youtube.com/@openactive)
- [Medium](https://openactiveio.medium.com/)
