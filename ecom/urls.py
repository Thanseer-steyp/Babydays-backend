from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("register/", include("api.v1.register.urls")),
        path("user/", include("api.v1.user.urls")),
        path("manager/", include("api.v1.manager.urls")),
        path("public/", include("api.v1.public.urls")),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    