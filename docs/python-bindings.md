API

This is a shallow python binding of the MusicBrainz web service so you should read Development/XML Web Service/Version 2 to understand how that web service works in general.

All requests that fetch data return the data in the form of a dict. Attributes and elements both map to keys in the dict. List entities are of type list.

This part will give an overview of available functions. Have a look at Usage for examples on how to use them.
General

musicbrainzngs.auth(u, p)

    Set the username and password to be used in subsequent queries to the MusicBrainz XML API that require authentication.

musicbrainzngs.set_rate_limit(limit_or_interval=1.0, new_requests=1)

    Sets the rate limiting behavior of the module. Must be invoked before the first Web service call. If the limit_or_interval parameter is set to False then rate limiting will be disabled. If it is a number then only a set number of requests (new_requests) will be made per given interval (limit_or_interval).

musicbrainzngs.set_useragent(app, version, contact=None)

    Set the User-Agent to be used for requests to the MusicBrainz webservice. This must be set before requests are made.

musicbrainzngs.set_hostname(new_hostname, use_https=False)

    Set the hostname for MusicBrainz webservice requests. Defaults to ‘musicbrainz.org’, accessing over https. For backwards compatibility, use_https is False by default.
    Parameters:	

        new_hostname (str) – The hostname (and port) of the MusicBrainz server to connect to
        use_https (bool) – True if the host should be accessed using https. Default is False

    Specify a non-standard port by adding it to the hostname, for example ‘localhost:8000’.

musicbrainzngs.set_caa_hostname(new_hostname, use_https=False)

    Set the base hostname for Cover Art Archive requests. Defaults to ‘coverartarchive.org’, accessing over https. For backwards compatibility, use_https is False by default.
    Parameters:	

        new_hostname (str) – The hostname (and port) of the CAA server to connect to
        use_https (bool) – True if the host should be accessed using https. Default is False

musicbrainzngs.set_parser(new_parser_fun=None)

    Sets the function used to parse the response from the MusicBrainz web service.

    If no parser is given, the parser is reset to the default parser mb_parser_xml().

musicbrainzngs.set_format(fmt='xml')

    Sets the format that should be returned by the Web Service. The server currently supports xml and json.

    This method will set a default parser for the specified format, but you can modify it with set_parser().

    Warning

    The json format used by the server is different from the json format returned by the musicbrainzngs internal parser when using the xml format! This format may change at any time.

Getting Data

All of these functions will fetch a MusicBrainz entity or a list of entities as a dict. You can specify a list of includes to get more data and you can filter on release_status and release_type. See musicbrainz.VALID_RELEASE_STATUSES and musicbrainz.VALID_RELEASE_TYPES. The valid includes are listed for each function.

musicbrainzngs.get_area_by_id(id, includes=[], release_status=[], release_type=[])

    Get the area with the MusicBrainz id as a dict with an ‘area’ key.

    Available includes: aliases, annotation, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_artist_by_id(id, includes=[], release_status=[], release_type=[])

    Get the artist with the MusicBrainz id as a dict with an ‘artist’ key.

    Available includes: recordings, releases, release-groups, works, various-artists, discids, media, isrcs, aliases, annotation, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels, tags, user-tags, ratings, user-ratings

musicbrainzngs.get_event_by_id(id, includes=[], release_status=[], release_type=[])

    Get the event with the MusicBrainz id as a dict with an ‘event’ key.

    The event dict has the following keys: id, type, name, time, disambiguation and life-span.

    Available includes: aliases, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels, tags, user-tags, ratings, user-ratings

musicbrainzngs.get_instrument_by_id(id, includes=[], release_status=[], release_type=[])

    Get the instrument with the MusicBrainz id as a dict with an ‘artist’ key.

    Available includes: aliases, annotation, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels, tags, user-tags

musicbrainzngs.get_label_by_id(id, includes=[], release_status=[], release_type=[])

    Get the label with the MusicBrainz id as a dict with a ‘label’ key.

    Available includes: releases, discids, media, aliases, annotation, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels, tags, user-tags, ratings, user-ratings

