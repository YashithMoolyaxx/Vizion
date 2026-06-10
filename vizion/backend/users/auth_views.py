from django.conf import settings
from django.contrib.auth import login as django_login, logout as django_logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

REFRESH_COOKIE = "vizion_refresh"
COOKIE_PATH = "/api/auth/"


def _cookie_kwargs():
    return {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Lax",
        "path": COOKIE_PATH,
    }


def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        REFRESH_COOKIE,
        str(refresh_token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        **_cookie_kwargs(),
    )
    return response


class CookieTokenObtainPairView(TokenObtainPairView):
    """Issue short-lived JWT access token + HttpOnly refresh cookie; establish Django session."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        django_login(request, user)
        request.session["auth_via"] = "jwt"

        response = Response(
            {
                "access": access,
                "token_type": "Bearer",
                "session_active": bool(request.session.session_key),
            },
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, refresh)
        return response


class CookieTokenRefreshView(APIView):
    """Exchange HttpOnly refresh cookie for a new access token."""

    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(REFRESH_COOKIE) or request.data.get("refresh")
        if not raw:
            return Response({"detail": "Refresh token not provided."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(raw)
            access = str(refresh.access_token)
        except (InvalidToken, TokenError):
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({"access": access, "token_type": "Bearer"})


class LogoutView(APIView):
    """Invalidate server session and clear refresh cookie."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        django_logout(request)
        response = Response({"detail": "Successfully logged out."})
        response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
        return response


class AuthSessionView(APIView):
    """Report dual auth state: JWT bearer + Django session."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "authenticated": True,
                "user_id": request.user.id,
                "username": request.user.username,
                "session_key": request.session.session_key,
                "session_auth": request.session.get("auth_via", "session"),
                "jwt_required": True,
            }
        )
