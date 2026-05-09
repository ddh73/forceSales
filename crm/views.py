from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView

from .forms import AccountForm, OpportunityForm, OpportunityLineItemFormSet, ProductForm
from .models import Account, Opportunity, Product


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
        context["opportunity_count"] = Opportunity.objects.count()
        context["product_count"] = Product.objects.count()
        return context


class AccountListView(LoginRequiredMixin, ListView):
    """Display the current list of CRM accounts."""

    context_object_name = "accounts"
    model = Account
    paginate_by = 25
    template_name = "crm/account_list.html"


class AccountCreateView(LoginRequiredMixin, TemplateView):
    """Allow normal users to create account records."""

    template_name = "crm/account_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or AccountForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save()
            messages.success(request, "Account created.")
            return redirect(account.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


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


class ProductListView(LoginRequiredMixin, ListView):
    """Display products available for opportunity line items."""

    context_object_name = "products"
    model = Product
    paginate_by = 25
    template_name = "crm/product_list.html"


class ProductCreateView(LoginRequiredMixin, TemplateView):
    """Allow users to create products for the catalog."""

    template_name = "crm/product_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or ProductForm()
        context["product"] = None
        return context

    def post(self, request, *args, **kwargs):
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, "Product created.")
            return redirect(product.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


class ProductDetailView(LoginRequiredMixin, TemplateView):
    """Display and edit a product record."""

    template_name = "crm/product_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["product"] = self.product
        context["form"] = kwargs.get("form") or ProductForm(instance=self.product)
        return context

    def post(self, request, *args, **kwargs):
        form = ProductForm(request.POST, instance=self.product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect(self.product.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form))


class OpportunityListView(LoginRequiredMixin, ListView):
    """Display sales opportunities."""

    context_object_name = "opportunities"
    model = Opportunity
    paginate_by = 25
    template_name = "crm/opportunity_list.html"

    def get_queryset(self):
        return Opportunity.objects.select_related("account").prefetch_related("line_items")


class OpportunityCreateView(LoginRequiredMixin, TemplateView):
    """Allow users to create opportunity records."""

    template_name = "crm/opportunity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or OpportunityForm()
        return context

    def post(self, request, *args, **kwargs):
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save()
            messages.success(request, "Opportunity created. Add product line items to build the amount.")
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
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opportunity"] = self.opportunity
        context["form"] = kwargs.get("form") or OpportunityForm(instance=self.opportunity)
        context["line_item_formset"] = kwargs.get("line_item_formset") or OpportunityLineItemFormSet(
            instance=self.opportunity
        )
        context["has_products"] = Product.objects.filter(active=True).exists()
        return context

    def post(self, request, *args, **kwargs):
        form = OpportunityForm(request.POST, instance=self.opportunity)
        line_item_formset = OpportunityLineItemFormSet(request.POST, instance=self.opportunity)
        if form.is_valid() and line_item_formset.is_valid():
            form.save()
            line_item_formset.save()
            messages.success(request, "Opportunity updated.")
            return redirect(self.opportunity.get_absolute_url())
        return self.render_to_response(self.get_context_data(form=form, line_item_formset=line_item_formset))