musicbrainzngs.get_place_by_id(id, includes=[], release_status=[], release_type=[])

    Get the place with the MusicBrainz id as a dict with an ‘place’ key.

    Available includes: aliases, annotation, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels, tags, user-tags

musicbrainzngs.get_recording_by_id(id, includes=[], release_status=[], release_type=[])

    Get the recording with the MusicBrainz id as a dict with a ‘recording’ key.

    Available includes: artists, releases, discids, media, artist-credits, isrcs, work-level-rels, annotation, aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_recordings_by_isrc(isrc, includes=[], release_status=[], release_type=[])

    Search for recordings with an ISRC. The result is a dict with an ‘isrc’ key, which again includes a ‘recording-list’.

    Available includes: artists, releases, discids, media, artist-credits, isrcs, work-level-rels, annotation, aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_release_group_by_id(id, includes=[], release_status=[], release_type=[])

    Get the release group with the MusicBrainz id as a dict with a ‘release-group’ key.

    Available includes: artists, releases, discids, media, artist-credits, annotation, aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_release_by_id(id, includes=[], release_status=[], release_type=[])

    Get the release with the MusicBrainz id as a dict with a ‘release’ key.

    Available includes: artists, labels, recordings, release-groups, media, artist-credits, discids, isrcs, recording-level-rels, work-level-rels, annotation, aliases, tags, user-tags, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_releases_by_discid(id, includes=[], toc=None, cdstubs=True, media_format=None)

    Search for releases with a Disc ID or table of contents.

    When a toc is provided and no release with the disc ID is found, a fuzzy search by the toc is done. The toc should have to same format as discid.Disc.toc_string. When a toc is provided, the format of the discid itself is not checked server-side, so any value may be passed if searching by only toc is desired.

    If no toc matches in musicbrainz but a CD Stub does, the CD Stub will be returned. Prevent this from happening by passing cdstubs=False.

    By default only results that match a format that allows discids (e.g. CD) are included. To include all media formats, pass media_format=’all’.

    The result is a dict with either a ‘disc’ , a ‘cdstub’ key or a ‘release-list’ (fuzzy match with TOC). A ‘disc’ has an ‘offset-count’, an ‘offset-list’ and a ‘release-list’. A ‘cdstub’ key has direct ‘artist’ and ‘title’ keys.

    Available includes: artists, labels, recordings, release-groups, media, artist-credits, discids, isrcs, recording-level-rels, work-level-rels, annotation, aliases, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_series_by_id(id, includes=[])

    Get the series with the MusicBrainz id as a dict with a ‘series’ key.

    Available includes: annotation, aliases, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_work_by_id(id, includes=[])

    Get the work with the MusicBrainz id as a dict with a ‘work’ key.

    Available includes: aliases, annotation, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_works_by_iswc(iswc, includes=[])

    Search for works with an ISWC. The result is a dict with a`work-list`.

    Available includes: aliases, annotation, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_url_by_id(id, includes=[])

    Get the url with the MusicBrainz id as a dict with a ‘url’ key.

    Available includes: area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.get_collections()

    List the collections for the currently authenticated user as a dict with a ‘collection-list’ key.

musicbrainzngs.get_releases_in_collection(collection, limit=None, offset=None)

    List the releases in a collection. Returns a dict with a ‘collection’ key, which again has a ‘release-list’.

    See Browsing for how to use limit and offset.

musicbrainzngs.musicbrainz.VALID_RELEASE_TYPES = ['nat', 'album', 'single', 'ep', 'broadcast', 'other', 'compilation', 'soundtrack', 'spokenword', 'interview', 'audiobook', 'live', 'remix', 'dj-mix', 'mixtape/street']

    These can be used to filter whenever releases are includes or browsed

musicbrainzngs.musicbrainz.VALID_RELEASE_STATUSES = ['official', 'promotion', 'bootleg', 'pseudo-release']

    These can be used to filter whenever releases or release-groups are involved

Cover Art

