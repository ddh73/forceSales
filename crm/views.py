from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, TemplateView

from .access import get_object_access, scope_queryset_to_readable_records, user_can_edit_record, user_can_read_record
from .forms import AccountForm, OpportunityForm, OpportunityLineItemFormSet
from .models import Account, Opportunity, Product


class HomeView(TemplateView):
    """Send authenticated users to the CRM dashboard and others to login."""

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return redirect("login")


class DashboardView(LoginRequiredMixin, TemplateView):
    """Authenticated dashboard focused on useful CRM work lists."""

    template_name = "crm/dashboard.html"

    def get_open_opportunities(self):
        """Return the current user's readable in-progress opportunities."""

        opportunities = (
            Opportunity.objects.filter(stage=Opportunity.IN_PROGRESS)
            .select_related("account")
            .prefetch_related("line_items__product")
        )
        return scope_queryset_to_readable_records(opportunities, self.request.user)[:10]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["open_opportunities"] = self.get_open_opportunities()
        context["can_create_opportunity"] = get_object_access(self.request.user, Opportunity).can_create
        user = self.request.user
        context["is_crm_admin"] = user.is_superuser or user.groups.filter(name="CRM Admin").exists()
        context["is_standard_user"] = user.groups.filter(name="Standard User").exists()
        context["account_count"] = scope_queryset_to_readable_records(Account.objects.all(), user).count()
        context["opportunity_count"] = scope_queryset_to_readable_records(Opportunity.objects.all(), user).count()
        return context


class AccountSearchView(LoginRequiredMixin, View):
    """Return matching accounts for opportunity account lookup."""

    def get(self, request, *args, **kwargs):
        query = request.GET.get("q", "").strip()
        accounts = Account.objects.none()
        if query:
            accounts = scope_queryset_to_readable_records(Account.objects.all(), request.user)
            for term in query.split():
                accounts = accounts.filter(
                    Q(first_name__icontains=term)
                    | Q(middle_name__icontains=term)
                    | Q(last_name__icontains=term)
                    | Q(tax_id_number__icontains=term)
                )
        results = [{"id": account.pk, "label": account.full_name} for account in accounts[:10]]
        return JsonResponse({"results": results})


class AccountListView(LoginRequiredMixin, ListView):
    """Display the current list of CRM accounts."""

    context_object_name = "accounts"
    model = Account
    paginate_by = 25
    template_name = "crm/account_list.html"

    def get_queryset(self):
        return scope_queryset_to_readable_records(Account.objects.all(), self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_account"] = get_object_access(self.request.user, Account).can_create
        return context


class AccountCreateView(LoginRequiredMixin, TemplateView):
    """Allow normal users to create account records."""

    template_name = "crm/account_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        access = get_object_access(self.request.user, Account)
        if not access.can_create:
            raise PermissionDenied
        context["form"] = kwargs.get("form") or AccountForm()
        return context

    def post(self, request, *args, **kwargs):
        if not get_object_access(request.user, Account).can_create:
            raise PermissionDenied
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.owner = request.user
            account.save()
            form.save_custom_fields(account)
            messages.success(request, "Account created.")
            return redirect(account.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


class AccountDetailView(LoginRequiredMixin, TemplateView):
    """Display an account record and allow inline field editing."""

    template_name = "crm/account_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.account = get_object_or_404(Account, pk=kwargs["pk"])
        if not user_can_read_record(request.user, self.account):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account"] = self.account
        context["can_edit_account"] = user_can_edit_record(self.request.user, self.account)
        context["form"] = kwargs.get("form") or AccountForm(instance=self.account)
        return context

    def post(self, request, *args, **kwargs):
        if not user_can_edit_record(request.user, self.account):
            raise PermissionDenied
        form = AccountForm(request.POST, instance=self.account)
        if form.is_valid():
            form.save()
            messages.success(request, "Account updated.")
            return redirect(self.account.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


class OpportunityListView(LoginRequiredMixin, ListView):
    """Display sales opportunities."""

    context_object_name = "opportunities"
    model = Opportunity
    paginate_by = 25
    template_name = "crm/opportunity_list.html"

    def get_queryset(self):
        opportunities = Opportunity.objects.select_related("account").prefetch_related("line_items")
        return scope_queryset_to_readable_records(opportunities, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_opportunity"] = get_object_access(self.request.user, Opportunity).can_create
        return context


class OpportunityCreateView(LoginRequiredMixin, TemplateView):
    """Allow users to create opportunity records."""

    template_name = "crm/opportunity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not get_object_access(self.request.user, Opportunity).can_create:
            raise PermissionDenied
        context["form"] = kwargs.get("form") or OpportunityForm(user=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        if not get_object_access(request.user, Opportunity).can_create:
            raise PermissionDenied
        form = OpportunityForm(request.POST, user=request.user)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.owner = request.user
            opportunity.save()
            messages.success(request, "Opportunity created. Add product line items.")
            return redirect(opportunity.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


class OpportunityDetailView(LoginRequiredMixin, TemplateView):
    """Display an opportunity and manage its product-backed line items."""

    template_name = "crm/opportunity_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.opportunity = get_object_or_404(
            Opportunity.objects.select_related("account").prefetch_related("line_items__product"),
            pk=kwargs["pk"],
        )
        if not user_can_read_record(request.user, self.opportunity):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opportunity"] = self.opportunity
        context["can_edit_opportunity"] = user_can_edit_record(self.request.user, self.opportunity)
        context["form"] = kwargs.get("form") or OpportunityForm(instance=self.opportunity, user=self.request.user)
        context["line_item_formset"] = kwargs.get("line_item_formset") or OpportunityLineItemFormSet(
            instance=self.opportunity
        )
        context["has_products"] = Product.objects.filter(active=True).exists()
        return context

    def post(self, request, *args, **kwargs):
        if not user_can_edit_record(request.user, self.opportunity):
            raise PermissionDenied
        form = OpportunityForm(request.POST, instance=self.opportunity, user=request.user)
        line_item_formset = OpportunityLineItemFormSet(request.POST, instance=self.opportunity)
        if form.is_valid() and line_item_formset.is_valid():
            form.save()
            line_item_formset.save()
            messages.success(request, "Opportunity updated.")
            return redirect(self.opportunity.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form, line_item_formset=line_item_formset))
