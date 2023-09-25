from soundcloud_extractor import SoundCloudExtractor
from constants import SOUNDCLOUD_EDM_URL

def lambda_handler(event, context):
    soundcloud_extractor = SoundCloudExtractor(SOUNDCLOUD_EDM_URL)
    return soundcloud_extractor.get_soundcloud_tracks()

