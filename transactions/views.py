from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transactions.constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from datetime import datetime
from django.db.models import Sum
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
)
from transactions.models import Transaction

# By default, CreateView will look for a ModelForm that corresponds to the model specified in the view
# (in this case, Transaction). Since TransactionCreateMixin sets model = Transaction,
# Django automatically uses TransactionForm as the form for this view, assuming no other form is explicitly set.

# ja form ba view  LoginRequiredMixin class inherite korbe shie form ba view ka access korta hola userlogin thaka lagbe


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')
    
    # get_form_kwargs() ফাংশনটি Django-এর CreateView-এর অংশ, 
    # এবং এটি মূলত ফর্মে অতিরিক্ত তথ্য পাঠানোর জন্য ব্যবহৃত হয়।
    def get_form_kwargs(self):

        # kwargs = super().get_form_kwargs()
        # It first calls the parent (CreateView) version of get_form_kwargs,
        # which will return the default form arguments
        # in default form there are having
        # data, files,instance:
        # instance: The specific instance of the model being created or edited (in this case,
        # a Transaction instance for Transaction model), which would usually be empty to a CreateView
        #  for it’s creating a new instance.

        kwargs = super().get_form_kwargs()

        # kwargs.update({'account': self.request.user.account})
        # It then adds an additional key-value pair to the kwargs dictionary: 'account': self.request.user.account.
        # self.request.user.account is not available in the default form
        # self.request.user.account in your view comes from Django’s authentication system.

        # LoginRequiredMixin is not responsible for providing self.request.user.account. Instead,
        # LoginRequiredMixin simply ensures that a user must be logged in to access the view.
        # If the user is not authenticated, LoginRequiredMixin redirects them to the login page.

        kwargs.update({

            'account': self.request.user.account
        })

        # In the get_form_kwargs method of TransactionCreateMixin, the return kwargs statement
        # returns a dictionary (kwargs) to the caller,which in this case is Django’s CreateView.
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context


# Since DepositMoneyView inherits from TransactionCreateMixin,
# it inherits all of TransactionCreateMixin's methods and attributes, including:
# template_name, model, success_url, get_form_kwargs,get_context_data:

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    # get_initial provides a dictionary of initial values for form fields,
    # in this case, setting 'transaction_type': DEPOSIT.
    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    # def form_valid(self, form):
    # akhane form_valid(self,form) funtion ar form paramiter a DopositForm theka amount field value thake ja daye CreateView class
    # DepositMoneyView class inherite kora CreateView class ka TransactionCreateMixin class ar maddoma

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        # if not account.initial_deposit_date:
        #     now = timezone.now()
        #     account.initial_deposit_date = now
        # amount = 200, tar ager balance = 0 taka new balance = 0+200 = 200
        account.balance += amount
        account.save(
            update_fields=[
                'balance'
            ]
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        # super().form_valid(form) funtion suposed to be return TransactionCreateMixin but it actually return to CreateView
        # super().form_valid(form) in DepositMoneyView ultimately calls CreateView’s form_valid method.
        # Saves the form instance to the database, creating a new Transaction model instance.
        return super().form_valid(form)


# akhane DepositMoneyView class hit korla  model Transaction ar 'transaction_type' field ar value set kora daye hoy get_initial funtion ar madoma.
# DepositMoneyView class thake return kori super().form_valid(form) form argument ar modda  model Transaction ar amount field value thake je ta pie amra  DepositForm class theka
# super().form_valid(form) funtion ar form argument return hoy CreateView class a CreateView  model Transaction ar amount field valu sorasori save kora daye. TransactionCreateMixin class ar modda
# kwargs = super().get_form_kwargs() call korla Createview class thake form daya hoy kwargs ar modda tarpor kwargs.update kori 'account': self.request.user.account diya
# pora yabar return kortaci CreateView class ke  CreateView class padiye TransactionForm class ke TransactionForm ar modda
# ja recieve kora  TransactionForm ar __init__ funtion ar **kwargs paramiter pora kwargs theka account key argument ke pop kore anlam  self.account = kwargs.pop('account') akhon self.account = account holo tarpor TransactionForm class ar def save(self, commit=True): funtion ar modda
# model Transaction ar 'account' field a rakha hoy self.account ja self.instance.account = self.account abong
# model Transaction ar 'balance_after_transaction' field a rakha hoy self.account.balance  ja self.instance.balance_after_transaction = self.account.balance
# ai vabe model Transaction ar potekta instance toyri hoy


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        self.request.user.account.balance -= form.cleaned_data.get('amount')
        # balance = 300
        # amount = 5000
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )

        return super().form_valid(form)


class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account, transaction_type=3, loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )

        return super().form_valid(form)


class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0  # filter korar pore ba age amar total balance ke show korbe

    # You don’t need to call get_queryset
    # The get_queryset method is called automatically by Django's ListView class
    # as part of its internal process for generating the view.
    # When a user requests the TransactionReportView,
    # Django processes this request and initiates rendering for the page associated with this view.
    # at that moment ListView call get_queryset(self) funtion to get list,
    # ListView's job is to retrieve a list of items and pass them to the template.

    def get_queryset(self):
        # queryset = super().get_queryset()
        # It first calls the parent (ListView) version of get_queryset,
        # queryset = super().get_queryset() calls the get_queryset method of the parent class (ListView),
        # By default, ListView’s get_queryset returns all objects for the specified model—in this case Transaction model.
        # Since TransactionReportView specifies model = Transaction, calling super().get_queryset() initially retrieves all transaction records in the Transaction model.

        # through .filter(account=self.request.user.account)
        # filters all transaction instance associated with the logged-in user
        # by matching the account field with self.request.user.account.
        queryset = super().get_queryset().filter(

            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            # akhane queryset ar modda logged-in user ar transaction instance ba object ache model Transaction ar
            # akhon start_date porer abong end_date yager transaction instance gula queryset a filter hoba
            queryset = queryset.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date)

            # akhon start_date porer abong end_date yager transaction instance gular amount field total sum queryset a filter hoba
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance

        # So, return queryset.distinct() returns the filtered list of transactions back to Django’s ListView,
        # which will then use it to render the page with only unique, filtered transactions for the logged-in user.
        # This queryset is ultimately used to render the list of transactions in the HTML template.
        return queryset.distinct()  # unique queryset hote hobe

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account,
            'balance': self.balance
        })

        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
            # Reduce the loan amount from the user's balance
            # 5000, 500 + 5000 = 5500
            # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('transactions:loan_list')
            else:
                messages.error(
                    self.request,
                    f'Loan amount is greater than available balance'
                )

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'  # loan list ta ei loans context er moddhe thakbe

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(
            account=user_account, transaction_type=3)
        print(queryset)
        return queryset


# Create your views here.
