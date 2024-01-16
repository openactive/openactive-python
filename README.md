<img src='https://openactive.io/brand-assets/openactive-logo-large.png' width='500'>

[![License](http://img.shields.io/:license-mit-blue.svg)](https://opensource.org/license/mit/)

This is a package for reading feeds of activity data published in the OpenActive format.

# Installation

It is recommended to first set up a virtual environment for your OpenActive project, to ensure that it's isolated from your base environment and runs as intended. The only thing that must be installed in your base environment is some package for generating virtual environments, such as `virtualenv`:

```
$ pip install virtualenv
```

Then, in a new project folder, create and initialise a new virtual environment as follows (`virt` and `venv` are typical names, but you can choose something else if needed):

```
$ virtualenv virt
$ source virt/bin/activate
(virt) $
```

Now install the `openactive` package, and you're good to go:

```
(virt) $ pip install openactive
```

# Usage

Let's import the `openactive` package under the proxy name `oa` in a Python session:

```
>>> import openactive as oa
```

In order to effectively use the package, we must first understand the OpenActive data model. OpenActive data is released by a data publisher as a Realtime Paged Data Exchange (RPDE) feed. There can be multiple feeds from a given provider, and in fact we often have complimentary pairs of feeds, such as having one for super-event data (e.g. a series of fitness class sessions) and one for sub-event data (e.g. particular scheduled sessions). In such cases, both feeds must be read in order to get a complete picture, and items in one feed will reference items in the other feed.

Groups of feeds are bundled together in a dataset, groups of datasets are bundled together in a catalogue, and groups of catalogues are bundled together in a collection. There is only one collection, which is therefore the starting point for everything else. Given a list of feed information, you will not often want to see the exact path by which the feeds were gathered, but there are functions in `openactive` that show the journey from source if needed. So let's just start at the very beginning to be clear on how things work. First, let's define a printer function to give us a clear indented output display for what follows:

```
>>> import json
>>> def printer(arg):
...     print(json.dumps(arg,indent=4))
```

Now let's get the catalogue URLs in the collection:

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

We see that this returns a dictionary with a single key, the collection URL, which has a value of the list of catalogue URLs. This function also has two optional boolean keywords which weren't used above. The first keyword is `flat`, which causes the function to return a flat list structure rather than a dictionary, so losing the collection URL showing the data path. The second keyword is `verbose`, which causes the function to print its name and the URLs that it calls during execution. Let's run the above again with both keywords set to `True`:

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

Now for each of these catalogue URLs, let's get the dataset URLs they contain:

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
```

We again see an output dictionary, with keys that are catalogue URLs and values that are lists of dataset URLs. The above output was manually truncated, and you will see many more dataset URLs if you run the command yourself. If needed, we can again use the `flat` keyword to remove the key-level information and combine the value lists into one, and the `verbose` keyword to show function calls and URL calls.

Now for each of these dataset URLs, let's get the feed information they contain:

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

Once again we see an output dictionary, with keys that are dataset URLs and values that are lists of feed dictionaries. The above output was manually truncated, and you will see many more feed dictionaries if you run the command yourself. If needed, we can again use the `flat` keyword to remove the key-level information and combine the value lists into one, and the `verbose` keyword to show function calls and URL calls. Note that, regardless of the `verbose` keyword, warning and error messages are printed as standard by all functions, as seen above for the last function call. We typically have such messages when a page is unavailable or not set up correctly.

The list of feeds is usually where you'll want to start your project work, but it's useful to be aware of the above journey in getting to this point. What we ultimately want is the information served via a given feed URL, which is the starting point for information transferred via Realtime Paged Data Exchange (RPDE). In essence, this is just like what we have returned from a search engine, which breaks results over a number of pages rather than showing them all on a single page. To get all of the information, we must visit each page one-by-one. This is done for us automatically by the next function in the series, so let's take a look at what we get for a given feed URL taken from the previous output:

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
    "firstPageOrigin": "https://opendata.leisurecloud.live",
    "nextPage": "https://opendata.leisurecloud.live/api/feeds/ActiveLeeds-live-session-series?afterTimestamp=26002956&afterId=KL2CLPL11001121"
}
```

The returned output is, once again, a dictionary. The main content of interest is found under the `items` key, which has a dictionary of 'opportunity' items, these being the activity items of this particular feed. The above is greatly truncated, and you will see a lot more if your run the command yourself. This output cannot be flattened via the `flat` keyword, as its structure is essential to maintain. The `verbose` keyword is still applicable, and will again cause the function to print the URLs that it calls. These URLs are in fact also returned in the output, along with base form (the 'origin') of the first page, and the next page to be visited when the feed is updated by the publisher, in order to continue the read at a later time from where we left off. To do this, which can also be done if we encounter an issue when we run the function and only receive output from a partial read of the full set of feed pages, we give the output dictionary to the function as argument rather than a feed URL:

```
>>> opportunities_updated = oa.get_opportunities(opportunities)
```

WORK IN PROGRESS

```
>>> item_kinds = oa.get_item_kinds(opportunities)
>>> item_data_types = oa.get_item_data_types(opportunities)
>>> partner_url = oa.get_partner_url('some feed URL', ['list of feed URLs to search for partner URL'])
```

The following table summarises the inputs and outputs of all functions described above:

Function             |Input|Keywords|Output
:---                 |:--- |:---    |:---
`get_catalogue_urls` |-|bool:`flat`<br>bool:`verbose`|dict: catalogue URLs in the collection
`get_dataset_urls`   |-|bool:`flat`<br>bool:`verbose`|dict: dataset URLs for each catalogue
`get_feeds`          |-|bool:`flat`<br>bool:`verbose`|dict: feed info for each dataset
`get_opportunities`  |str: feed URL<br>or<br>dict: opportunities|bool:`verbose`|dict: opportunity info for a given feed
`get_item_kinds`     |dict: opportunities|-|dict: Item kinds for a given set of opportunities
`get_item_data_types`|dict: opportunities|-|dict: Item data types for a given set of opportunities
`get_partner_url`    |str: feed URL1<br>[str]: feed URL2 options|-|str: feed URL2 that best partners with feed URL1

# Links

- [Initiative homepage](https://openactive.io/)
- [Developer homepage](https://developer.openactive.io/)
- [GitHub](https://github.com/openactive)
