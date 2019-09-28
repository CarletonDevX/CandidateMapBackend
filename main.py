# Builtin imports

# Internal/Django imports
from willbeddow import content_utils
from django.core.cache import cache
from django.conf import settings

# External imports
import twitter

_CONTENTFUL_FEATURE_ID = "candidate-map-2020"
# Set up the twitter api
api = twitter.Api(consumer_key=settings.CONF_DATA["twitter"]["api_key"],
                  consumer_secret=settings.CONF_DATA["twitter"]["secret_key"],
                  access_token_key=settings.CONF_DATA["twitter"]["access_token"],
                  access_token_secret=settings.CONF_DATA["twitter"]["access_token_secret"])


def get_candidates():
    pass


def get_tweets(candidate):
    """
    Use the twitter API to get the recent tweets from a candidate
    :param candidate:
    :return:
    """
    pass

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
    candidates = _get_candidates()
    for candidate in candidates:
        candidate_tweets = get_tweets(candidate)
