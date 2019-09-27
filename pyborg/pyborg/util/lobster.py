import logging
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import attr
import requests

from voicesynth import MyLittleResult

logger = logging.getLogger(__name__)

async def mk_audio(content: str):
    sess = requests.Session()
    ret = sess.get("https://www.notjordanpeterson.com/")
    ret.raise_for_status()
    tree = ET.fromstring(ret.text)
    logger.debug(tree)
    post = sess.post("https://www.notjordanpeterson.com/", data={'crsf': crsf, 'text': content})
    post.raise_for_status()
    checking_url = post.url
    job_id = urlparse(post.url).path
    # walrusable?
    no_result = True
    while no_result:
        r = sess.get(checking_url)
        r.raise_for_status()
        if r.json["status"] == "running":
            continue
        else:
            no_result = False
        logging.debug(f"mk_audio.lobster:{job_id} - ETA {r.json['eta']}")
    logging.debug(f"mk_audio.lobster:{job_id} - Done")
    return MyLittleResult(r.json["audio_url"])
    # return mp3_url = r.json["audio_url"]

