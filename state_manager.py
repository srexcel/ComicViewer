# -*- coding: utf-8 -*-
"""
Created on Thu Jul 11 19:27:34 2024

@author: Usuario
"""

import json
from logger import logger

STATE_FILE = 'comic_state.json'

# def save_state(file_path, current_page, current_panel, viewing_panels):
#     state = {
#         'last_file': file_path,
#         'current_page': current_page,
#         'current_panel': current_panel,
#         'viewing_panels': viewing_panels
#     }
#     with open(STATE_FILE, 'w') as f:
#         json.dump(state, f)
#     logger.info(f"Saved state: Page {current_page}, Panel {current_panel}, Viewing panels: {viewing_panels}")

def load_state():
    try:
        with open('comic_state.json', 'r') as f:
            state = json.load(f)
        logger.info(f"Loaded state: Page {state['current_page']}, Panel {state['current_panel']}, Viewing panels: {state['viewing_panels']}")
        return state
    except FileNotFoundError:
        logger.info("No previous state found")
        return None
    
    
def save_state(file_path, current_page, current_panel, viewing_panels):
    state = {
        'last_file': file_path,
        'current_page': int(current_page),
        'current_panel': int(current_panel),
        'viewing_panels': bool(viewing_panels)
    }
    with open('comic_state.json', 'w') as f:
        json.dump(state, f)
    logger.info(f"Saved state: Page {current_page}, Panel {current_panel}, Viewing panels: {viewing_panels}")    