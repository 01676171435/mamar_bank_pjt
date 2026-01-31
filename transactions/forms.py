from django import forms
from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

        # def __init__(self, *args, **kwargs):
        # self.account = kwargs.pop('account')
        # CreateView class theka jokhon call kora hoy TransactionForm ka tokhon account key argument ta pathano hoy
        # ja recieve kora  TransactionForm ar __init__ funtion ar **kwargs paramiter
        # kwargs theka account key argument ke pop kore anlam

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')

        # super().__init__(*args, **kwargs)
        # This calls the parent class (forms.ModelForm)
        # initializer to set up the form with the remaining arguments (*args and kwargs).
        # It prepares the form fields like any normal form.
        super().__init__(*args, **kwargs)

        # ei field disable thakbe
        self.fields['transaction_type'].disabled = True
        # user er theke hide kora thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):

        # self.instance.account = self.account
        # The account field on the Transaction model is being set to the value of self.account
        # (which was passed when the form was initialized).
        # By using self.instance.account,
        # you are directly assigning the account value to the specific
        # transaction instance that will be saved to the database.
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance

        # return super().save():
        # When super().save() is called, ModelForm's save method takes care of saving self.instance
        # (which is your Transaction instance)  So, ModelForm ensures that account.self.instance and self.instance.balance_after_transaction values
        # are saved to the Transaction model
        return super().save()


# Since DepositForm inherits from TransactionForm, the amount field is also available in DepositForm.
class DepositForm(TransactionForm):
    def clean_amount(self):  # amount field ke filter korbo
        min_deposit_amount = 100
        # user er fill up kora form theke amra amount field er value ke niye aslam, 50
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance  # 1000
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance:  # amount = 5000, tar balance ache 200
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount


class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        return amount
