from django.db import models
from django.core.files.base import ContentFile
import qrcode
from io import BytesIO
from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Max
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    restaurant_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='restaurant_logos/', blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    theme_color = models.CharField(max_length=7, default='#3b82f6')  # Default blue
    cart_enabled = models.BooleanField(default=True)

    MENU_DISPLAY_CHOICES = [
        ('grid', 'Item First View'),
        ('category_first', 'Category First View'),
    ]
    menu_display_mode = models.CharField(
        max_length=20,
        choices=MENU_DISPLAY_CHOICES,
        default='grid'
    )
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        Profile.objects.create(user=instance)

class Table(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)  # Add this line
    number = models.IntegerField()
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    has_pending_orders = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'number')  # Ensure table numbers are unique per user

    def save(self, *args, **kwargs):
        if not self.qr_code:
            qr_code_file = self.generate_qr_code()
            self.qr_code.save(qr_code_file.name, qr_code_file, save=False)
        super().save(*args, **kwargs)

    def generate_qr_code(self):
        table_url = f"http://localhost:8000/table/{self.number}"
        qr = qrcode.make(table_url)
        buffer = BytesIO()
        qr.save(buffer)
        buffer.seek(0)
        return ContentFile(buffer.getvalue(), f"table_{self.number}_qr.png")
    
    def __str__(self):
        return f"Table {self.number}"


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True) 
    name = models.CharField(max_length=100, )
    sort_id=models.IntegerField(blank=True, null=True)
    available = models.BooleanField(default=True)  # Add this field
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)

    class Meta:
        unique_together = ('user', 'name')  # Same name allowed for different users
        ordering = ['sort_id']
    def __str__(self):
        if self.user:  # Check if user exists
            return f"{self.name}"
        return self.name  # Fallback to just the name if no user
    
    def save(self, *args, **kwargs):
        # If the category already exists and the sort_id is changing
        if self.pk:
            original_sort_id = Category.objects.get(pk=self.pk).sort_id
            if original_sort_id != self.sort_id:
                self.handle_sort_id_conflict()
        else:
            # If sort_id is not set, assign the next available one
            if self.sort_id is None:
                max_sort_id = Category.objects.aggregate(Max('sort_id'))['sort_id__max'] or 0
                self.sort_id = max_sort_id + 1

        super().save(*args, **kwargs)

    def handle_sort_id_conflict(self):
        # If the sort_id already exists, we need to shift the existing categories
        # Find categories with a sort_id greater than or equal to the new sort_id
        conflicting_categories = Category.objects.filter(sort_id__gte=self.sort_id).exclude(pk=self.pk)

        for category in conflicting_categories:
            category.sort_id += 1
            category.save()

    

class MenuItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True) 
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True, related_name="menu_items")
    image = models.ImageField(upload_to="menu_items/", null=True, blank=True)


    class Meta:
        unique_together = ('user', 'name', 'category')

    def save(self, *args, **kwargs):
        # If category is not available, force item to be unavailable
        if self.category and not self.category.available:
            self.available = False
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.name} - {self.category.name}"


from django.db import models
from django.db.models import Sum, F
import uuid  # For combined_id

# class Order(models.Model):
#     table = models.ForeignKey('Table', on_delete=models.CASCADE)
#     customer_name = models.CharField(max_length=255, blank=True, null=True)
#     customer_phone = models.CharField(max_length=15, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
#     status = models.CharField(max_length=50, choices=[
#         ('Pending', 'Pending'),
#         ('Completed', 'Completed'),
#         ('Cancelled', 'Cancelled')
#     ], default='Pending')

#     discount = models.DecimalField(max_digits=10, decimal_places=2, default=2)
#     sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9)
#     cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9)
#     final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     billed = models.BooleanField(default=False)
#     combined_id = models.UUIDField(default=None, null=True, blank=True)

