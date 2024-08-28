from djongo import models

class Genre(models.Model):
    name = models.CharField(max_length=255)

class Track(models.Model):
    isrc = models.CharField(max_length=255)
    track_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    youtube_url = models.URLField()
    album_cover_url = models.URLField()
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

class ViewCountEntry(models.Model):
    current_timestamp = models.DateTimeField()
    view_count = models.BigIntegerField()
    delta_count = models.BigIntegerField()

    class Meta:
        abstract = True 

class ViewCounts(models.Model):
    Spotify = models.ArrayField(
        model_container=ViewCountEntry,
        model_form_class=None,
    )
    Youtube = models.ArrayField(
        model_container=ViewCountEntry,
        model_form_class=None,
    )

    class Meta:
        abstract = True 

class HistoricalTrackView(models.Model):
    isrc = models.CharField(max_length=255)
    view_counts = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
