
try:
    import requests
    print("Successfully imported requests.")
    raise ValueError
except ImportError:
    print("Failed to import requests.")
    
    
from extractor import Extractor

extractor = Extractor()
print(extractor.get_soundcloud_tracks())
