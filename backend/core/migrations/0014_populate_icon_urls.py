from django.db import migrations


def populate_icon_urls(apps, schema_editor):
    Genre = apps.get_model('core', 'Genre')
    Rank = apps.get_model('core', 'Rank')

    # Icon URL mappings from constants
    genre_icon_urls = {
        "dance": "/images/genre-dance.png",
        "rap": "/images/genre-rap.png",
        "country": "/images/genre-country.png",
        "pop": "/images/genre-pop.png",
    }

    rank_icon_urls = {
        "tunemeld_rank": "/images/tunemeld.png",
        "spotify_views_rank": "/images/spotify_logo.png",
        "youtube_views_rank": "/images/youtube_logo.png",
    }

    # Update genres
    for genre in Genre.objects.all():
        if genre.name in genre_icon_urls:
            genre.icon_url = genre_icon_urls[genre.name]
            genre.save()

    # Update ranks
    for rank in Rank.objects.all():
        if rank.name in rank_icon_urls:
            rank.icon_url = rank_icon_urls[rank.name]
            rank.save()


def reverse_populate_icon_urls(apps, schema_editor):
    Genre = apps.get_model('core', 'Genre')
    Rank = apps.get_model('core', 'Rank')

    # Clear icon URLs
    Genre.objects.all().update(icon_url="")
    Rank.objects.all().update(icon_url="")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_update_icon_fields_to_url'),
    ]

    operations = [
        migrations.RunPython(populate_icon_urls, reverse_populate_icon_urls),
    ]
