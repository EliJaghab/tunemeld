from lambda_functions.soundcloud_extractor import SoundCloudExtractor
from lambda_functions.constants import SOUNDCLOUD_EDM_URL

def lambda_handler(event, context):
    soundcloud_extractor = SoundCloudExtractor(SOUNDCLOUD_EDM_URL)
    return soundcloud_extractor.get_soundcloud_tracks()

