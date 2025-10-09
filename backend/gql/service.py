import strawberry
from core.constants import IFRAME_CONFIGS, SERVICE_CONFIGS, GraphQLCacheKey
from core.models.genre_service import ServiceModel
from core.services.iframe_service import generate_iframe_src
from core.utils.redis_cache import CachePrefix, redis_cache_get, redis_cache_set
from domain_types.types import IframeConfig

from backend.gql.button_labels import (
    ButtonLabelType,
    generate_misc_button_labels,
    generate_rank_button_labels,
    generate_service_button_labels,
)


@strawberry.type
class ServiceModelType:
    """Service model type for Django ServiceModel data."""

    name: str
    display_name: str
    icon_url: str


@strawberry.type
class ServiceType:
    """Service configuration type with button labels."""

    name: str
    display_name: str
    url: str | None = None
    icon_url: str
    url_field: str | None = None
    source_field: str | None = None
    button_labels: list[ButtonLabelType] = strawberry.field(
        description="Button labels for this service", default_factory=list
    )


@strawberry.type
class IframeConfigType:
    """Iframe configuration type for service embedding."""

    service_name: str
    embed_base_url: str
    embed_params: str | None = None
    allow: str
    height: str
    referrer_policy: str | None = None


@strawberry.type
class ServiceQuery:
    """Service-related GraphQL queries."""

    @strawberry.field(description="Get all services from the database")
    def services(self) -> list[ServiceModelType]:
        """Get all services from the database."""
        services = ServiceModel.objects.all()
        return [
            ServiceModelType(name=service.name, display_name=service.display_name, icon_url=service.icon_url)
            for service in services
        ]

    @strawberry.field(description="Get service configurations with button labels")
    def service_configs(self) -> list[ServiceType]:
        """Get service configurations with button labels."""
        cache_key_data = GraphQLCacheKey.ALL_SERVICE_CONFIGS

        cached_result = redis_cache_get(CachePrefix.GQL_SERVICE_CONFIGS, cache_key_data)

        if cached_result is not None:
            # Convert cached dict data back to ServiceType with ButtonLabelType objects
            service_configs = []
            for config in cached_result:
                # Convert button_labels from dict to ButtonLabelType objects
                button_labels = [ButtonLabelType(**bl) for bl in config["button_labels"]]
                config_copy = config.copy()
                config_copy["button_labels"] = button_labels
                service_configs.append(ServiceType(**config_copy))
            return service_configs

        service_configs = []
        cache_data = []
        for service_name, config in SERVICE_CONFIGS.items():
            button_labels = generate_service_button_labels(service_name)

            service_type = ServiceType(
                name=service_name,
                display_name=config["display_name"],
                icon_url=config["icon_url"],
                url_field=config.get("url_field"),
                source_field=config.get("source_field"),
                button_labels=button_labels,
            )
            service_configs.append(service_type)

            # For caching, convert ButtonLabelType objects to dict
            button_label_dicts = [bl.to_dict() for bl in button_labels]
            cache_data.append(
                {
                    "name": service_name,
                    "display_name": config["display_name"],
                    "icon_url": config["icon_url"],
                    "url_field": config.get("url_field"),
                    "source_field": config.get("source_field"),
                    "button_labels": button_label_dicts,
                }
            )

        redis_cache_set(CachePrefix.GQL_SERVICE_CONFIGS, cache_key_data, cache_data)

        return service_configs

    @strawberry.field(description="Get iframe configurations for all services")
    def iframe_configs(self) -> list[IframeConfigType]:
        """Get iframe configurations for all services."""
        cache_key_data = GraphQLCacheKey.ALL_IFRAME_CONFIGS

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

    @strawberry.field(description="Generate an iframe URL for a service and track")
    def generate_iframe_url(self, service_name: str, track_url: str) -> str | None:
        """Generate an iframe URL for a service and track."""
        cache_key_data = GraphQLCacheKey.iframe_url(service_name, track_url)

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

    @strawberry.field(description="Get button labels for ranking/sorting functionality")
    def rank_button_labels(self, rank_type: str) -> list[ButtonLabelType]:
        """Get button labels for ranking/sorting functionality."""
        cache_key_data = GraphQLCacheKey.rank_button_labels(rank_type)

        cached_result = redis_cache_get(CachePrefix.GQL_BUTTON_LABELS, cache_key_data)

        if cached_result is not None:
            return [ButtonLabelType(**label) for label in cached_result]

        button_labels = generate_rank_button_labels(rank_type)
        # Convert ButtonLabelType objects to dict for caching
        cache_data = [bl.to_dict() for bl in button_labels]

        redis_cache_set(CachePrefix.GQL_BUTTON_LABELS, cache_key_data, cache_data)

        return button_labels

    @strawberry.field(description="Get button labels for miscellaneous UI elements")
    def misc_button_labels(self, button_type: str, context: str | None = None) -> list[ButtonLabelType]:
        """Get button labels for miscellaneous UI elements."""
        cache_key_data = GraphQLCacheKey.misc_button_labels(button_type, context)

        cached_result = redis_cache_get(CachePrefix.GQL_BUTTON_LABELS, cache_key_data)

        if cached_result is not None:
            return [ButtonLabelType(**label) for label in cached_result]

        button_labels = generate_misc_button_labels(button_type, context)
        # Convert ButtonLabelType objects to dict for caching
        cache_data = [bl.to_dict() for bl in button_labels]

        redis_cache_set(CachePrefix.GQL_BUTTON_LABELS, cache_key_data, cache_data)

        return button_labels
