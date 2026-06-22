from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from users.auth_views import AuthSessionView, CookieTokenObtainPairView, CookieTokenRefreshView, LogoutView
from django.http import HttpResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", lambda request: HttpResponse("ok")),
    path("api/auth/login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/session/", AuthSessionView.as_view(), name="auth_session"),
    path("api/", include("users.urls")),
    path("api/", include("social.urls")),
]

if settings.DEBUG or True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
