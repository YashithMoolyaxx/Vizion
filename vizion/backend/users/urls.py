from django.urls import path

from .views import AvatarUploadView, MeView, RegisterView

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/avatar/", AvatarUploadView.as_view(), name="avatar-upload"),
]
