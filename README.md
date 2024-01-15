<img src='https://openactive.io/brand-assets/openactive-logo-large.png' width='500'>

[![License](http://img.shields.io/:license-mit-blue.svg)](http://theodi.mit-license.org)

# Project description

OpenActive is a package for reading feeds of activity data published in the [OpenActive](https://openactive.io/) format.

# Installation

```
$ pip install openactive
```

# Usage

```
>>> import openactive as oa

>>> catalogue_urls = oa.get_catalogue_urls()
>>> dataset_urls = oa.get_dataset_urls()
>>> feeds = oa.get_feeds()
>>> opportunities = oa.get_opportunities('some feed URL')
>>> item_kinds = oa.get_item_kinds(opportunities)
>>> item_data_types = oa.get_item_data_types(opportunities)
>>> partner_url = oa.get_partner_url('some feed URL', ['list of feed URLs to search for partner URL'])
```

# Links

- [Initiative homepage](https://openactive.io/)
- [Developer homepage](https://developer.openactive.io/)
- [GitHub](https://github.com/openactive)
