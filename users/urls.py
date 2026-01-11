from django.urls import path, reverse_lazy
from . import views
from users.views import RegisterView, ProfileView, ProfileUpdateView, ProfileListView, DisableProfileView
from django.contrib.auth.views import LoginView, LogoutView
from users.apps import UsersConfig
from django.contrib.auth import views as auth_views

app_name = UsersConfig.name
# app_name = 'users'


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='mailing:home'), name='logout'),
    path('email-confirm/<str:token>/', views.email_verification, name='email-confirm'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile-edit/', ProfileUpdateView.as_view(), name='edit-profile'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset_form.html',
             email_template_name="users/password_reset_email.html",
             success_url=reverse_lazy("users:password_reset_done")
         ), name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url=reverse_lazy("users:password_reset_complete")
         ), name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    path('profiles/', ProfileListView.as_view(), name='profile_list'),
    path('disable-profile/<int:pk>/', DisableProfileView.as_view(), name='disable_profile'),
]
