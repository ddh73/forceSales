from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("accounts/", views.AccountListView.as_view(), name="account_list"),
    path("accounts/new/", views.AccountCreateView.as_view(), name="account_create"),
    path("accounts/<int:pk>/", views.AccountDetailView.as_view(), name="account_detail"),
    path("products/", views.ProductListView.as_view(), name="product_list"),
    path("products/new/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("opportunities/", views.OpportunityListView.as_view(), name="opportunity_list"),
    path("opportunities/new/", views.OpportunityCreateView.as_view(), name="opportunity_create"),
    path("opportunities/<int:pk>/", views.OpportunityDetailView.as_view(), name="opportunity_detail"),
]
