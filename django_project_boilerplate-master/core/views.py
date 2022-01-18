from django.conf import settings
from django.core import exceptions
from django.http.response import BadHeaderError, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .models import Item, OrderItem, Order, Address, Payment, Coupons, Refund
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from .forms import RegistrationForm, CheckoutForm, CouponForm, RefundForm
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.contrib.auth.models import User

import random
import string
import stripe
stripe.api_key = "sk_test_4eC39HqLyjWDarjtT1zdp7dc"

def item_list(request):
    context = {
        'items': Item.objects.all()
        
    }
    return render(request, "itemlist.html", context)

def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid

class checkout(View):   
    def get(self, *args, **kwargs):
        try:
            couponform = CouponForm()
            form = CheckoutForm()
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'form': form,
                'order': order,
                'coupon': couponform,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user = self.request.user, 
                address_type = 'S',
                default = True
            )
            if shipping_address_qs.exists():
                context.update({ 'default_shipping_address': shipping_address_qs[0] })

            billing_address_qs = Address.objects.filter(
                user = self.request.user, 
                address_type = 'B',
                default = True
            )
            if billing_address_qs.exists():
                context.update({ 'default_billing_address': billing_address_qs[0] })

            return render(self.request, 'checkout-page.html', context)      
        except ObjectDoesNotExist:
            messages.info(self.request, "The order doesn't exist")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered="False")
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                use_default_billing = form.cleaned_data.get('use_default_billing')
                if use_default_shipping:
                    print('Using default shipping address')
                    address_qs = Address.objects.filter(
                        user = self.request.user, 
                        address_type = 'S',
                        default = True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No shipping address available")
                        return redirect("core:checkout")
                else:
                    print('User are using new shipping address')
                    first_name_shipping_address = form.cleaned_data.get('first_name_shipping_address')
                    last_name_shipping_address = form.cleaned_data.get('last_name_shipping_address')
                    email_shipping_address = form.cleaned_data.get('email_shipping_address')
                    address_shipping_address = form.cleaned_data.get('address_shipping_address')
                    country_shipping_address = form.cleaned_data.get('country_shipping_address')
                    zip_shipping_address = form.cleaned_data.get('zip_shipping_address')
                    default_shipping = form.cleaned_data.get('set_default_shipping')

                    if is_valid_form(['address_shipping_address', 'country_shipping_address', 'zip_shipping_address']):
                        shipping_address = Address(
                            user = self.request.user,
                            first_name = first_name_shipping_address,
                            last_name = last_name_shipping_address,
                            email = email_shipping_address,
                            address = address_shipping_address,
                            country = country_shipping_address,
                            zip = zip_shipping_address,
                            address_type = 'S'
                        )
                        if default_shipping:
                            shipping_address.default = True
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.warning(self.request, "Invalid form")
                        return redirect("core:checkout")

                same_billing_address = form.cleaned_data.get('same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print('Using default billing address')
                    address_qs = Address.objects.filter(
                        user = self.request.user, 
                        address_type = 'B',
                        default = True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, "No billing address available")
                        return redirect("core:checkout")
                else:
                    print('User are using new billing address')
                    first_name_billing_address = form.cleaned_data.get('first_name_billing_address')
                    last_name_billing_address = form.cleaned_data.get('last_name_billing_address')
                    email_billing_address = form.cleaned_data.get('email_billing_address')
                    address_billing_address = form.cleaned_data.get('address_billing_address')
                    country_billing_address = form.cleaned_data.get('country_billing_address')
                    zip_billing_address = form.cleaned_data.get('zip_billing_address')
                    default_billing = form.cleaned_data.get('set_default_billing')

                    if is_valid_form(['address_billing_address', 'country_billing_address', 'zip_billing_address']):
                        billing_address = Address(
                            user = self.request.user,
                            first_name = first_name_billing_address,
                            last_name = last_name_billing_address,
                            email = email_billing_address,
                            address = address_billing_address,
                            country = country_billing_address,
                            zip = zip_billing_address,
                            address_type = 'B'
                        )
                        if default_billing:
                            billing_address.default = True
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.warning(self.request, "Invalid form")
                        return redirect("core:checkout")

                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'COD':
                    try: 
                        subject = "thanks " + order.user.username + " for your ordering"
                        order_item = order.items.all()
                        message = "You have order "
                        for items in order_item:
                            message += items.item.title + ", "
                        from_mail = "nnguythanh@gmail.com"
                        to_mail = order.shipping_address.email
                        try:
                            send_mail(subject, message, from_mail, [to_mail])
                        except BadHeaderError:
                            return HttpResponse('Invalid Header found')
                    except:
                        messages.info(self.request, "Error occur")
                        return redirect("core:checkout")   
                    return redirect("core:home")
                elif payment_option == 'P':
                    return redirect("core:payment", payment_option='paypal')
                else:
                    messages.warning(self.request, "Failed checkout")
                    return redirect("core:checkout")

            else:
                messages.warning(self.request, "Invalid payment option")
                return redirect("core:checkout")
        except ObjectDoesNotExist:
            messages.info(self.request, "You haven't bought anything yet")
            return redirect("core:order-summary")
        
class PaymentOption(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        
        context = {
            'order': order,
            'DISPLAY_COUPON_FORM': False
        }
        return render(self.request, "payment.html", context)
        """ else:
            messages.warning(self.request, "You haven't add billing address yet")
            return redirect("core:checkout") """

    def post(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
        except:
            messages.info(self.request, "You haven't bought anything yet")
            return redirect("core:home")
        token = self.request.POST.get('stripeToken')
        if order.coupon:
            amount = int(order.total_price() * 100)
        else:
            amount = int(order.total_price_order_summary() * 100)

        order_items = order.items.all()
        order_items.update(ordered=True)
        for item in order_items:
            item.save()

        """ create payment """
        payment = Payment()
        payment.stripe_charge_id = "1234"
        payment.user = self.request.user
        if order.coupon:    
            payment.amount = int(order.total_price() * 100)
        else:
            payment.amount = int(order.total_price_order_summary() * 100)
        payment.save()
        order.payment = payment

        order.ordered = True

        order.ref_code = create_ref_code()

        order.save()

        
        subject = "thanks " + order.user.username + " for your ordering"
        order_item = order.items.all()
        message = "You have order "
        for items in order_item:
            message += items.item.title + ", "
        from_mail = "nnguythanh@gmail.com"
        to_mail = order.shipping_address.email
        try:
            send_mail(subject, message, from_mail, [to_mail])
        except BadHeaderError:
            return HttpResponse('Invalid Header found')

        if order.payment == 'S':
            payment = Payment()
            payment.user = self.request.user
            payment.amount = order.total_price()
            payment.save()
                
            """ order.ordered = True """
            order.payment = payment
            
            order.save()
            messages.success(self.request, "You have successfully ordered")
            return redirect("/")

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token
            )
                
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.total_price()
            payment.save()
                
            """ order.ordered = True """
            order.payment = payment
            
            order.save()
            messages.success(self.request, "You have successfully ordered")
            return redirect("/")

        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            
            messages.error(self.request, f"{err.get('message')}")
            return redirect("/")
        except stripe.error.RateLimitError as e:
            messages.error(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, "Paypal error")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            messages.error(self.request, "Authentication error")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            messages.error(self.request, "API connection error")
            return redirect("/")

        except stripe.error.StripeError as e:
            messages.error(self.request, "Stripe error")
            return redirect("/")

        except Exception as e:
            messages.error(self.request, "A serious error occur")
            return redirect("/")


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"

class OrderSummaryView(LoginRequiredMixin, View):
    login_url = '/login'
    redirect_field_name = 'redirect_to'   
    def get(self, *avrgs, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered="False")
            context = {
                'objects': order
            }
            return render(self.request, "order_summary.html", context) 
        except ObjectDoesNotExist:
            messages.info(self.request, "You haven't bought anything yet")
            return redirect("/")

class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"
    def get_context_data(self, *args, **kwargs):
        context = super(ItemDetailView, self).get_context_data(*args, **kwargs)
        context['item_list'] = Item.objects.all()
        return context

@login_required(login_url='/login')
def add_to_cart(request, slug):
    login_url = '/login'
    redirect_field_name = 'redirect_to'  
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False,
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():   
        order = order_qs[0]
        # check if the item is existed in order item
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item was added to your cart")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart")
            return redirect("core:product", slug=slug)
    else:
        order_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=order_date)
        
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart")
        return redirect("core:product", slug=slug)
    return redirect("core:product", slug=slug)

@login_required(login_url='/login')
def add_single_item_to_cart(request, slug):
    login_url = '/login'
    redirect_field_name = 'redirect_to'  
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():   
        order = order_qs[0]
        # check if the item is existed in order item
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "The amount of this item was changed")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "The amount of this item was changed")
            return redirect("core:order-summary") 
    