#     def calculate_total(self):
#         total = self.items.aggregate(
#             total=Sum(F('quantity') * F('price'))
#         )['total'] or 0
#         self.total = total
#         return total
    
#     def calculate_sgst(self):
#         return (self.total * self.sgst_rate) / 100

#     def calculate_cgst(self):
#         return (self.total * self.cgst_rate) / 100

#     def calculate_discount(self):
#         return (self.total * self.discount) / 100

#     def calculate_final_total(self):
#         sgst = self.calculate_sgst()
#         cgst = self.calculate_cgst()
#         discount = self.calculate_discount()
#         self.final_total = self.total + sgst + cgst - discount
#         return self.final_total

#     def save(self, *args, **kwargs):
#         """ Ensure final_total is always calculated before saving """
#         if self.final_total is None:  # Only calculate if not already set
#             self.calculate_final_total()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"Order {self.id} - Table {self.table.id if self.table else 'N/A'}"

from django.contrib.postgres.fields import ArrayField
import json

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True) 
    table = models.ForeignKey('Table', on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=255, blank=True, null=True)  
    customer_phone = models.CharField(max_length=15, blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    status = models.CharField(max_length=50, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        
    ], default='Pending')  
    user_order_id = models.PositiveIntegerField(blank=True, null=True, editable=False)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=2)  # Discount on the total
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9)  # SGST rate, e.g., 9%
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9)
    # gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18)  # GST rate, e.g., 18%
    final_total = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True )  # Final total after applying GST and discount

    billed = models.BooleanField(default=False)
    combined_id = models.UUIDField(default=None, null=True, blank=True)  # Identifies grouped orders

    # PAYMENT_METHODS = [
    #     ('cash', 'Cash'),
    #     ('gpay', 'GPay'),
    #     ('card', 'Credit Card'),
    #     ('pending', 'Pending'),
    # ]
    # payment_method = models.CharField(
    #     max_length=20,
    #     choices=PAYMENT_METHODS,
    #     default='pending'
    # )
    

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('gpay', 'GPay'),
        ('card', 'Credit Card'),
    ]
    
    # Replace with this implementation
    _payment_methods = models.TextField(
        default='[]',
        blank=True
    )
    payment_amounts = models.JSONField(default=list, blank=True)
    
    # def save_payment_methods(self, methods, amounts):
    #     self.payment_methods = methods
    #     self.payment_amounts = amounts
    #     self.save()

    def get_payment_methods_with_amounts(self):
        """Returns dict of {method: amount} for this order"""
        if hasattr(self, 'payment_amounts') and self.payment_amounts:
            # If payment amounts are stored separately
            return {method: amount for method, amount in zip(self.payment_methods, self.payment_amounts)}
        
        # Default equal distribution if amounts not stored
        if self.payment_methods and self.final_total:
            amount_per_method = self.final_total / len(self.payment_methods)
            return {method: amount_per_method for method in self.payment_methods}
        return {}

    @classmethod
    def get_combined_payment_summary(cls, orders):
        """Returns combined payment summary for multiple orders"""
        summary = {}
        for order in orders:
            methods_with_amounts = order.get_payment_methods_with_amounts()
            for method, amount in methods_with_amounts.items():
                summary[method] = summary.get(method, 0) + amount
        return summary
    
    @property
    def payment_methods(self):
        try:
            return json.loads(self._payment_methods)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @payment_methods.setter
    def payment_methods(self, value):
        self._payment_methods = json.dumps(value if value else [])
    

    class Meta:
        unique_together = ('user', 'user_order_id')  # Ensures uniqueness per user
    
    def calculate_total(self):
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0
        self.total = total
        self.save()
        return total
    
    def calculate_sgst(self):
        return (self.total * self.sgst_rate) / 100

    def calculate_cgst(self):
        return (self.total * self.cgst_rate) / 100

    def calculate_discount(self):
        return (self.total * self.discount) / 100
    
    def calculate_final_total(self):
        sgst = self.calculate_sgst()
        cgst = self.calculate_cgst()
        discount = self.calculate_discount()
        return self.total + sgst + cgst - discount  # Just return the value, don't save

    def save(self, *args, **kwargs):
        if not self.user_order_id:
            last_order = Order.objects.filter(user=self.user).order_by('-user_order_id').first()
            # Handle case where last_order exists but user_order_id is None
            self.user_order_id = (last_order.user_order_id + 1) if last_order and last_order.user_order_id is not None else 1
            
        
        if self.final_total is None:  # Calculate only if not set
            self.final_total = self.calculate_final_total()  # Assign value instead of saving
        super().save(*args, **kwargs)


    # def calculate_final_total(self):
    #     sgst = self.calculate_sgst()
    #     cgst = self.calculate_cgst()
    #     discount = self.calculate_discount()
    #     self.final_total = self.total + sgst + cgst - discount
    #     self.save()
    #     return self.final_total
    # def save(self, *args, **kwargs):
    #     if self.final_total is None:  # Only calculate if it's not set
    #         self.calculate_final_total()
    #     super().save(*args, **kwargs)


    def __str__(self):
        return f"Order {self.id} - Table {self.table.id if self.table else 'N/A'}"
  
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey('MenuItem', on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_completed = models.BooleanField(default=False)  # ✅ New field to track strike-through
    # preferences = models.TextField(blank=True, null=True) 
    notes = models.TextField(blank=True, null=True)
    def save(self, *args, **kwargs):
        if self.menu_item and not self.item_name:
            self.item_name = self.menu_item.name  # Store the name permanently
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.item_name}"


