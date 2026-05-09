from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from .forms import AccountForm
from .models import Account


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
        context["account_count"] = Account.objects.count()
        return context


class AccountListView(LoginRequiredMixin, ListView):
    """Display the current list of CRM accounts."""

    context_object_name = "accounts"
    model = Account
    paginate_by = 25
    template_name = "crm/account_list.html"


class AccountDetailView(LoginRequiredMixin, TemplateView):
    """Display an account record and allow inline field editing."""

    template_name = "crm/account_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(Account, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.account
        context["form"] = kwargs.get("form") or AccountForm(instance=self.account)
        return context

    def post(self, request, *args, **kwargs):
        form = AccountForm(request.POST, instance=self.account)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated.")
            return redirect(self.account.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))
