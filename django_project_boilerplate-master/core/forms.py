from django import forms
import re
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.forms.fields import CharField
from django.forms.widgets import Textarea
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICES = (
    ('COD', 'COD'),
    ('P', 'Paypal')
)

class RegistrationForm(forms.Form):
    username = forms.CharField(label='Tài khoản', max_length=30)
    email = forms.EmailField(label='Email')
    password1 = forms.CharField(label='Mật khẩu', widget=forms.PasswordInput())
    password2 = forms.CharField(label='Nhập lại mật khẩu', widget=forms.PasswordInput())

    if User.objects.filter(email = email).first():
        raise forms.ValidationError("Mật khẩu không hợp lệ!")   

    def clean_password2(self):
        if 'password1' in self.cleaned_data:
            password1 = self.cleaned_data['password1']
            password2 = self.cleaned_data['password2']
            if password1==password2 and password1:
                return password2
        raise forms.ValidationError("Mật khẩu không hợp lệ!")    

    def clean_username(self):
        username= self.cleaned_data['username']
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError("Tên tài khoản không hợp lệ (tên tài khoản có ký tự đặc biệt)")    
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError("Tên tài khoản đã tồn tại")
    
    def save(self):
        User.objects.create_user(username=self.cleaned_data['username'], email=self.cleaned_data['email'], password=self.cleaned_data['password1'])


class CheckoutForm(forms.Form):
    first_name_shipping_address = forms.CharField(required=False)
    last_name_shipping_address = forms.CharField(required=False)
    email_shipping_address = forms.CharField(required=False)
    address_shipping_address = forms.CharField(required=False)
    country_shipping_address = CountryField(blank_label='(select country)').formfield(required=False, widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
    }))
    zip_shipping_address = CharField(required=False)

    
    first_name_billing_address = forms.CharField(required=False)
    last_name_billing_address = forms.CharField(required=False)
    email_billing_address = forms.CharField(required=False)
    address_billing_address = forms.CharField(required=False)
    country_billing_address = CountryField(blank_label='(select country)').formfield(required=False, widget=CountrySelectWidget(attrs={
        'class': 'custom-select d-block w-100',
    }))
    zip_billing_address = CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

    payment_option = forms.ChoiceField(widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipients username',
        'aria-describedby': 'basic-addon2',
        'autocomplete': 'off'
    }))

class RefundForm(forms.Form):
    ref_code = forms.CharField(widget=forms.TextInput(attrs={
        'autocomplete': 'off'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'row': 4
    }))
    email = forms.EmailField()
    