@login_required(login_url='/login')
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():   
        order = order_qs[0]
        # check if the item is existed in order item
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart")
            return redirect("core:product", slug=slug)
        else:           
            # add a message saying that a user's ordered dosent contain this order
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        # add a message saying that a user havent ordered yet
        messages.info(request, "You didn't order anything")
        return redirect("core:product", slug=slug)

@login_required(login_url='/login')
def remove_the_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():   
        order = order_qs[0]
        # check if the item is existed in order item
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart")
            return redirect("core:order-summary")
        else:           
            # add a message saying that a user's ordered dosent contain this order
            messages.info(request, "This item was not in your cart")
            return redirect("core:order-summary")
    

@login_required(login_url='/login')
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user, 
        ordered=False
    )
    if order_qs.exists():   
        order = order_qs[0]
        # check if the item is existed in order item
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            
            if order_item.quantity == 0:
                order.items.remove(order_item)
            else: 
                order_item.quantity -= 1
            order_item.save()
            messages.info(request, "The amount of this item was changed")
            return redirect("core:order-summary")
    

def login(request):
    return render(request, 'login-page.html')

def register(request):
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            mail = form.cleaned_data.get('email')
            if User.objects.filter(email = mail).first():
                messages.error(request, "This email is already taken")
                return redirect('core:register')
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/')
    return render(request, 'register.html', {'form': form})

