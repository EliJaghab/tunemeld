from ..transform import get_isrc


def test_never_be_lonely_by_jax_jones_and_zoe_wees():
    track_name = "Never Be Lonely"
    artist_name = "Jax Jones & Zoe Wees"
    url = "https://music.apple.com/us/album/never-be-lonely/1727350063?i=1727350064"
    expected = "GBUM72400217"  # The expected ISRC for the exact match
    actual = get_isrc(track_name, artist_name, url)
    assert expected == actual, f"Failed for track '{track_name}' by '{artist_name}'"
