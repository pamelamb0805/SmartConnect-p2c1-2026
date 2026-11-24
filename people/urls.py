from rest_framework.routers import DefaultRouter
from .views import PersonViewSet

router = DefaultRouter()
router.register(r"personas", PersonViewSet, basename="persona")

urlpatterns = router.urls