""" def get_coupon(request, code):
    try:
        coupons = Coupons.objects.get(code=code)
        return coupons
    except:
        messages.info(request, "Coupons dosen't exist")
        return redirect("core:checkout") """

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False) 
                try:
                    coupons = Coupons.objects.get(code=code)
                    order.coupon = coupons
                    order.save()
                    messages.success(self.request, "Your coupon is activate")
                    return redirect("core:checkout")
                except:
                    messages.info(self.request, "Coupons dosen't exist")
                    return redirect("core:checkout")
                     
            except ObjectDoesNotExist:
                messages.info(self.request, "The order doesn't exist")
                return redirect("core:checkout")

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k = 20))

class RefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "request-refund.html", context)
    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refunds = True
                order.save()
            
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, "Your request for refund was sent")
                return redirect("core:request-refund")
            except ObjectDoesNotExist:
                messages.info(self.request, "Order dosen't exist")
                return redirect("core:request-refund")


def search(request):
    search = request.GET['search']
    item=Item.objects.filter(title = search)
    return render(request, 'search.html', {'item':item})

def CategoryRau(request):
    item=Item.objects.filter(category = 'R')
    return render(request, 'rau.html', {'item':item})

def CategoryCu(request):
    item=Item.objects.filter(category = 'C')
    return render(request, 'rau.html', {'item':item})








