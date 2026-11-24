
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    RoleViewSet,
    PersonRoleViewSet,
    CredentialViewSet,
    AccessRecordViewSet,
    CheckAccessView,
)

router = DefaultRouter()

router.register("roles", RoleViewSet, basename="role")
router.register("person-roles", PersonRoleViewSet, basename="person-role")
router.register("credentials", CredentialViewSet, basename="credential")
router.register("access-records", AccessRecordViewSet, basename="access-record")

urlpatterns = [
    path(
        "check-access/",
        CheckAccessView.as_view(),
        name="check-access",
    ),
]

urlpatterns += router.urls
