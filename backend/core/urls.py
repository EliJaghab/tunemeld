from core import views
from core.graphql import schema
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from graphene_django.views import GraphQLView

urlpatterns = [
    path("", views.root, name="root"),
    path("health/", views.health, name="health"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
    path(
        "edm-events/",
        views.get_edm_events,
        name="get_edm_events",
    ),
    path(
        "gql/",
        csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema)),
        name="graphql",
    ),
]