musicbrainzngs.get_image_list(releaseid)

    Get the list of cover art associated with a release.

    The return value is the deserialized response of the JSON listing returned by the Cover Art Archive API.

    If an error occurs then a ResponseError will be raised with one of the following HTTP codes:

        400: Releaseid is not a valid UUID
        404: No release exists with an MBID of releaseid
        503: Ratelimit exceeded

musicbrainzngs.get_release_group_image_list(releasegroupid)

    Get the list of cover art associated with a release group.

    The return value is the deserialized response of the JSON listing returned by the Cover Art Archive API.

    If an error occurs then a ResponseError will be raised with one of the following HTTP codes:

        400: Releaseid is not a valid UUID
        404: No release exists with an MBID of releaseid
        503: Ratelimit exceeded

musicbrainzngs.get_image(mbid, coverid, size=None, entitytype='release')

    Download cover art for a release. The coverart file to download is specified by the coverid argument.

    If size is not specified, download the largest copy present, which can be very large.

    If an error occurs then a ResponseError will be raised with one of the following HTTP codes:

        400: Releaseid is not a valid UUID or coverid is invalid
        404: No release exists with an MBID of releaseid
        503: Ratelimit exceeded

    Parameters:	

        coverid (int or str) – front, back or a number from the listing obtained with get_image_list()
        size (str or None) – “250”, “500”, “1200” or None. If it is None, the largest available picture will be downloaded. If the image originally uploaded to the Cover Art Archive was smaller than the requested size, only the original image will be returned.
        entitytype (str) – The type of entity for which to download the cover art. This is either release or release-group.

    Returns:	

    The binary image data
    Type:	

    str

musicbrainzngs.get_image_front(releaseid, size=None)

    Download the front cover art for a release. The size argument and the possible error conditions are the same as for get_image().

musicbrainzngs.get_release_group_image_front(releasegroupid, size=None)

    Download the front cover art for a release group. The size argument and the possible error conditions are the same as for get_image().

musicbrainzngs.get_image_back(releaseid, size=None)

    Download the back cover art for a release. The size argument and the possible error conditions are the same as for get_image().

Searching

For all of these search functions you can use any of the allowed search fields as parameter names. The documentation of what these fields do is on Development/XML Web Service/Version 2/Search.

You can also set the query parameter to any lucene query you like. When you use any of the search fields as parameters, special characters are escaped in the query.

By default the elements are concatenated with spaces in between, so lucene essentially does a fuzzy search. That search might include results that don’t match the complete query, though these will be ranked lower than the ones that do. If you want all query elements to match for all results, you have to set strict=True.

By default the web service returns 25 results per request and you can set a limit of up to 100. You have to use the offset parameter to set how many results you have already seen so the web service doesn’t give you the same results again.

musicbrainzngs.search_annotations(query='', limit=None, offset=None, strict=False, **fields)

    Search for annotations and return a dict with an ‘annotation-list’ key.

    Available search fields: entity, name, text, type

musicbrainzngs.search_areas(query='', limit=None, offset=None, strict=False, **fields)

    Search for areas and return a dict with an ‘area-list’ key.

    Available search fields: aid, alias, area, areaaccent, begin, comment, end, ended, iso, iso1, iso2, iso3, sortname, tag, type

musicbrainzngs.search_artists(query='', limit=None, offset=None, strict=False, **fields)

    Search for artists and return a dict with an ‘artist-list’ key.

    Available search fields: alias, area, arid, artist, artistaccent, begin, beginarea, comment, country, end, endarea, ended, gender, ipi, isni, primary_alias, sortname, tag, type

musicbrainzngs.search_events(query='', limit=None, offset=None, strict=False, **fields)

    Search for events and return a dict with an ‘event-list’ key.

    Available search fields: aid, alias, area, arid, artist, begin, comment, eid, end, ended, event, eventaccent, pid, place, tag, type

musicbrainzngs.search_instruments(query='', limit=None, offset=None, strict=False, **fields)

    Search for instruments and return a dict with a ‘instrument-list’ key.

    Available search fields: alias, comment, description, iid, instrument, instrumentaccent, tag, type

