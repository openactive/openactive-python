# v2.0.0 (2024-03-22)
- Added new functions for assessing opportunities:
  - `get_event_type`: Returns `'superevent'`, `'subevent'` or `None` for a given opportunity item "kind" or "type" label such as `'SessionSeries'`
  - `get_superevents`: Returns a list of super-events for a given sub-event (should only be one, the user should check for spurious cases where this may not be so)
  - `get_subevents`: Returns a list of sub-events for a given super-event (could legitimately be many)
- Added rate limiting to any function that makes multiple web calls, default 0.2 seconds between calls i.e. 5 calls per second
- Renamed `get_partner_url` to `get_partner_feed_url` for clarity of use (breaking change)
- Catered for more possible situations in `get_partner_feed_url`
- Allowed for keyword arguments to pass through between chained data gathering functions
- Modified throughout to be better aligned with the PEP8 style guide
- Various internal tweaks for performance and clarity
- Added changelog
- Updated readme

# v1.0.1 (2024-01-18)
- Updated readme

# v1.0.0 (2024-01-17)
- Initial release with the following publicly accessible functions:
  - `get_catalogue_urls`: Returns all catalogue URLs in the master collection of OpenActive data locations
  - `get_dataset_urls`: Returns all dataset URLs for all catalogues
  - `get_feeds`: Returns all feed information summaries for all datasets
  - `get_opportunities`: Returns all opportunity items for a given feed URL
  - `get_item_kinds`: Returns all "kind" labels and counts for a given set of opportunity items
  - `get_item_data_types`: Returns all "type" labels and counts for a given set of opportunity items
  - `get_partner_url`: Returns a partner feed URL for a given feed URL i.e. the sub-event feed URL for a given super-event feed URL