from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("accounts/<int:pk>/", views.AccountDetailView.as_view(), name="account_detail"),
]
