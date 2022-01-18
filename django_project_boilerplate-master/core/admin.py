from django.contrib import admin

from .models import Item, OrderItem, Order, Payment, Coupons, Refund, Address

def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refunds=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'ordered', 'being_delivery', 'received', 'refunds', 'refund_granted', 'billing_address', 'shipping_address', 'payment', 'coupon']

    list_display_links = ['user', 'billing_address', 'payment', 'coupon','shipping_address']

    list_filter = ['ordered', 'being_delivery', 'received', 'refunds', 'refund_granted']

    search_fields = ['user__username', 'ref_code']
    
    actions = [make_refund_accepted]

def update_request_refund(request, queryset, modeladmin):
    queryset.update(refunds=False, refund_granted=True)

class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'first_name',
        'last_name',
        'email',
        'address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = [
        'user',
        'first_name',
        'last_name',
        'country',
        'address_type'
    ]
    search_fields = [
        'user',
        'first_name',
        'last_name'
    ]

admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupons)
admin.site.register(Refund)
admin.site.register(Address, AddressAdmin)

class MyAdmin(admin.ModelAdmin):
     def has_add_permission(self, request, obj=None):
        return False
