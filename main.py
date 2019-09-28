# Internal/Django imports
from willbeddow import content_utils
from django.core.cache import cache
from django.conf import settings
from django.http.response import JsonResponse

# External imports
import twitter
import spacy
import requests

# Builtin imports
import urllib

# Load the spacy model
nlp = spacy.load('en_core_web_lg')

_CONTENTFUL_FEATURE_ID = "candidate-map-2020"
_GEOCODING_KEY = settings.CONF_DATA["candidate-map-geocoding-key"]
# Set up the twitter api
api = twitter.Api(consumer_key=settings.CONF_DATA["twitter"]["api_key"],
                  consumer_secret=settings.CONF_DATA["twitter"]["secret_key"],
                  access_token_key=settings.CONF_DATA["twitter"]["access_token"],
                  access_token_secret=settings.CONF_DATA["twitter"]["access_token_secret"])


def geocode(location):
    """
    Take a location and use the google geocoding API

    :param location: A location string of where we think thge tweet is about
    :return: (lat, lon) The latitude and longitude of the location, to be displayed with a pin on the map
    """
    geocoding_url = f'https://maps.googleapis.com/maps/api/geocode/json?' \
                    f'address={location}&key={_GEOCODING_KEY}'
    geocode_data = requests.get(geocoding_url).json()
    return geocode_data


def get_tweets(candidate):
    """
    Use the twitter API to get the recent tweets from a candidate
    :param candidate:
    :return:
    """
    statuses = api.GetUserTimeline(screen_name=candidate["twitter"])
    # Use NLP to try to figure out where the tweets are
    for tweet in statuses:
        if tweet.user.screen_name == candidate["twitter"]:
            parsed_location = nlp(tweet.text)
            for ent in parsed_location.ents:
                if ent.label_ == "GPE":
                    location = geocode(ent.text)
                    if "results" in location.keys():
                        if len(location["results"]) >= 1:
                            # Look for a country
                            for address_component in location["results"][0]["address_components"]:
                                if "country" in address_component["types"] and address_component["short_name"] == "US":
                                    print(tweet)
                                    return {
                                        "tweet": f"https://twitter.com/{candidate['twitter']}/status/{tweet.id}",
                                        "user_image": tweet.user.profile_image_url_https,
                                        "lat": location["results"][0]["geometry"]["location"]["lat"],
                                        "lon": location["results"][0]["geometry"]["location"]["lng"],
                                        "location": ent.text
                                    }
    return None


def _get_candidates():
    """
    Use the Contentful API to determine which candidates we should get information about
    :return status: The status of the app
    """
    cache_str = "candidate_map_contentful_update"
    status = cache.get(cache_str)
    if not status:
        status_app = content_utils.Feature(_CONTENTFUL_FEATURE_ID)
        status = status_app.context["candidates"]
        cache.set(cache_str, status, 120)
    return status


def candiate_data(request, *args, **kwargs):
    """
    The view endpoint that will return the actual data for the API
    :return:
    """
    candidates_raw = _get_candidates()
    candidates = []
    for candidate in candidates_raw:
        candidate_tweets = get_tweets(candidate)
        if candidate_tweets:
            candidate.update(candidate_tweets)
        candidates.append(candidate)
    return JsonResponse({"candidates": candidates})
