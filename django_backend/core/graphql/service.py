import graphene
from core.models.b_genre_service import Service
from graphene_django import DjangoObjectType


class ServiceModelType(DjangoObjectType):
    class Meta:
        model = Service
        fields = ("name", "display_name", "icon_url")


class ServiceType(graphene.ObjectType):
    name = graphene.String(required=True)
    display_name = graphene.String(required=True)
    url = graphene.String(required=True)
    icon_url = graphene.String(required=True)


class ServiceQuery(graphene.ObjectType):
    services = graphene.List(ServiceModelType)

    def resolve_services(self, info):
        return Service.objects.all()
