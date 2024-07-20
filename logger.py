# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 19:18:50 2024

@author: Usuario
"""

import logging
import os
from datetime import datetime
import functools

def setup_logger():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('ComicViewer')
    logger.setLevel(logging.DEBUG)

    log_file = os.path.join(log_dir, f'comic_viewer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()

def log_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering function: {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Exiting function: {func.__name__}")
        return result
    return wrapper