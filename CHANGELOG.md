# v3.0.0 (2026-01-05)
- `try_requests`
  - Added option for call headers, with defaults
  - Added protection against calls not returning properly
- `get_catalogue_urls`
  - Added option to use the preview collection
- `get_feeds`
  - Added feed `logo_url`
  - Changed feed `name` to `dataset_name`, as it applies to all feeds in the dataset
- `get_partner_feed_url`
  - Added more variants of slot URLs
- `get_opportunities`
  - Added timeout functionality, default set to 600 seconds for running a single feed
  - Added memory logging functionality, tracking item-by-item bytesize differences using `sys.getsizeof`. This may not be super accurate, but should at least give some idea of how the opportunities dictionary size changes in memory as it's altered.
  - Added `status` field to the opportunities dictionary, which has a value of `'COMPLETE'`, `'TIMEOUT'` or `'ERROR'`
  - Added `num_urls` field to the opportunities dictionary, which is the number of URLs visited in total for the feed
  - Removed the perpetual accumulating record of feed URLs visited, as this just grows over time and is unnecessary
  - Allowed for extra custom keys in the opportunities dictionary by loosening the input verification
  - Delegated tasks to a new function `get_opportunities_helper`, which processes a single feed page at a time before returning to `get_opportunities`. As such, `get_opportunities` itself no longer operates on an ever deepening recursion, which had potential performance issues.
- `get_opportunities_helper`
  - Added this new function
- `get_bytesize`
  - Added this new function
- `get_item_kinds`
  - Modified to also count `None` if the kind is not present
- `get_item_data_types`
  - Modified to also count `None` if the type is not present
  - Renamed to `get_item_types`
- `get_event_type`
  - Added more superevent and subevent labels to judge feeds by their kind/type
  - Moved `'HeadlineEvent'` and `'CourseInstance'` from superevent to subevent labels, which seemed to better suit the nature of their content i.e. actually containing subevent information
- `get_superevents`
  - Added keyword list of superevent IDs to skip
- `get_subevents`
  - Added keyword list of subevent IDs to skip
- `get_superevent_id_v_subevent_ids`
  - Added this new function
- `get_superevent_id_in_subevent`
  - Renamed to `get_subevent_superevent_modified_id`
- `get_superevent_ids`
  - Renamed to `get_item_modified_ids`
- Miscellaneous
  - Various nomenclature and ordering changes for simplicity, consistency and clarity, also ensuring snake case throughout

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