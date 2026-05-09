from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("users/me/", views.UserDetailView.as_view(), name="user_detail"),
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("accounts/new/", views.AccountCreateView.as_view(), name="account_create"),
    path("accounts/search/", views.AccountSearchView.as_view(), name="account_search"),
    path("accounts/<int:pk>/", views.AccountDetailView.as_view(), name="account_detail"),
    path("opportunities/", views.OpportunityListView.as_view(), name="opportunity_list"),
    path("opportunities/new/", views.OpportunityCreateView.as_view(), name="opportunity_create"),
    path("opportunities/<int:pk>/", views.OpportunityDetailView.as_view(), name="opportunity_detail"),
]
