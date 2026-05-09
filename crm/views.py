from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """Send authenticated users to the CRM dashboard and others to login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return redirect("login")


class DashboardView(LoginRequiredMixin, TemplateView):
    """Starter authenticated dashboard with admin and standard-user views."""

    template_name = "crm/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["is_crm_admin"] = user.is_superuser or user.groups.filter(name="CRM Admin").exists()
        context["is_standard_user"] = user.groups.filter(name="Standard User").exists()
        return context