musicbrainzngs.search_labels(query='', limit=None, offset=None, strict=False, **fields)

    Search for labels and return a dict with a ‘label-list’ key.

    Available search fields: alias, area, begin, code, comment, country, end, ended, ipi, label, labelaccent, laid, release_count, sortname, tag, type

musicbrainzngs.search_places(query='', limit=None, offset=None, strict=False, **fields)

    Search for places and return a dict with a ‘place-list’ key.

    Available search fields: address, alias, area, begin, comment, end, ended, lat, long, pid, place, placeaccent, type

musicbrainzngs.search_recordings(query='', limit=None, offset=None, strict=False, **fields)

    Search for recordings and return a dict with a ‘recording-list’ key.

    Available search fields: alias, arid, artist, artistname, comment, country, creditname, date, dur, format, isrc, number, position, primarytype, qdur, recording, recordingaccent, reid, release, rgid, rid, secondarytype, status, tag, tid, tnum, tracks, tracksrelease, type, video

musicbrainzngs.search_release_groups(query='', limit=None, offset=None, strict=False, **fields)

    Search for release groups and return a dict with a ‘release-group-list’ key.

    Available search fields: alias, arid, artist, artistname, comment, creditname, primarytype, reid, release, releasegroup, releasegroupaccent, releases, rgid, secondarytype, status, tag, type

musicbrainzngs.search_releases(query='', limit=None, offset=None, strict=False, **fields)

    Search for recordings and return a dict with a ‘recording-list’ key.

    Available search fields: alias, arid, artist, artistname, asin, barcode, catno, comment, country, creditname, date, discids, discidsmedium, format, label, laid, lang, mediums, primarytype, quality, reid, release, releaseaccent, rgid, script, secondarytype, status, tag, tracks, tracksmedium, type

musicbrainzngs.search_series(query='', limit=None, offset=None, strict=False, **fields)

    Search for series and return a dict with a ‘series-list’ key.

    Available search fields: alias, comment, orderingattribute, series, seriesaccent, sid, tag, type

musicbrainzngs.search_works(query='', limit=None, offset=None, strict=False, **fields)

    Search for works and return a dict with a ‘work-list’ key.

    Available search fields: alias, arid, artist, comment, iswc, lang, recording, recording_count, rid, tag, type, wid, work, workaccent

Browsing

You can browse entitities of a certain type linked to one specific entity. That is you can browse all recordings by an artist, for example.

These functions can be used to to include more than the maximum of 25 linked entities returned by the functions in Getting Data. You can set a limit as high as 100. The default is still 25. Similar to the functions in Searching, you have to specify an offset to see the results you haven’t seen yet.

You have to provide exactly one MusicBrainz ID to these functions.

musicbrainzngs.browse_artists(recording=None, release=None, release_group=None, work=None, includes=[], limit=None, offset=None)

    Get all artists linked to a recording, a release or a release group. You need to give one MusicBrainz ID.

    Available includes: aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_events(area=None, artist=None, place=None, includes=[], limit=None, offset=None)

    Get all events linked to a area, a artist or a place. You need to give one MusicBrainz ID.

    Available includes: aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_labels(release=None, includes=[], limit=None, offset=None)

    Get all labels linked to a relase. You need to give a MusicBrainz ID.

    Available includes: aliases, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_places(area=None, includes=[], limit=None, offset=None)

    Get all places linked to an area. You need to give a MusicBrainz ID.

    Available includes: aliases, tags, user-tags, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_recordings(artist=None, release=None, includes=[], limit=None, offset=None)

    Get all recordings linked to an artist or a release. You need to give one MusicBrainz ID.

    Available includes: artist-credits, isrcs, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_release_groups(artist=None, release=None, release_type=[], includes=[], limit=None, offset=None)

    Get all release groups linked to an artist or a release. You need to give one MusicBrainz ID.

    You can filter by musicbrainz.VALID_RELEASE_TYPES.

    Available includes: artist-credits, tags, user-tags, ratings, user-ratings, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_releases(artist=None, track_artist=None, label=None, recording=None, release_group=None, release_status=[], release_type=[], includes=[], limit=None, offset=None)

    Get all releases linked to an artist, a label, a recording or a release group. You need to give one MusicBrainz ID.

    You can also browse by track_artist, which gives all releases where some tracks are attributed to that artist, but not the whole release.

    You can filter by musicbrainz.VALID_RELEASE_TYPES or musicbrainz.VALID_RELEASE_STATUSES.

    Available includes: artist-credits, labels, recordings, isrcs, release-groups, media, discids, area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

