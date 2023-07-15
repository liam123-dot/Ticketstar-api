"""

Uses the fixr search api f"https://api.fixr.co/search/organisers?query={query}&limit=6&offset=0&popularity__boost=0"

which loads a list of results containing:

{
            "id": 324100179,
            "slug": null,
            "name": "The Fun Raisers",
            "image_url": "https://fixr-cdn.fixr.co/images/sales_account/logo/ed921611e2fa4a67a6456f963146c103.jpeg",
            "routing_part": "324100179"
        },

We then can use the url:

f"https://fixr.co/_next/data/{build}}/en-GB/organiser/5486166.json?id={organiser_id}"

the build id is something that has to be fetched from the main fixr page url

"""
import concurrent.futures

from FixrExceptions import FixrApiException
import requests
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

build_id_exception = FixrApiException("There has been a server issue", "build id not found")

headers = {
    "Accept": "application/json; version=3.0"
}


def get_build_id():
    try:
        url = 'https://fixr.co'

        search_term = "{\"props\":"

        response = requests.get(url)

        text = response.text

        index = text.find(search_term)

        if index == -1:
            raise build_id_exception

        counter = 0

        open_counter = 0
        close_counter = 0

        while True:
            try:
                if text[index + counter] == '{':
                    open_counter += 1
                elif text[index + counter] == '}':
                    close_counter += 1

                counter += 1

                if open_counter == close_counter and open_counter != 0:
                    break
            except IndexError as e:
                logger.error("Error fetching build_id, error: %s, response: %s. Response text: %s", e, response, response.text)
                raise build_id_exception

        data = json.loads(text[index: index + counter])

        buildId = data['buildId']

        return buildId
    except Exception as e:
        logger.error("Error fetching build_id, error: %s", e)
        raise build_id_exception


def check_organiser_has_evevents(build_id, organiser_id=None, slug=None):

    return len(get_organiser_events(build_id, organiser_id, slug)) != 0


def get_organiser_events(build_id, organiser_id=None, slug=None):
    if slug is not None:
        url = f"https://fixr.co/_next/data/{build_id}/en-GB/organiser/{slug}.json?id={slug}"
    else:
        url = f"https://fixr.co/_next/data/{build_id}/en-GB/organiser/{organiser_id}.json?id={organiser_id}"

    response = requests.get(url, headers=headers)

    if not response.ok:
        logger.error("Response error from fixr organiser_has_event. Response code: %s, Response text: %s", response.status_code,
                     response.text)

        raise FixrApiException("Invalid response from fixr api")

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("Error decoding organiser response into json, get_organiser_events, response: %s", response.content)
        raise FixrApiException("Json decode error")

    try:

        events = data['pageProps']['data']['data']

    except KeyError as e:
        logger.error("Error checking orgnnier has event, error: %s, response text: %s", e, response.text)

        raise FixrApiException("Invalid response from fixr api, key error")

    return events


def search(query, limit=None, offset=None):
    if limit is None:
        limit = 6
    if offset is None:
        offset = 0
    organisers_url = f"https://api.fixr.co/search/organisers?query={query}&limit={limit}&offset={offset}&popularity__boost=0"

    response = requests.get(organisers_url, headers=headers)

    if not response.ok:
        logger.error("Response error from fixr. Response code: %s, Response text: %s", response.status_code,
                     response.text)

        raise FixrApiException("Invalid response from fixr api")

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("Error decoding organiser response into json, response: %s", response.content)
        raise FixrApiException("Json decode error")

    organisers = []

    build_id = get_build_id()

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_organiser = {executor.submit(check_organiser_has_evevents, build_id, organiser['id'], organiser['slug']): organiser for
                                   organiser in data['results']}

            for future in concurrent.futures.as_completed(future_to_organiser):
                organiser = future_to_organiser[future]
                organiser_has_events = future.result()

                if organiser_has_events:
                    organisers.append({
                        'fixr_id': organiser['id'],
                        'name': organiser['name'],
                        'image_url': organiser['image_url'],
                        'slug': organiser['slug']
                    })

                if len(organisers) == 3:
                    break

    except FixrApiException as e:
        raise e
    except KeyError as e:
        logger.error("Error checking organiser has events, key error: %S, ", e)
        raise FixrApiException('Key error', e)
    except IndexError as e:
        logger.error("Error checking organiser has events, index error: %S, ", e)
        raise FixrApiException('Index error', e)
    except Exception as e:
        logger.error("Error checking organiser has events, unknown error: %S, ", e)
        raise FixrApiException('unknown error', e)

    return organisers

