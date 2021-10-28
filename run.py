import os

from threebot import threebot

def load_config_from_env():
    return {
        'profile': os.getenv('THREEBOT_PROFILE'),
        'token': os.getenv('THREEBOT_TOKEN')
    }

if __name__ == '__main__':
    config = load_config_from_env();
    if config['token']:
        print(f'Running bot using the {config["profile"]} profile.')
        threebot.run(config['token'])