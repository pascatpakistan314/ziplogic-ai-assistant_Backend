from django.urls import path
from .views import RegisterView, VerifyCodeView,LoginView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify-code'),
    path('login/', LoginView.as_view(), name='login'),
]
