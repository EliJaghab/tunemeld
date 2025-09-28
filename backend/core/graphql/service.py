import graphene
from core.constants import IFRAME_CONFIGS, SERVICE_CONFIGS
from core.graphql.button_labels import (
    ButtonLabelType,
    generate_misc_button_labels,
    generate_rank_button_labels,
    generate_service_button_labels,
)
from core.models.genre_service import Service
from core.services.iframe_service import generate_iframe_src
from graphene_django import DjangoObjectType


class ServiceModelType(DjangoObjectType):
    class Meta:
        model = Service
        fields = ("name", "display_name", "icon_url")


class ServiceType(graphene.ObjectType):
    name = graphene.String(required=True)
    display_name = graphene.String(required=True)
    url = graphene.String()
    icon_url = graphene.String(required=True)
    url_field = graphene.String()
    source_field = graphene.String()
    button_labels = graphene.List(ButtonLabelType, description="Button labels for this service")


class IframeConfigType(graphene.ObjectType):
    service_name = graphene.String(required=True)
    embed_base_url = graphene.String(required=True)
    embed_params = graphene.String()
    allow = graphene.String(required=True)
    height = graphene.String(required=True)
    referrer_policy = graphene.String()


class ServiceQuery(graphene.ObjectType):
    services = graphene.List(ServiceModelType)
    service_configs = graphene.List(ServiceType)
    iframe_configs = graphene.List(IframeConfigType)
    generate_iframe_url = graphene.String(
        service_name=graphene.String(required=True), track_url=graphene.String(required=True)
    )
    rank_button_labels = graphene.List(ButtonLabelType, rank_type=graphene.String(required=True))
    misc_button_labels = graphene.List(
        ButtonLabelType, button_type=graphene.String(required=True), context=graphene.String()
    )

    def resolve_services(self, info):
        return Service.objects.all()

    def resolve_service_configs(self, info):
        return [
            ServiceType(
                name=service_name,
                display_name=config["display_name"],
                icon_url=config["icon_url"],
                url_field=config.get("url_field"),
                source_field=config.get("source_field"),
                button_labels=generate_service_button_labels(service_name),
            )
            for service_name, config in SERVICE_CONFIGS.items()
        ]

    def resolve_iframe_configs(self, info):
        return [
            IframeConfigType(
                service_name=service_name,
                embed_base_url=config["embed_base_url"],
                embed_params=config.get("embed_params"),
                allow=config["allow"],
                height=config["height"],
                referrer_policy=config.get("referrer_policy"),
            )
            for service_name, config in IFRAME_CONFIGS.items()
        ]

    def resolve_generate_iframe_url(self, info, service_name, track_url):
        try:
            return generate_iframe_src(service_name, track_url)
        except ValueError:
            return None

    def resolve_rank_button_labels(self, info, rank_type):
        return generate_rank_button_labels(rank_type)

    def resolve_misc_button_labels(self, info, button_type, context=None):
        return generate_misc_button_labels(button_type, context)
