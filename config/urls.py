from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # API de personas
    path("api/", include("people.urls")),

    # API de infraestructura
    path("api/", include("infrastructure.urls")),
]