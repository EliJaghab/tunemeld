import graphene
from core.constants import IFRAME_CONFIGS, SERVICE_CONFIGS
from core.graphql.button_labels import (
    ButtonLabelType,
    generate_misc_button_labels,
    generate_rank_button_labels,
    generate_service_button_labels,
)
from core.models.genre_service import ServiceModel
from core.services.iframe_service import generate_iframe_src
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import ButtonLabelData, IframeConfig, ServiceConfigWithLabels
from graphene_django import DjangoObjectType


class ServiceModelType(DjangoObjectType):
    class Meta:
        model = ServiceModel
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
        return ServiceModel.objects.all()

    def resolve_service_configs(self, info):
        cache_key_data = "all_service_configs"

        cached_result = redis_cache_get(CachePrefix.GQL_SERVICE_CONFIGS, cache_key_data)

        if cached_result is not None:
            return [ServiceType(**config) for config in cached_result]

        service_configs = []
        cache_data = []
        for service_name, config in SERVICE_CONFIGS.items():
            button_labels = generate_service_button_labels(service_name)
            button_label_data = [
                ButtonLabelData(bl.button_type, bl.context, bl.title, bl.aria_label).to_dict() for bl in button_labels
            ]

            domain_service_config = ServiceConfigWithLabels(
                name=service_name,
                display_name=config["display_name"],
                icon_url=config["icon_url"],
                url_field=config.get("url_field"),
                source_field=config.get("source_field"),
                button_labels=button_label_data,
            )
            service_config_dict = domain_service_config.to_dict()
            cache_data.append(service_config_dict)
            service_configs.append(ServiceType(**service_config_dict))

        redis_cache_set(CachePrefix.GQL_SERVICE_CONFIGS, cache_key_data, cache_data)

        return service_configs

    def resolve_iframe_configs(self, info):
        cache_key_data = "all_iframe_configs"

        cached_result = redis_cache_get(CachePrefix.GQL_IFRAME_CONFIGS, cache_key_data)

        if cached_result is not None:
            return [IframeConfigType(**config) for config in cached_result]

        iframe_configs = []
        cache_data = []
        for service_name, config in IFRAME_CONFIGS.items():
            domain_iframe_config = IframeConfig(
                service_name=service_name,
                embed_base_url=config["embed_base_url"],
                embed_params=config.get("embed_params"),
                allow=config["allow"],
                height=config["height"],
                referrer_policy=config.get("referrer_policy"),
            )
            iframe_config_dict = domain_iframe_config.to_dict()
            cache_data.append(iframe_config_dict)
            iframe_configs.append(IframeConfigType(**iframe_config_dict))

        redis_cache_set(CachePrefix.GQL_IFRAME_CONFIGS, cache_key_data, cache_data)

        return iframe_configs

    def resolve_generate_iframe_url(self, info, service_name, track_url):
        cache_key_data = f"iframe_url:service={service_name}:url={track_url}"

        cached_result = redis_cache_get(CachePrefix.GQL_IFRAME_URL, cache_key_data)

        if cached_result is not None:
            return cached_result

        try:
            iframe_url = generate_iframe_src(service_name, track_url)
            redis_cache_set(CachePrefix.GQL_IFRAME_URL, cache_key_data, iframe_url)
            return iframe_url
        except ValueError:
            redis_cache_set(CachePrefix.GQL_IFRAME_URL, cache_key_data, None)
            return None

    def resolve_rank_button_labels(self, info, rank_type):
        cache_key_data = f"rank_button_labels:type={rank_type}"

        cached_result = redis_cache_get(CachePrefix.GQL_BUTTON_LABELS, cache_key_data)

        if cached_result is not None:
            return [ButtonLabelType(**label) for label in cached_result]

        button_labels = generate_rank_button_labels(rank_type)
        cache_data = [bl.to_dict() for bl in button_labels]

        redis_cache_set(CachePrefix.GQL_BUTTON_LABELS, cache_key_data, cache_data)

        return [ButtonLabelType(**bl.to_dict()) for bl in button_labels]

    def resolve_misc_button_labels(self, info, button_type, context=None):
        cache_key_data = f"misc_button_labels:type={button_type}:context={context}"

        cached_result = redis_cache_get(CachePrefix.GQL_BUTTON_LABELS, cache_key_data)

        if cached_result is not None:
            return [ButtonLabelType(**label) for label in cached_result]

        button_labels = generate_misc_button_labels(button_type, context)
        cache_data = [bl.to_dict() for bl in button_labels]

        redis_cache_set(CachePrefix.GQL_BUTTON_LABELS, cache_key_data, cache_data)

        return [ButtonLabelType(**bl.to_dict()) for bl in button_labels]
