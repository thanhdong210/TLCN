from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django_countries.fields import CountryField
# Create your models here.

CATEGORY_CHOICES = (
    ('R', 'Rau'),
    ('C', 'Cu'),
)

LABEL_CHOICES = (
    ('B', 'black'),
    ('BL', 'blue'),
    ('R', 'red')
)

ADDRESS_CHOICES = (
    ('S', 'shipping'),
    ('B', 'billing')
)

class Item(models.Model):
    title = models.CharField(max_length=100)

    price = models.FloatField()

    discount_price = models.FloatField(blank=True, null=True)

    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)

    label = models.CharField(choices=LABEL_CHOICES, max_length=2)

    slug = models.SlugField()

    description = models.TextField()

    image = models.ImageField(null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    ordered = models.BooleanField(default=False)

    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        else:
            return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    ref_code = models.CharField(max_length=30, blank=True, null=True)

    items = models.ManyToManyField(OrderItem)

    start_date = models.DateTimeField(auto_now_add=True)

    ordered_date = models.DateTimeField()

    ordered = models.BooleanField(default=False)

    billing_address = models.ForeignKey("Address", related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)

    shipping_address = models.ForeignKey("Address", related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)

    payment = models.ForeignKey("Payment", on_delete=models.SET_NULL, blank=True, null=True)

    coupon = models.ForeignKey("Coupons", on_delete=models.SET_NULL, blank=True, null=True)

    being_delivery = models.BooleanField(default=False)

    received = models.BooleanField(default=False)

    refunds = models.BooleanField(default=False)

    refund_granted = models.BooleanField(default=False)

    '''
    1. Add to cart
    2. Adding billing address
    (Failed checkout)
    3. Payment
    (preprocessing, processing, packaging, etc)
    4. Being delivery
    5. Received
    6.Refunds

    '''

    def __str__(self):
        return self.user.username

    def total_price(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

    def total_price_order_summary(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.final_price()
        return total

    def cart_item_count(self):       
        qs = Order.objects.filter(ordered=False)
        if qs.exists():
            return qs[0].items.count()
        return 0


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

    email = models.CharField(max_length=100)
    
    address = models.CharField(max_length=100)

    country = CountryField(multiple=False)

    zip = models.CharField(max_length=100)

    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)

    default = models.BooleanField(default=False)

    def __str__(self):
        return self.address

    class Meta:
        verbose_name_plural = 'Address'

class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.stripe_charge_id

class Coupons(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code

class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.CharField(max_length=100)
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.order.user.username}"

""" class UserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_id = models.CharField(blank=True, null=True, max_length=50)
    use_old_cardpayment = models.BooleanField(required=False)

    def __str__(self):
        return self.user.user_name
 """
class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        user_profile = UserProfile.objects.create(user=instance)

""" post_save.connect(user_profile_receiver, sender=settings.AUTH_USER_MODEL) """
""" post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL) """