import time
import sys
import logging
import xml.etree.ElementTree as ET

import attr
import aiohttp
import requests

logger = logging.getLogger(__name__)

@attr.s
class MyLittleResult():
    final_url = attr.ib()
    session_id = attr.ib()

async def mk_audio(content, delete=False, download=False):
    "VOICEFORGE: send a string to voiceforge to make a mp3 (I think ogg is broken on their end)"
    sess = requests.Session()
    # pretend we're a real ~~boy~~ browser
    sess.get("https://www.voiceforge.com/demo?uservoice=Wiseguy").raise_for_status()
    unixtime = int(time.time())
    logger.info("grabbed cookies: %s", sess.cookies)
    ret = sess.get("https://www.voiceforge.com/demos/createAudio.php", params={"voice": "Wiseguy", "createTime": unixtime, "voiceText": content})
    logger.debug("http request on their end took: %s", ret.elapsed)
    ret.raise_for_status()
    logger.debug(ret.text)
    mp3 = ET.fromstring(ret.text)[1].attrib['src']
    final_url = "https://www.voiceforge.com" + mp3
    logger.info(final_url)
    if delete:
        # an amazing api call.
        sess.post("https://www.voiceforge.com/demos/deleteAudio.php").raise_for_status()
    else:
        return MyLittleResult(final_url, sess.cookies["PHPSESSID"])


async def post_hoc_delete(phpsess):
    "VOICEFORGE: wipeout files even after you closed the session"
    requests.post("https://www.voiceforge.com/demos/deleteAudio.php", cookies={"PHPSESSID": phpsess}).raise_for_status()


async def tacotron(content: str, taco_server: str, session: aiohttp.ClientSession) -> None:
    "connect to local tacotron model."
    async with session.get(f"{taco_server}/meta/status.json", raise_for_status=True) as ret_status:
        data = await ret_status.json()
        logger.info(data)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    target = " ".join(sys.argv[1:])
    if target == "":
        target = "feeeeeeeet"
    mk_audio(target)
