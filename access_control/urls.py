
from rest_framework.routers import DefaultRouter

from .views import (
    RoleViewSet,
    PersonRoleViewSet,
    CredentialViewSet,
    AccessRecordViewSet,
)

router = DefaultRouter()
router.register("roles", RoleViewSet, basename="role")
router.register("person-roles", PersonRoleViewSet, basename="person-role")
router.register("credentials", CredentialViewSet, basename="credential")
router.register("access-records", AccessRecordViewSet, basename="access-record")

urlpatterns = router.urls