musicbrainzngs.browse_urls(resource=None, includes=[], limit=None, offset=None)

    Get urls by actual URL string. You need to give a URL string as ‘resource’

    Available includes: area-rels, artist-rels, label-rels, place-rels, event-rels, recording-rels, release-rels, release-group-rels, series-rels, url-rels, work-rels, instrument-rels

Submitting

These are the only functions that write to the MusicBrainz database. They take one or more dicts with multiple entities as keys, which take certain values or a list of values.

You have to use auth() before using any of these functions.

musicbrainzngs.submit_barcodes(release_barcode)

    Submits a set of {release_id1: barcode, …}

musicbrainzngs.submit_isrcs(recording_isrcs)

    Submit ISRCs. Submits a set of {recording-id1: [isrc1, …], …} or {recording_id1: isrc, …}.

musicbrainzngs.submit_tags(**kwargs)

    Submit user tags. Takes parameters named e.g. ‘artist_tags’, ‘recording_tags’, etc., and of the form: {entity_id1: [tag1, …], …} If you only have one tag for an entity you can use a string instead of a list.

    The user’s tags for each entity will be set to that list, adding or removing tags as necessary. Submitting an empty list for an entity will remove all tags for that entity by the user.

musicbrainzngs.submit_ratings(**kwargs)

    Submit user ratings. Takes parameters named e.g. ‘artist_ratings’, ‘recording_ratings’, etc., and of the form: {entity_id1: rating, …}

    Ratings are numbers from 0-100, at intervals of 20 (20 per ‘star’). Submitting a rating of 0 will remove the user’s rating.

musicbrainzngs.add_releases_to_collection(collection, releases=[])

    Add releases to a collection. Collection and releases should be identified by their MBIDs

musicbrainzngs.remove_releases_from_collection(collection, releases=[])

    Remove releases from a collection. Collection and releases should be identified by their MBIDs

Exceptions

These are the main exceptions that are raised by functions in musicbrainzngs. You might want to catch some of these at an appropriate point in your code.

Some of these might have subclasses that are not listed here.

class musicbrainzngs.MusicBrainzError

    Base class for all exceptions related to MusicBrainz.

class musicbrainzngs.UsageError

    Bases: musicbrainzngs.musicbrainz.MusicBrainzError

    Error related to misuse of the module API.

class musicbrainzngs.WebServiceError(message=None, cause=None)

    Bases: musicbrainzngs.musicbrainz.MusicBrainzError

    Error related to MusicBrainz API requests.

class musicbrainzngs.AuthenticationError(message=None, cause=None)

    Bases: musicbrainzngs.musicbrainz.WebServiceError

    Received a HTTP 401 response while accessing a protected resource.

class musicbrainzngs.NetworkError(message=None, cause=None)

    Bases: musicbrainzngs.musicbrainz.WebServiceError

    Problem communicating with the MB server.

class musicbrainzngs.ResponseError(message=None, cause=None)

    Bases: musicbrainzngs.musicbrainz.WebServiceError

    Bad response sent by the MB server.

Logging

musicbrainzngs logs debug and informational messages using Python’s logging module. All logging is done in the logger with the name musicbrainzngs.

You can enable this output in your application with:

import logging
logging.basicConfig(level=logging.DEBUG)
# optionally restrict musicbrainzngs output to INFO messages
logging.getLogger("musicbrainzngs").setLevel(logging.INFO)