# class OrderItem(models.Model):
#     order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
#     # menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
#     menu_item = models.ForeignKey('MenuItem', on_delete=models.SET_NULL, null=True, blank=True)
#     item_name = models.CharField(max_length=255,null=True, blank=True )
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
#     status = models.CharField(
#         max_length=20,
#         choices=[('Pending', 'Pending'), ('Completed', 'Completed')],
#         default='Pending')

#     # def __str__(self):
#     #     return f"{self.quantity} x {self.menu_item.name}"

#     # def __str__(self):
#     #     return f"{self.quantity} x {self.menu_item.name}"

    
#     def save(self, *args, **kwargs):
#         if self.menu_item and not self.item_name:
#             self.item_name = self.menu_item.name  # Store the name permanently
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.quantity} x {self.item_name}"

receiver(post_save, sender=Order)
def update_table_pending_status(sender, instance, **kwargs):
    table = instance.table
    table.has_pending_orders = table.orders.filter(user=table.user,status='Pending').exists()
    table.save()

# def __str__(self):
#     return f"Table {self.number}"




# from django.contrib.auth.models import AbstractUser

# class Restaurant(models.Model):
#     name = models.CharField(max_length=100)
#     address = models.TextField()
#     phone = models.CharField(max_length=15)
#     logo = models.ImageField(
#         upload_to='restaurant_logos/',
#         null=True,
#         blank=True,
#         help_text="Upload your restaurant logo"
#     )
#     #gst_number = models.CharField(max_length=15, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['name']
#         verbose_name_plural = "Restaurants"

#     def __str__(self):
#         return self.name

# class RestaurantUser(AbstractUser):
#     restaurant = models.OneToOneField(
#         Restaurant,
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name='admin_user'
#     )
#     is_restaurant_admin = models.BooleanField(default=False)
    
#     class Meta:
#         verbose_name = "Restaurant User"
#         verbose_name_plural = "Restaurant Users"

#     def __str__(self):
#         return f"{self.username} ({self.restaurant.name if self.restaurant else 'No Restaurant'})"


# models.py
# class OrderPayment(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
#     method = models.CharField(max_length=20, choices=Order.PAYMENT_METHODS)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.method} - ₹{self.amount}"
