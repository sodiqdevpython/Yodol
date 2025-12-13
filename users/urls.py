from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenBlacklistView, TokenRefreshView

urlpatterns = [
    path('sign-up/', views.SignUpView.as_view(), name='sign-up'),
    path('verify/', views.UserVerifyView.as_view(), name='verify-account'),
    path('generate-new-verify/', views.GenerateNewVerifyView.as_view(), name='new-verify'),
    path('change-main-info/', views.ChangeUserMainInfoView.as_view(), name='change-main-info'),
    path('finish-profile/', views.ChangeProfilePicture.as_view(), name='finish-profile'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token-refresh/', TokenRefreshView.as_view()),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('me/', views.ProfileInfoView.as_view(), name='profile-info'),
]
