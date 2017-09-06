import os
import logging

import click

logger = logging.getLogger(__name__)
folder = click.get_app_dir("Pyborg")


def mk_folder():
    try:
        os.makedirs(os.path.join(folder, "brains"))
        os.makedirs(os.path.join(folder, "tmp"))
        logger.info("pyborg folder created.")
    except OSError:
        logger.info("pyborg folder already exists.")