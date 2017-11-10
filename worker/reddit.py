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
from time import sleep

_DEFAULT_HEADERS = {
    'User-Agent': 'popularitytestbot - Currently crawling for "popularitybot"'
                  'to predict a meme\'s popularity. Students at the University of Waterloo.'
}


def get_new(subreddit, limit=10, after=None):
    sleep(2.5)  # ensure we don't GET too frequently or the API will block us
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
    after = data['data']['after']

    return posts, after


def get_previews(links):
    previews = []

    for link in links:
        link_preview_images = link['data'].get('preview', {}).get('images', [])

        if not link_preview_images:
            continue

        previews.append(link_preview_images[0]['source']['url'])

    return previews
