# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
import logging
from time import sleep, time
import math

_DEFAULT_HEADERS = {
    'User-Agent': 'popularitytestbot - Currently crawling for "popularitybot"'
                  'to predict a meme\'s popularity. Students at the University of Waterloo.'
}

default_sleep_time = 2.25


class ScrapedRedditPost(object):

    def __init__(self, posts, user_info, image_urls):
        self.posts = posts
        self.user_info = user_info
        self.image_urls = image_urls

    @staticmethod
    def clean(scraped_info):
        filtered = ((post, image_url, user_info)
                    for post, image_url, user_info
                    in zip(scraped_info.posts, scraped_info.image_urls, scraped_info.user_info)
                    if post is not None and image_url is not None and user_info is not None)
        scraped_info.posts, scraped_info.image_urls, scraped_info.user_info = zip(*filtered)


def scrape_reddit(subreddit, post_count: int=100, after: str=None, limit: int=100, sleep_time: float=default_sleep_time):
    if limit is None:
        limit = 100
    elif limit > 100 or limit < 1:
        raise ValueError("Limit range = [1, 100]")
    if post_count < 1 or post_count > 100000:
        raise ValueError("Post count range = [1, 100000]")
    if sleep_time < 2 or sleep_time > 4:
        raise ValueError("Sleep time range = [2, 4]")
    pages = int(math.ceil(post_count / limit))

    first_iteration = True
    for _ in range(pages):
        if not first_iteration and after is None:
            raise RuntimeError("Seen a None 'after' after the first iteration. Re-reading data.")
        try:
            posts, after = get_new(subreddit, limit=limit, after=after, sleep_time=sleep_time)
        except requests.exceptions.HTTPError as e:
            logging.error("{}: {} - Get new json failed.", e.errno, e.response)
            yield None
        if first_iteration:
            first_iteration = False
        image_urls = get_previews(posts)
        user_info = get_user_info(posts, sleep_time=sleep_time)
        res = ScrapedRedditPost(posts=posts, user_info=user_info, image_urls=image_urls)
        yield res


def get_new(subreddit, limit: int=100, after=None, sleep_time: float=default_sleep_time):
    sleep(sleep_time)  # ensure we don't GET too frequently or the API will block us
    logging.debug('Reddit new json: <sub: {}, after: {}>'.format(subreddit, after))
    r = requests.get(
        "https://www.reddit.com/r/{}/new.json".format(subreddit),
        params={
            'limit': limit,
            'raw_json': 1,
            'after': after
        },
        headers=_DEFAULT_HEADERS)

    r.raise_for_status()

    data = r.json()

    posts = data['data']['children']
    for post in posts:
        post['time_collected'] = int(time())
    after = data['data']['after']

    return posts, after


def get_previews(links):
    previews = []

    for link in links:
        link_preview_images = link['data'].get('preview', {}).get('images', [])

        if not link_preview_images:
            previews.append(None)  # inserting null keeps the place of the image
            continue

        previews.append(link_preview_images[0]['source']['url'])

    return previews


def get_post_id(post):
    return post.get('data').get('id')


def get_user_info(posts, sleep_time: float=default_sleep_time):
    user_info = []

    for post in posts:
        author = post.get('data').get('author')
        try:
            author_data = get_info_from_author(author=author, sleep_time=sleep_time)
            user_info.append(author_data)
        except requests.exceptions.HTTPError:
            user_info.append(None)
        except ValueError:
            user_info.append(None)
    return user_info


def get_info_from_author(author: str, sleep_time: float=default_sleep_time):
    if author == "[deleted]":
        raise ValueError("Author is deleted.")
    sleep(sleep_time)  # ensure we don't GET too frequently or the API will block us
    r = requests.get(
        "https://www.reddit.com/user/{}/about.json".format(author),
        params={},
        headers=_DEFAULT_HEADERS)

    r.raise_for_status()

    data = r.json()
    data['time_collected'] = int(time())

    return data
