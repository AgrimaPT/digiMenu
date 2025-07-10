# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from .models import Table, MenuItem, Order, OrderItem,Category
from .forms import CustomerDetailsForm,CategoryForm, MenuItemForm,Profile
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import F, Case, When, Value
import json
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils.timezone import localtime
from django.shortcuts import get_list_or_404
from collections import defaultdict
from .consumers import OrderConsumer
import uuid
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .models import OrderItem
from .forms import UserUpdateForm, ProfileUpdateForm




# alertmessage=False

# def table_view(request, table_number):
#     table = get_object_or_404(Table, number=table_number)
#     menu_items = MenuItem.objects.filter(available=True)
#     category = Category.objects.annotate(
#         effective_sort_id=Case(
#             When(sort_id__isnull=True, then=Value(999999)),  # Assign a high value if sort_id is None
#             default=F('sort_id'),
#             # output_field=models.IntegerField()
#         )
#     ).order_by('effective_sort_id') 
    
#     if request.method == "POST":
#         order = Order.objects.create(table=table)
#         for item_id, quantity in request.POST.items():
#             if item_id.startswith('menu_item_'):
#                 menu_item_id = item_id.split('_')[2]
#                 menu_item = get_object_or_404(MenuItem, id=menu_item_id)
#                 OrderItem.objects.create(order=order, menu_item=menu_item, quantity=int(quantity))
#         order.calculate_total()
#         return redirect('order_summary', order_id=order.id)
#     return render(request, 'table.html', {'table': table, 'menu_items': menu_items,'categories':category})

def table_view(request, username, table_number):
    # Verify table belongs to the user
    table = get_object_or_404(Table, number=table_number, user__username=username)
    
    restaurant_profile = get_object_or_404(Profile, user=table.user)
    if restaurant_profile.menu_display_mode == 'category_first':
        return redirect('category_grid', username=username, table_number=table_number)

    menu_items = MenuItem.objects.filter(available=True, user=table.user)
    
    categories = Category.objects.filter(user=table.user,available=True).annotate(
        effective_sort_id=Case(
            When(sort_id__isnull=True, then=Value(999999)),
            default=F('sort_id'),
            #output_field=models.IntegerField()
        )
    ).order_by('effective_sort_id')

    menu_items = MenuItem.objects.filter(
        available=True,
        user=table.user,
        category__available=True  # Only items from available categories
        
    )
    
    # if request.method == "POST":
    #     order = Order.objects.create(table=table, user=request.user)
    #     for item_id, quantity in request.POST.items():
    #         if item_id.startswith('menu_item_') and int(quantity) > 0:
    #             menu_item_id = item_id.split('_')[2]
    #             menu_item = get_object_or_404(MenuItem, id=menu_item_id, user=request.user)
    #             OrderItem.objects.create(
    #                 order=order, 
    #                 menu_item=menu_item, 
    #                 quantity=int(quantity)
    #             )
    #     order.calculate_total()
    #     return redirect('order_summary', username=request.user.username, order_id=order.id)
    
    return render(request, 'table.html', {
        'table': table,
        'menu_items': menu_items,
        'categories': categories,
        'restaurant': table.user,
        'cart_enabled': restaurant_profile.cart_enabled 
    })


def customer_details(request, username, table_number):
    # Verify table belongs to the user
    table = get_object_or_404(Table, number=table_number, user=request.user)
    
    if request.method == 'POST':
        form = CustomerDetailsForm(request.POST)
        if form.is_valid():
            request.session['customer_name'] = form.cleaned_data['name']
            request.session['customer_phone'] = form.cleaned_data['phone_number']
            return redirect('table_view', username=username, table_number=table.number)
    else:
        form = CustomerDetailsForm()
    
    return render(request, 'customer_details.html', {
        'form': form,
        'table_number': table.number,
        'current_user': request.user
    })


def order_summary(request, username, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_summary.html', {
        'order': order,
        'current_user': request.user
    })


def get_user_or_404(username):
    """Helper function to get user or return 404"""
    return get_object_or_404(User, username=username)


# @login_required
# def dashboard_home(request, username):
#     # Verify the requested user matches the logged-in user
#     if request.user.username != username:
#         messages.error(request, "You don't have permission to access this page")
#         return redirect('login')
    
#     user = get_user_or_404(username)
#     return render(request, 'dashboard/home.html', {'profile_user': user})



# def dashboard_categories(request):
#     cat=Category.objects.all()
#     if request.method == 'POST':
#         form = CategoryForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('dashboard_categories')  
#     else:
#         form = CategoryForm()

#     return render(request, 'dashboard/categories.html',{'cat':cat,'form': form})

@login_required
def dashboard_categories(request, username):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    cat = Category.objects.filter(user=user)
    
    # if request.method == 'POST':
    #     form = CategoryForm(request.POST)
    #     if form.is_valid():
    #         category = form.save(commit=False)
    #         category.user = user
    #         category.save()
    #         messages.success(request, "Category added successfully!")
    #         return redirect('dashboard_categories', username=username)
    # else:
    #     form = CategoryForm()

    return render(request, 'dashboard/categories.html', {
        'cat': cat,
        'profile_user': user
    })


@login_required
def add_category(request, username):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    
    if request.method == "POST":
        form = CategoryForm(request.POST,user=user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            messages.success(request, "Category added successfully!")
            return redirect('dashboard_categories', username=username)
    else:
        form = CategoryForm(user=user)
    
    return render(request, 'dashboard/add_category.html', {
        'form': form,
        'profile_user': user
    })


@login_required
def delete_category(request, username, category_id):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    category = get_object_or_404(Category, pk=category_id, user=user)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Category deleted successfully!")
    return redirect('dashboard_categories', username=username)


@login_required
def edit_category(request, username, category_id):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    category = get_object_or_404(Category, pk=category_id, user=user)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated successfully!")
            return redirect('dashboard_categories', username=username)
    else:
        form = CategoryForm(instance=category,user=user)

    return render(request, 'dashboard/edit_category.html', {
        'form': form,
        'category': category,
        'profile_user': user
    })

# views.py
from django.views.decorators.http import require_POST

@require_POST
@login_required
def toggle_category_availability(request, username, category_id):
    if request.user.username != username:
        return redirect('login')
    
    category = get_object_or_404(Category, id=category_id, user=request.user)
    category.available = not category.available
    category.save()
    
    # Update all items in this category
    MenuItem.objects.filter(category=category).update(available=category.available)
    
    messages.success(request, f"Category '{category.name}' is now {'available' if category.available else 'unavailable'}")
    return redirect('dashboard_categories', username=username)
    

# def dashboard_items(request):
#     item=MenuItem.objects.all()
#     if request.method == 'POST':
#         form = MenuItemForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('dashboard_items')  
#     else:
#         form = MenuItemForm()

#     return render(request, 'dashboard/items.html',{'item':item,'form': form})

@login_required
def dashboard_items(request, username):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    items = MenuItem.objects.filter(user=user)
    
    # if request.method == 'POST':
    #     form = MenuItemForm(request.POST, request.FILES)
    #     if form.is_valid():
    #         item = form.save(commit=False)
    #         item.user = user
    #         item.save()
    #         messages.success(request, "Item added successfully!")
    #         return redirect('dashboard_items', username=username)
    # else:
    #     form = MenuItemForm()

    return render(request, 'dashboard/items.html', {
        'items': items,
        
        'profile_user': user
    })

   
@login_required
def add_item(request, username):
    # Verify the requested user matches the logged-in user
    if request.user.username != username:
        messages.error(request, "You don't have permission to access this page")
        return redirect('login')
    
    user = get_user_or_404(username)
    
    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = user  # Set the owner
            item.save()
            messages.success(request, "Item added successfully!")
            return redirect('dashboard_items', username=username)  # Include username in redirect
    else:
        form = MenuItemForm(user=user)  # Pass user to form
    
    return render(request, 'dashboard/add_item.html', {
        'form': form,
        'current_user': user
    })

@login_required
def delete_item(request, username, item_id):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, pk=item_id, user=user)  # Verify ownership
        item.delete()
        messages.success(request, "Item deleted successfully!")
        return redirect('dashboard_items', username=username)  # Include username in redirect
    return redirect('dashboard_items', username=username)

@login_required
def edit_item(request, username, item_id):
    if request.user.username != username:
        return redirect('login')
    
    user = get_user_or_404(username)
    item = get_object_or_404(MenuItem, id=item_id, user=user)  # Verify ownership
    
    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES, instance=item, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Item updated successfully!")
            return redirect('dashboard_items', username=username)
    else:
        form = MenuItemForm(instance=item, user=user)
    
    return render(request, 'dashboard/edit_item.html', {
        'form': form,
        'current_user': user,
        'item': item
    })

# def update_availability(request, item_id):
#     item = get_object_or_404(MenuItem, pk=item_id)
    
#     if request.method == 'POST':
#         item.available = not item.available  # Toggle between True/False
#         item.save() 
#         messages.success(request, f"Item '{item.name}' availability updated successfully!")
#     return redirect('dashboard_items')

@login_required
def update_availability(request, username, item_id):
    # Verify the requested user matches the logged-in user
    if request.user.username != username:
        messages.error(request, "You don't have permission to update this item")
        return redirect('login')
    
    # Get the item and verify ownership
    item = get_object_or_404(MenuItem, pk=item_id, user=request.user)
    
    if request.method == 'POST':
        item.available = not item.available  # Toggle availability
        item.save()
        messages.success(request, f"'{item.name}' is now {'available' if item.available else 'unavailable'}")
    
    # Redirect back to the user's items page
    return redirect('dashboard_items', username=username)

# def confirm_order(request,table_id):
#     global alertmessage
#     if request.method == 'POST':
       
#         table = get_object_or_404(Table, id=table_id)
#         request.session['table_id'] = table.id

#         customer_name = request.POST.get('customer_name')
#         customer_phone = request.POST.get('customer_phone')
#         cart_items = request.POST.get('cart_items') 
#         if not customer_name or not customer_phone or not cart_items:
#             return render(request, 'order_confirmation.html', {
#                 'table_number': table_id,
#                 'error': 'All fields (name, phone, and cart) are required.',
#             })
#         try:
#             # Parse cart items JSON
#             cart_data = json.loads(cart_items)
#             if not isinstance(cart_data, dict):
#                 raise ValueError("Invalid cart format. Expected a dictionary.")
#         except (json.JSONDecodeError, ValueError) as e:
#             return render(request, 'order_confirmation.html', {
#                 'table_number': table_id,
#                 'error': f"Invalid cart data: {e}"
#             })
#         # Create the order object
#         order = Order.objects.create(
#             table=table,
#             customer_name=customer_name,
#             customer_phone=customer_phone,
#             status="Pending",
#             created_at=timezone.now()
#         )
#         alertmessage=True

#         for item_id, item_data in cart_data.items():
#             try:
               
#                 item = get_object_or_404(MenuItem, id=item_id)

#                 # Ensure valid data for quantity and price
#                 quantity = int(item_data.get('quantity', 0))
#                 price = float(item_data.get('price', 0.00))
#                 if quantity <= 0 or price <= 0:
#                     raise ValueError(f"Invalid quantity ({quantity}) or price ({price}) for item {item.name}.")

#                 # Create OrderItem
#                 OrderItem.objects.create(
#                     order=order,
#                     menu_item=item,
#                     item_name=item.name,
#                     quantity=quantity,
#                     price=price
#                 )
#             except (MenuItem.DoesNotExist, ValueError) as e:
#                 print(f"Skipping item due to error: {e}")
#                 continue

#         order.calculate_total()

    
#         order_items_data = [
#             {
#                 'name': item.menu_item.name,
#                 'quantity': item.quantity,
#                 'price': str(item.price),
               
#             }
#             for item in order.items.all() 
#         ]

#         # Calculate the number of pending orders per table
#         orders_by_table = {
#             table.id: Order.objects.filter(table=table, status="Pending").count()
#             for table in Table.objects.all()
#         }

      
#         order_data = {
#             'id': order.id,
#             'table': order.table.number,
#             'customer_name': order.customer_name,
#             'customer_phone': order.customer_phone,
#             'total': str(order.total),
#             'status': order.status,
#             'items': order_items_data,
#             "created_at": order.created_at.isoformat(),
#             'order_count': orders_by_table.get(table.id, 0)
#         }
#         # Get the channel layer to broadcast the message to the group
#         # channel_layer = get_channel_layer()
       

#         # # Send the new order to the WebSocket group (using the room name for orders_dashboard)
#         # async_to_sync(channel_layer.group_send)(
#         #     'order_orders_dashboard',  # Use the same group name for all clients (or room based on table)
#         #     {
#         #         'type': 'order_message',
#         #         'order': order_data
#         #     }
#         # )

#         request.session["cart"] = {}
#         return redirect('order_success')  

 
#     return render(request, 'order_confirmation.html', {'table_number': table_id})


# def order_success(request):
#     table_id = request.session.get('table_id', None)
#     if table_id:
#         table = get_object_or_404(Table, id=table_id)
#     else:
#         table = None 
#     order_data = request.session.get('order_data', {})
#     print("hiiiiiiiiiiii")
#     return render(request, 'order_success.html', {'order_data': order_data, 'table': table})


# def confirm_order(request, username, table_number):
#     """
#     Public order confirmation view
#     - No login required
#     - Uses username and table_number from QR code
#     """
#     table = get_object_or_404(Table, number=table_number, user__username=username)
    
#     if request.method == 'POST':
#         customer_name = request.POST.get('customer_name')
#         customer_phone = request.POST.get('customer_phone')
#         cart_items = request.POST.get('cart_items')
        
#         # Validate required fields
#         if not all([customer_name, customer_phone, cart_items]):
#             return render(request, 'order_confirmation.html', {
#                 'table': table,
#                 'restaurant': table.user,
#                 'error': 'All fields (name, phone, and cart) are required.'
#             })

#         try:
#             cart_data = json.loads(cart_items)
#             if not isinstance(cart_data, dict):
#                 raise ValueError("Invalid cart format")
#         except (json.JSONDecodeError, ValueError) as e:
#             return render(request, 'order_confirmation.html', {
#                 'table': table,
#                 'restaurant': table.user,
#                 'error': f'Invalid cart data: {str(e)}'
#             })

#         # Create order
#         order = Order(
#             table=table,
#             user=table.user,
#             customer_name=customer_name,
#             customer_phone=customer_phone,
#             status='Pending'
#         )
#         order.save()

#         # Add order items
#         for item_id, item_data in cart_data.items():
#             try:
#                 item = get_object_or_404(MenuItem, id=item_id, user=table.user)
#                 OrderItem.objects.create(
#                     order=order,
#                     menu_item=item,
#                     quantity=int(item_data.get('quantity', 1)),
#                     price=float(item_data.get('price', item.price)),
#                     notes=item_data.get('notes', '')
#                 )
#             except (MenuItem.DoesNotExist, ValueError) as e:
#                 print(f"Error adding item {item_id}: {str(e)}")
#                 continue

#         order.calculate_total()
        
#         # Store minimal data in session
#         request.session['last_order'] = {
#             'id': order.id,
#             'table_number': table.number,
#             'restaurant': table.user.username
#         }
#         return redirect('order_success', username=username, table_number=table.number)
#     return render(request, 'order_confirmation.html', {
#         'table': table,
#         'restaurant': table.user
#     })




def confirm_order(request, username, table_number):
    """
    Public order confirmation view
    - No login required
    - Uses username and table_number from QR code
    """
    table = get_object_or_404(Table, number=table_number, user__username=username)
    
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        customer_phone = request.POST.get('customer_phone')
        cart_items = request.POST.get('cart_items')
        
        # Validate required fields
        if not all([customer_name, customer_phone, cart_items]):
            return render(request, 'order_confirmation.html', {
                'table': table,
                'restaurant': table.user,
                'error': 'All fields (name, phone, and cart) are required.'
            })

        try:
            cart_data = json.loads(cart_items)
            if not isinstance(cart_data, dict):
                raise ValueError("Invalid cart format")
        except (json.JSONDecodeError, ValueError) as e:
            return render(request, 'order_confirmation.html', {
                'table': table,
                'restaurant': table.user,
                'error': f'Invalid cart data: {str(e)}'
            })

        # Create order
        order = Order(
            table=table,
            user=table.user,
            customer_name=customer_name,
            customer_phone=customer_phone,
            status='Pending',
            _payment_methods='[]',
        )
        order.save()

        # Add order items
        for item_id, item_data in cart_data.items():
            try:
                item = get_object_or_404(MenuItem, id=item_id, user=table.user)
                OrderItem.objects.create(
                    order=order,
                    menu_item=item,
                    quantity=int(item_data.get('quantity', 1)),
                    price=float(item_data.get('price', item.price)),
                    notes=item_data.get('notes', '')
                )
            except (MenuItem.DoesNotExist, ValueError) as e:
                print(f"Error adding item {item_id}: {str(e)}")
                continue

        order.calculate_total()
        
        request.session['play_sound'] = 1
        request.session.modified = True
        # Store minimal data in session
        request.session['last_order'] = {
            'id': order.id,
            'table_number': table.number,
            'restaurant': table.user.username
        }
        return redirect('order_success', username=username, table_number=table.number)
    return render(request, 'order_confirmation.html', {
        'table': table,
        'restaurant': table.user
    })

def order_success(request, username, table_number):
    """
    Order success page
    - Shows confirmation without sensitive data
    """
    table = get_object_or_404(Table, number=table_number, user__username=username)
    order_data = request.session.get('last_order', {})
    
    # Clear the session data after displaying
    if 'last_order' in request.session:
        del request.session['last_order']
    
    return render(request, 'order_success.html', {
        'order': order_data,
        'table': table,
        'restaurant': table.user
    })


from django.http import JsonResponse
from django.shortcuts import render
from .models import Table, Order



from django.views.decorators.cache import never_cache
from django.http import JsonResponse

@never_cache
@login_required
def dashboard_orders(request, username=None):
    # Verify user access
    if request.user.username != username:
        return JsonResponse({'error': 'Unauthorized'}, status=403) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('login')
    
    # Initialize sound flag
    sound = request.session.pop('play_sound', 0)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        tables = Table.objects.filter(user=request.user).order_by('id')
        orders_data = []
        
        for table in tables:
            pending_orders = Order.objects.filter(
                table=table, 
                status='Pending',
                user=request.user
            ).order_by('created_at')  # Order by creation time
            
            has_pending = pending_orders.exists()
            oldest_minutes = 0
            
            if has_pending:
                # Calculate age of oldest pending order in minutes
                oldest_order = pending_orders.first()
                time_difference = timezone.now() - oldest_order.created_at
                oldest_minutes = time_difference.total_seconds() // 60
            
            orders_data.append({
                'id': table.id,
                'number': table.number,
                'has_pending_orders': has_pending,
                'order_count': pending_orders.count(),
                'oldest_pending_order_minutes': oldest_minutes,
                'pending_orders': [
                    {
                        'id': order.id,
                        'created_at': order.created_at.isoformat()
                    } for order in pending_orders
                ] if has_pending else []
            })
        
        return JsonResponse({
            'tables': orders_data,
            'sound': sound
        })
    
    return render(request, 'dashboard/orders.html', {
        'tables': Table.objects.filter(user=request.user).order_by('id'),
        'sound': sound,
        'current_user': request.user
    })

@login_required
def create_order(request, username):
    if request.method == 'POST':
        try:
            # Your existing order creation logic
            # ...
            
            # After successfully creating the order:
            request.session['play_sound'] = 1
            request.session.modified = True  # Ensure the session is saved
            
            return JsonResponse({'status': 'success', 'order_id': new_order.id})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# @login_required
# def dashboard_orders(request, username=None):
#     # Verify user access
#     if request.user.username != username:
#         return JsonResponse({'error': 'Unauthorized'}, status=403) if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect('login')
    
#     # Initialize sound flag (better to use session than global variable)
#     sound = request.session.pop('play_sound', 0)
    
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         tables = Table.objects.filter(user=request.user).order_by('id')
#         orders_data = []
        
#         for table in tables:
#             pending_orders = Order.objects.filter(
#                 table=table, 
#                 status='Pending',
#                 user=request.user  # Ensure user ownership
#             )
#             has_pending = pending_orders.exists()
            
#             orders_data.append({
#                 'id': table.id,
#                 'number': table.number,
#                 'has_pending_orders': has_pending,
#                 'order_count': pending_orders.count()
#             })
        
#         return JsonResponse({
#             'tables': orders_data,
#             'sound': sound
#         })
    
#     return render(request, 'dashboard/orders.html', {
#         'tables': Table.objects.filter(user=request.user).order_by('id'),
#         'sound': sound,
#         'current_user': request.user
#     })

@login_required
def table_pending_orders(request, username, table_id):
    # Verify user access
    if request.user.username != username:
        return redirect('login')
    
    table = get_object_or_404(Table, id=table_id, user=request.user)
    # pending_orders = Order.objects.filter(
    #     table=table, 
    #     status='Pending',
    #     user=request.user  
    # ).order_by('created_at')
    pending_orders = Order.objects.filter(
        table=table,
        billed=False,
        user=request.user  # Ensure user ownership
    ).order_by('created_at')
    
    return render(request, 'dashboard/table_pending_orders.html', {
        'table': table,
        'pending_orders': pending_orders,
        'current_user': request.user
    })


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Order
from django.views.decorators.csrf import csrf_protect
# @csrf_protect
# def update_order_status(request, order_id):
#     if request.method == 'POST':
#         order = get_object_or_404(Order, id=order_id)
#         order.status = 'Completed'
#         order.save()

#         # Get the updated count of pending orders for the same table
#         pending_orders_count = Order.objects.filter(table=order.table, status='Pending').count()

#         # Return a JSON response with the updated count
#         return JsonResponse({
#             'status': 'success',
#             'pending_orders_count': pending_orders_count,
#             'order_id': order.id
#         })
#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# def completed_orders(request,table_id):
    
#     table = get_object_or_404(Table, id=table_id)
#     completed_orders = Order.objects.filter(table=table, status='Completed',billed=False).order_by('-updated_at').annotate(unique_item_count=Count('items', distinct=True))

#     # for order in completed_orders:
#     #     order.localized_updated_at = localtime(order.updated_at)
    
#     return render(request, 'dashboard/completed_orders.html', {
#         'completed_orders': completed_orders,
#         'table':table
#     })


@login_required
@csrf_protect
def update_order_status(request, username, order_id):
    # Verify user owns this order
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.user.username != username:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    order.status = 'Completed'
    order.save()

    # Get the updated count of pending orders for the same table
    pending_orders_count = Order.objects.filter(
        table=order.table, 
        status='Pending',
        user=request.user  # Ensure we only count user's orders
    ).count()

    return JsonResponse({
        'status': 'success',
        'pending_orders_count': pending_orders_count,
        'order_id': order.id
    })

@login_required
def completed_orders(request, username, table_id):
    # Verify user access
    if request.user.username != username:
        return redirect('login')
    
    table = get_object_or_404(Table, id=table_id, user=request.user)
    completed_orders = Order.objects.filter(
        table=table,
        status='Completed',
        billed=False,
        user=request.user  # Ensure user ownership
    ).order_by('-updated_at').annotate(
        unique_item_count=Count('items', distinct=True)
    )
    return render(request, 'dashboard/completed_orders.html', {
        'completed_orders': completed_orders,
        'table': table,
        'current_user': request.user  # Pass user to template
    })


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from collections import defaultdict
from .models import Order

def generate_bill(request, order_id):
    """Generates a bill for a single order and marks it as billed."""
    order = get_object_or_404(Order, id=order_id)
    
    # Calculate totals and save the order as billed
    order.final_total = order.calculate_final_total()
    order.billed = True  # Mark order as billed
    order.save()
    bill_generated_at = datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")

    # Render bill content
    bill_content = render_to_string('dashboard/bill_template.html', {
        'order': order,
        'bill_generated_at':bill_generated_at,
        'user_order_id': order.user_order_id,
        'username': order.user.username  # Pass username to template
    })

    return JsonResponse({'bill_content': bill_content, 'success': True})



def generate_combined_bill(request):
    """Generates a combined bill for multiple orders and marks them as billed."""
    
    order_ids = request.GET.get('order_ids', '').split(',')
    orders = Order.objects.filter(id__in=order_ids, billed=False)  # Ensure orders are not already billed

    if not orders.exists():
        return JsonResponse({'success': False, 'error': 'No valid orders found'})

    # Generate a unique identifier for the combined bill
    combined_uuid = uuid.uuid4()

    # Dictionary to store combined items
    combined_items = defaultdict(lambda: {"quantity": 0, "price": 0})


    username = orders.first().user.username if orders else "Unknown"
    customer_names = list(set(order.customer_name for order in orders if order.customer_name))
    user_order_ids = [order.user_order_id for order in orders if order.user_order_id]
    bill_generated_at = datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")

    # Combine items from multiple orders
    for order in orders:
        order.combined_id = combined_uuid  # Assign shared ID to group orders
        order.billed = True  # Mark as billed
        order.save()
        
        for item in order.items.all():
            item_name = item.menu_item.name if item.menu_item else item.item_name if item.item_name else "Unknown Item"
            combined_items[item_name]["quantity"] += item.quantity
            combined_items[item_name]["price"] += item.price * item.quantity

    # Calculate totals
    combined_subtotal = sum(item['price'] for item in combined_items.values())
    combined_cgst = sum(order.calculate_cgst() for order in orders)  
    combined_sgst = sum(order.calculate_sgst() for order in orders)  
    combined_discount = sum(order.calculate_discount() for order in orders)  
    combined_final_total = combined_subtotal + combined_cgst + combined_sgst - combined_discount


    
    # Prepare context for bill template
    context = {
        'orders': orders,
        'bill_generated_at': bill_generated_at,
        'customer_names': customer_names,
        'user_order_ids': user_order_ids,
        'username': username,  # Add username to bill
        'combined_items': dict(combined_items),
        'combined_subtotal': combined_subtotal,
        'combined_cgst': combined_cgst,
        'combined_sgst': combined_sgst,
        'combined_discount': combined_discount,
        'combined_final_total': combined_final_total,
    }

    # Render combined bill content
    bill_content = render_to_string('dashboard/combined_bill.html', context)

    return JsonResponse({'bill_content': bill_content, 'success': True})


# @login_required
# def generate_bill(request, order_id):
#     """Generates a bill for a single order and marks it as billed."""
#     order = get_object_or_404(Order, id=order_id, user=request.user)  # Add user check
    
#     if order.billed:
#         return JsonResponse({'success': False, 'error': 'Order already billed'})
    
#     # Calculate totals and save the order as billed
#     order.final_total = order.calculate_final_total()
#     order.billed = True
#     order.save()

#     # Render bill content
#     bill_content = render_to_string('dashboard/bill_template.html', {'order': order})

#     return JsonResponse({
#         'bill_content': bill_content,
#         'success': True,
#         'message': 'Bill generated successfully'
#     })

# @login_required
# def generate_combined_bill(request):
#     """Generates a combined bill for multiple orders and marks them as billed."""
#     if not request.user.is_authenticated:
#         return JsonResponse({'success': False, 'error': 'Authentication required'})
    
#     order_ids = request.GET.get('order_ids', '').split(',')
#     orders = Order.objects.filter(
#         id__in=order_ids,
#         billed=False,
#         user=request.user  # Add user check
#     )

#     if orders.count() < 2:
#         return JsonResponse({'success': False, 'error': 'Select at least 2 orders'})

#     # Generate a unique identifier for the combined bill
#     combined_uuid = uuid.uuid4()
#     combined_items = defaultdict(lambda: {"quantity": 0, "price": 0})

#     for order in orders:
#         order.combined_id = combined_uuid
#         order.billed = True
#         order.save()
        
#         for item in order.items.all():
#             item_name = item.menu_item.name if item.menu_item else item.item_name
#             combined_items[item_name]["quantity"] += item.quantity
#             combined_items[item_name]["price"] += item.price * item.quantity

#     # Calculate totals
#     combined_subtotal = sum(item['price'] for item in combined_items.values())
#     combined_cgst = sum(order.calculate_cgst() for order in orders)  
#     combined_sgst = sum(order.calculate_sgst() for order in orders)  
#     combined_discount = sum(order.calculate_discount() for order in orders)  
#     combined_final_total = combined_subtotal + combined_cgst + combined_sgst - combined_discount

#     context = {
#         'orders': orders,
#         'combined_items': dict(combined_items),
#         'combined_subtotal': combined_subtotal,
#         'combined_cgst': combined_cgst,
#         'combined_sgst': combined_sgst,
#         'combined_discount': combined_discount,
#         'combined_final_total': combined_final_total,
#         'user': request.user  # Pass user to template
#     }

#     bill_content = render_to_string('dashboard/combined_bill.html', context)

#     return JsonResponse({
#         'bill_content': bill_content,
#         'success': True,
#         'message': 'Combined bill generated successfully'
#     })


# def order_details(request, order_id):
#     try:
#         order = Order.objects.get(id=order_id)

#         # Fetch all order items (ensure menu_item name is accessible)
#         items = OrderItem.objects.filter(order=order).select_related('menu_item')

#         # Convert QuerySet into a properly formatted list
#         items_list = [
#             {
#                 'id': item.id,
#                 'name': item.item_name,  # Ensure this field exists
#                 'quantity': item.quantity,
#                 'price': item.price,
#                 'is_completed': item.is_completed,
#                 # 'status': item.status
#             }
#             for item in items
#         ]

#         return JsonResponse({
#             'order': {
#                 'id': order.id,
#                 'customer_name': order.customer_name,
#                 'items': items_list  # Move items inside "order"
#             }
#         })
#     except Order.DoesNotExist:
#         return JsonResponse({'error': 'Order not found'}, status=404)


@csrf_exempt
def update_item_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            is_completed = data.get('is_completed')

            item = OrderItem.objects.get(id=item_id)
            item.is_completed = is_completed  # ✅ Save the completed state
            item.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



@login_required
@csrf_protect
def update_order_status(request, username, order_id):
    # Verify user owns this order
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if request.user.username != username:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    order.status = 'Completed'
    order.save()

    # Get the updated count of pending orders for the same table
    pending_orders_count = Order.objects.filter(
        table=order.table, 
        status='Pending',
        user=request.user  # Ensure we only count user's orders
    ).count()

    return JsonResponse({
        'status': 'success',
        'pending_orders_count': pending_orders_count,
        'order_id': order.id
    })


@csrf_exempt
@require_POST
def update_item_status(request, username):
    try:
        # Parse JSON data from request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)

        item_id = data.get('item_id')
        is_completed = data.get('is_completed')

        # Validate required parameters
        if item_id is None or is_completed is None:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing required parameters: item_id and is_completed'
            }, status=400)

        # Get and update the item
        item = OrderItem.objects.get(id=item_id)
        item.is_completed = is_completed
        item.save()

        return JsonResponse({
            'status': 'success',
            'data': {
                'item_id': item.id,
                'is_completed': item.is_completed,
                'order_id': item.order.id
            }
        })

    except OrderItem.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'OrderItem with id {item_id} does not exist'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# @login_required
# @csrf_protect
# def update_order_status(request, username, order_id):
#     # Verify user owns this order
#     order = get_object_or_404(Order, id=order_id, user=request.user)
    
#     if request.user.username != username:
#         return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
#     try:
#         data = json.loads(request.body) if request.body else {}
#         new_status = data.get('status', 'Completed')
        
#         # Validate status
#         if new_status not in dict(Order.status).keys():
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Invalid status value'
#             }, status=400)
        
#         order.status = new_status
#         order.save()

#         # Check if all items are completed when marking order as Completed
#         if new_status == 'Completed':
#             incomplete_items = order.items.filter(is_completed=False).exists()
#             if incomplete_items:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Cannot complete order with pending items',
#                     'order_id': order.id
#                 }, status=400)

#         # Get updated order data
#         order_data = {
#             'id': order.id,
#             'status': order.status,
#             'all_completed': not order.items.filter(is_completed=False).exists(),
#             'items': [{
#                 'id': item.id,
#                 'item_name': item.item_name,
#                 'quantity': item.quantity,
#                 'is_completed': item.is_completed
#             } for item in order.items.all()]
#         }

#         return JsonResponse({
#             'status': 'success',
#             'order': order_data,
#             'pending_orders_count': Order.objects.filter(
#                 table=order.table,
#                 status='Pending',
#                 user=request.user
#             ).count()
#         })

#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         }, status=500)


# @login_required
# @csrf_protect
# def update_item_status(request, username):
#     try:
#         # Parse JSON data
#         data = json.loads(request.body)
#         item_id = data.get('item_id')
#         is_completed = data.get('is_completed')
#         order_id = data.get('order_id')

#         # Validate
#         if None in [item_id, is_completed, order_id]:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Missing required parameters'
#             }, status=400)

#         # Verify ownership
#         item = get_object_or_404(
#             OrderItem.objects.select_related('order'),
#             id=item_id,
#             order__user=request.user,
#             order__id=order_id
#         )

#         # Update item
#         item.is_completed = is_completed
#         item.save()

#         # Get updated order data
#         order = item.order
#         all_completed = not order.items.filter(is_completed=False).exists()
        
#         order_data = {
#             'id': order.id,
#             'all_completed': all_completed,
#             'items': [{
#                 'id': i.id,
#                 'item_name': i.item_name,
#                 'quantity': i.quantity,
#                 'is_completed': i.is_completed
#             } for i in order.items.all()]
#         }

#         return JsonResponse({
#             'status': 'success',
#             'order': order_data,
#             'item': {
#                 'id': item.id,
#                 'is_completed': item.is_completed
#             }
#         })

#     except json.JSONDecodeError:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Invalid JSON data'
#         }, status=400)
#     except OrderItem.DoesNotExist:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Order item not found'
#         }, status=404)
#     except Exception as e:
#         return JsonResponse({
#             'status': 'error',
#             'message': str(e)
#         }, status=500)
    

def order_details(request, username, order_id):
    try:
        order = Order.objects.select_related('table').prefetch_related('items').get(id=order_id)
        
        items_list = [{
            'id': item.id,
            'name': item.item_name,
            'quantity': item.quantity,
            'price': str(item.price),
            'is_completed': item.is_completed,
            'notes': item.notes if hasattr(item, 'notes') and item.notes else None
        } for item in order.items.all()]

        response_data = {
            'status': 'success',
            'data': {
                'order': {
                    'id': order.id,
                    'table_number': order.table.number if order.table else 'N/A',
                    'customer_name': order.customer_name,
                    'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    'total': str(order.total) if hasattr(order, 'total') else '0.00',
                    'items': items_list
                }
            }
        }
        print(items_list) 
        return JsonResponse(response_data)

    except Order.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Order with id {order_id} does not exist'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

@csrf_exempt
def mark_items_completed(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])

       
        OrderItem.objects.filter(id__in=item_ids).update(status='Completed')

        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



# def send_order_update(order):
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         'orders',  # Replace with your WebSocket group name
#         {
#             'type': 'order.update',
#             'message': json.dumps({
#                 'order': {
#                     'id': order.id,
#                     'table_id': order.table.id,
#                     'customer_name': order.customer_name,
#                     'total': order.total,
#                     'items': [{'name': item.menu_item.name, 'quantity': item.quantity, 'price': item.price} for item in order.items.all()],
#                     'status': order.status,
#                 }
#             })
#         }
#     )

def get_initial_table_state(request):
    tables = Table.objects.all()
    data = []
    for table in tables:
        pending_orders = Order.objects.filter(table=table, status='pending').count()
        data.append({
            'id': table.id,
            'number': table.number,
            'pending_orders': pending_orders,
        })
    return JsonResponse({'tables': data})

def get_orders_state(request):
    tables = Table.objects.all()
    data = []

    for table in tables:
        pending_orders = Order.objects.filter(table=table, status='pending').count()
        data.append({
            'id': table.id,
            'order_count': pending_orders,
        })

    return JsonResponse(data, safe=False)

# @csrf_exempt
# def update_item_status(request):
#     """API to mark order items as completed."""
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             item_ids = data.get("item_ids", [])

#             # Mark items as "Completed" in the database
#             OrderItem.objects.filter(id__in=item_ids).update(status="Completed")

#             return JsonResponse({"status": "success"})
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
#     return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

# @csrf_exempt
# def update_order_status(request, order_id):
#     if request.method == "POST":
#         try:
#             order = Order.objects.get(id=order_id)
#             order.status = "completed"  # Ensure you have a "completed" status in your model
#             order.save()

#             # Broadcast update via WebSockets
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                 f'order_{order.table.number}',
#                 {'type': 'order_completed', 'completed_order': order_id}
#             )

#             return JsonResponse({"status": "success"})
#         except Order.DoesNotExist:
#             return JsonResponse({"status": "error", "message": "Order not found"}, status=404)
    
#     return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)



from itertools import chain
from django.shortcuts import render, get_object_or_404
from decimal import Decimal

# def billed_orders(request, table_number):
#     table = get_object_or_404(Table, number=table_number)

#     # Fetch individual billed orders
#     individual_billed_orders = Order.objects.filter(
#         table=table, billed=True, combined_id__isnull=True
#     ).order_by('-updated_at')

#     # Fetch combined orders
#     combined_orders = Order.objects.filter(
#         table=table, billed=True, combined_id__isnull=False
#     ).order_by('-updated_at')

#     # Group combined orders and calculate total
#     grouped_combined_orders = {}
#     for order in combined_orders:
#         grouped_combined_orders.setdefault(order.combined_id, []).append(order)

#     # combined_list = [
#     #     {
#     #         "type": "combined",
#     #         "combined_id": combined_id,
#     #         "orders": orders,  # Store orders to show in sub-rows
#     #         "total_amount": sum(order.final_total or Decimal('0.00') for order in orders),  # Total for combined
#     #         "updated_at": max(order.updated_at for order in orders)  # Latest update time
#     #     }
#     #     for combined_id, orders in grouped_combined_orders.items()
#     # ]

#     combined_list = [
#     {
#         "type": "combined",
#         "combined_id": combined_id,
#         "orders": [
#             {
#                 "id": order.id,
#                 "customer_name": order.customer_name,
#                 "final_total": order.final_total or Decimal('0.00'),
#                 "updated_at": order.updated_at
#             }
#             for order in orders
#         ],
#         "total_amount": sum(Decimal(order.final_total or '0.00') for order in orders),
#         "updated_at": max(order.updated_at for order in orders)
#     }
#     for combined_id, orders in grouped_combined_orders.items()
# ]


#     # Prepare individual orders list
#     individual_list = [
#         {
#             "type": "single",
#             "order": order,
#             "total_amount": order.final_total or Decimal('0.00'),  # Individual total
#             "updated_at": order.updated_at
#         }
#         for order in individual_billed_orders
#     ]

#     # Merge lists and sort by latest update time
#     final_order_list = sorted(
#         chain(combined_list, individual_list),
#         key=lambda x: x["updated_at"],
#         reverse=True
#     )

#     # Assign numbering
#     for index, entry in enumerate(final_order_list):
#         entry["number"] = len(final_order_list) - index

#     return render(request, 'dashboard/billed_orders.html', {
#         'table': table,
#         'final_order_list': final_order_list
#     })
# from django.shortcuts import render, get_object_or_404
# from django.db.models import Prefetch, Sum, F
# from decimal import Decimal
# from itertools import chain
# from .models import Table, Order, OrderItem

# def billed_orders(request, table_number):
#     table = get_object_or_404(Table, number=table_number)
    
#     # Optimized query with prefetching of related items
#     billed_orders = Order.objects.filter(
#         table=table,
#         billed=True
#     ).prefetch_related(
#         Prefetch('items', queryset=OrderItem.objects.select_related('menu_item'))
#     ).order_by('-updated_at')

#     individual_orders = []
#     combined_orders_dict = {}

#     # First pass: ensure all orders have proper final totals
#     for order in billed_orders:
#         # Recalculate if total is None or zero
#         if order.final_total is None or order.final_total == 0:
#             order.final_total = calculate_order_total(order)
#             order.save(update_fields=['final_total'])

#         if order.combined_id:
#             combined_orders_dict.setdefault(order.combined_id, []).append(order)
#         else:
#             individual_orders.append(order)

#     # Process combined orders
#     combined_orders_list = []
#     for combined_id, orders in combined_orders_dict.items():
#         # Verify and update any individual orders with zero totals
#         for order in orders:
#             if order.final_total == 0:
#                 order.final_total = calculate_order_total(order)
#                 order.save(update_fields=['final_total'])

#         # Calculate combined total from validated individual orders
#         combined_total = sum(order.final_total for order in orders)
        
#         combined_orders_list.append({
#             'type': 'combined',
#             'combined_id': combined_id,
#             'orders': orders,
#             'total_amount': combined_total,
#             'updated_at': max(order.updated_at for order in orders)
#         })

#     # Process individual orders
#     individual_orders_list = [{
#         'type': 'single',
#         'order': order,
#         'total_amount': order.final_total,
#         'updated_at': order.updated_at
#     } for order in individual_orders]

#     # Combine and sort all orders by update time (newest first)
#     final_order_list = sorted(
#         chain(combined_orders_list, individual_orders_list),
#         key=lambda x: x['updated_at'],
#         reverse=True
#     )

#     # Add sequential numbering
#     for index, entry in enumerate(final_order_list, start=1):
#         entry['number'] = index

#     return render(request, 'dashboard/billed_orders.html', {
#         'table': table,
#         'final_order_list': final_order_list
#     })

# def calculate_order_total(order):
#     """Calculate the complete order total including taxes and discounts"""
#     # Calculate subtotal from all items
#     subtotal = order.items.aggregate(
#         total=Sum(F('quantity') * F('price'))
#     )['total'] or Decimal('0')
    
#     # Calculate taxes and discount
#     cgst = (subtotal * order.cgst_rate) / Decimal('100')
#     sgst = (subtotal * order.sgst_rate) / Decimal('100')
#     discount = (subtotal * order.discount) / Decimal('100')
    
#     # Return final total
#     return subtotal + cgst + sgst - discount


from datetime import date, datetime
from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Sum, F
from decimal import Decimal
from itertools import chain
from .models import Table, Order, OrderItem

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
from decimal import Decimal
from itertools import chain
from django.db.models import Prefetch
from .models import Table, Order, OrderItem
 # Assuming you have a helper for this

@login_required
def billed_orders(request, table_number):
    table = get_object_or_404(Table, number=table_number, user=request.user)

    selected_date = request.GET.get('date')
    try:
        filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date() if selected_date else date.today()
    except (ValueError, TypeError):
        filter_date = date.today()

    payment_method = request.GET.get('payment_method')

    # Query all billed orders for this table and date
    billed_orders_qs = Order.objects.filter(
        table=table,
        billed=True,
        updated_at__date=filter_date,
        user=request.user
    ).prefetch_related(
        Prefetch('items', queryset=OrderItem.objects.select_related('menu_item'))
    ).order_by('-updated_at')

    billed_orders_all = list(billed_orders_qs)  # For totals
    billed_orders_display = billed_orders_all  # For filtered table display

    # if payment_method:
    #     billed_orders_display = [
    #         order for order in billed_orders_all
    #         if payment_method in (order.payment_methods or [])
    #     ]
    if payment_method:
        if payment_method == 'pending':
            billed_orders_display = [order for order in billed_orders_all if not order.payment_methods]
        else:
            billed_orders_display = [
                order for order in billed_orders_all
                if order.payment_methods and payment_method.lower() in [pm.strip().lower() for pm in order.payment_methods]
            ]

    # Calculate daily total from all billed orders
    daily_total = Decimal('0.00')
    for order in billed_orders_all:
        if not order.final_total:
            order.final_total = calculate_order_total(order)
            order.save(update_fields=['final_total'])
        daily_total += order.final_total

    # Process filtered orders (for display only)
    display_individual_orders = []
    display_combined_orders_dict = {}

    for order in billed_orders_display:
        if order.combined_id:
            display_combined_orders_dict.setdefault(order.combined_id, []).append(order)
        else:
            display_individual_orders.append(order)

    combined_orders_list = []
    for combined_id, orders in display_combined_orders_dict.items():
        valid_orders = [o for o in orders if o.user == request.user]
        if not valid_orders:
            continue
        for order in valid_orders:
            if not order.final_total:
                order.final_total = calculate_order_total(order)
                order.save(update_fields=['final_total'])
        combined_total = sum(order.final_total for order in valid_orders)
        combined_orders_list.append({
            'type': 'combined',
            'combined_id': combined_id,
            'orders': valid_orders,
            'total_amount': combined_total,
            'updated_at': max(order.updated_at for order in valid_orders),
            'has_pending_payments': any(not order.payment_methods for order in valid_orders),
        })

    individual_orders_list = [{
        'type': 'single',
        'order': order,
        'total_amount': order.final_total,
        'updated_at': order.updated_at,
    } for order in display_individual_orders if order.user == request.user]

    final_order_list = sorted(
        chain(combined_orders_list, individual_orders_list),
        key=lambda x: x['updated_at'],
        reverse=True
    )

    for index, entry in enumerate(final_order_list, start=1):
        entry['number'] = index

    return render(request, 'dashboard/billed_orders.html', {
        'table': table,
        'final_order_list': final_order_list,
        'selected_date': filter_date,
        'today': date.today(),
        'daily_total': daily_total,
        'order_count': len(billed_orders_all),  # Count of all billed orders (not filtered)
        'user': request.user
    })


def calculate_order_total(order):
    """Helper function to calculate order total with taxes and discount"""
    subtotal = order.items.aggregate(
        total=Sum(F('quantity') * F('price'))
    )['total'] or Decimal('0')
    
    cgst = (subtotal * order.cgst_rate) / Decimal('100')
    sgst = (subtotal * order.sgst_rate) / Decimal('100')
    discount = (subtotal * order.discount) / Decimal('100')
    
    return subtotal + cgst + sgst - discount

# def billed_orders(request, table_number):
#     table = get_object_or_404(Table, number=table_number)
    
#     # Date filtering logic
#     selected_date = request.GET.get('date')
#     if selected_date:
#         try:
#             filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             filter_date = date.today()
#     else:
#         filter_date = date.today()
    
#     # Base queryset with date filtering
#     billed_orders = Order.objects.filter(
#         table=table,
#         billed=True,
#         updated_at__date=filter_date
#     ).prefetch_related(
#         Prefetch('items', queryset=OrderItem.objects.select_related('menu_item'))
#     ).order_by('-updated_at')

#     individual_orders = []
#     combined_orders_dict = {}
    
#     # Initialize daily total
#     daily_total = Decimal('0.00')

#     # Process orders and ensure totals are calculated
#     for order in billed_orders:
#         if order.final_total is None or order.final_total == 0:
#             order.final_total = calculate_order_total(order)
#             order.save(update_fields=['final_total'])
        
#         # Add to daily total
#         daily_total += order.final_total

#         if order.combined_id:
#             combined_orders_dict.setdefault(order.combined_id, []).append(order)
#         else:
#             individual_orders.append(order)

#     # Prepare combined orders list
#     combined_orders_list = []
#     for combined_id, orders in combined_orders_dict.items():
#         # Verify all orders have proper totals
#         for order in orders:
#             if order.final_total == 0:
#                 order.final_total = calculate_order_total(order)
#                 order.save(update_fields=['final_total'])

#         combined_total = sum(order.final_total for order in orders)
        
#         combined_orders_list.append({
#             'type': 'combined',
#             'combined_id': combined_id,
#             'orders': orders,
#             'total_amount': combined_total,
#             'updated_at': max(order.updated_at for order in orders)
#         })

#     # Prepare individual orders list
#     individual_orders_list = [{
#         'type': 'single',
#         'order': order,
#         'total_amount': order.final_total,
#         'updated_at': order.updated_at
#     } for order in individual_orders]

#     # Combine and sort all orders
#     final_order_list = sorted(
#         chain(combined_orders_list, individual_orders_list),
#         key=lambda x: x['updated_at'],
#         reverse=True
#     )

#     # Add sequential numbering
#     for index, entry in enumerate(final_order_list, start=1):
#         entry['number'] = index

#     return render(request, 'dashboard/billed_orders.html', {
#         'table': table,
#         'final_order_list': final_order_list,
#         'selected_date': filter_date,
#         'today': date.today(),
#         'daily_total': daily_total,  # Add daily total to context
#         'order_count': len(final_order_list)  # Add order count
#     })

# def calculate_order_total(order):
#     """Helper function to calculate order total with taxes and discount"""
#     subtotal = order.items.aggregate(
#         total=Sum(F('quantity') * F('price'))
#     )['total'] or Decimal('0')
    
#     cgst = (subtotal * order.cgst_rate) / Decimal('100')
#     sgst = (subtotal * order.sgst_rate) / Decimal('100')
#     discount = (subtotal * order.discount) / Decimal('100')
    
#     return subtotal + cgst + sgst - discount

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
def SignupPage(request):
    if request.method == 'POST':
        uname = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        

        if pass1 != pass2:
            messages.error(request, "Your password and confirm password do not match!")
            return redirect('signup')

        if User.objects.filter(username=uname).exists():
            messages.error(request, "Username is already taken. Please choose another.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered. Try logging in instead.")
            return redirect('signup')

        try:
            my_user = User.objects.create_user(username=uname, email=email, password=pass1)
            my_user.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('signup')
         # Clear any non-signup messages when loading the page
    
    return render(request, 'dashboard/signup.html')
from django.urls import reverse

def LoginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass')
        
         # Clear any existing messages to prevent mixing
        
        # Basic validation
        if not username or not pass1:
            messages.error(request, "Both username and password are required!")
        else:
            user = authenticate(request, username=username, password=pass1)
            if user is not None:
                login(request, user)
                return redirect(reverse('dashboard_home', kwargs={'username': user.username}))
            else:
                messages.error(request, "Invalid username or password!")
        
        # Return to login page with messages
        return redirect('login')  # Assuming 'login' is your URL name
    
    return render(request, 'dashboard/login.html')


def LogoutPage(request):
    logout(request)
    return redirect('login')

@login_required
def add_table(request, username):
    if request.method == 'POST':
        number = request.POST.get('number')
        
        if not number:
            messages.error(request, "Table number is required")
            return redirect('add_table', username=username)
            
        if Table.objects.filter(user=request.user, number=number).exists():
            messages.error(request, f"Table {number} already exists")
            return redirect('add_table', username=username)
            
        Table.objects.create(
            user=request.user,
            number=number
        )
        messages.success(request, f"Table {number} added successfully")
        return redirect('dashboard_orders', username=username)
    
    # Suggest next available table number
    last_table = Table.objects.filter(user=request.user).order_by('-number').first()
    suggested_number = last_table.number + 1 if last_table else 1
    
    return render(request, 'dashboard/add_table.html', {
        'username': username,
        'suggested_number': suggested_number
    })




from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta, date
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem, Table, MenuItem, Category
from django.core.cache import cache
from collections import defaultdict
from django.db.models.functions import Coalesce
import colorsys



from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import ExtractHour
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Order, OrderItem

@never_cache
@login_required
def dashboard_home(request, username):
    if request.user.username != username:
        return redirect('login')
    
    # Get and validate the filter date
    filter_date = get_date_filter(request)
    
    # Get date ranges - simplified to single day comparison
    date_range, previous_date_range = get_date_ranges(filter_date)
    
    # Get orders for the SPECIFIC selected date
    orders = Order.objects.filter(
        user=request.user,
        created_at__date=date_range[0],  # Exact date match
        billed=True
    ).select_related('table')
    
    # Get previous day's orders for comparison
    previous_orders = Order.objects.filter(
        user=request.user,
        created_at__date=previous_date_range[0],
        billed=True
    )
    
    # 1. Calculate key metrics
    current_sales = orders.aggregate(total=Sum('final_total'))['total'] or 0
    previous_sales = previous_orders.aggregate(total=Sum('final_total'))['total'] or 0
    
    growth_rate = 0
    if previous_sales > 0:
        growth_rate = ((current_sales - previous_sales) / previous_sales) * 100
    
    # 2. Order statistics
    total_orders = orders.count()
    completed_orders = orders.filter(status='Completed').count()
    
    avg_order_value = 0
    if total_orders > 0:
        avg_order_value = current_sales / total_orders
    
    # 3. Top selling items
    top_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('price'))
    ).order_by('-total_quantity')[:10]

    if current_sales > 0:
        for item in top_items:
            item['percentage'] = (item['total_revenue'] / current_sales) * 100
    
    top_item = top_items.first() if top_items.exists() else None
    
    # 4. Table performance
    table_performance = orders.values(
        'table__number'
    ).annotate(
        order_count=Count('id'),
        total_revenue=Sum('final_total'),
        avg_value=ExpressionWrapper(
            F('total_revenue') / F('order_count'),
            output_field=DecimalField()
        )
    ).order_by('-total_revenue')
    
    # 5. Sales trend data - hourly for single day
    hourly_sales = orders.annotate(
        hour=ExtractHour('created_at')
    ).values('hour').annotate(
        hourly_total=Sum('final_total')
    ).order_by('hour')
    
    # Fill all 24 hours
    sales_dict = {sale['hour']: float(sale['hourly_total']) for sale in hourly_sales}
    sales_data = [sales_dict.get(hour, 0) for hour in range(24)]
    sales_labels = [f"{hour}:00" for hour in range(24)]
    
    # 6. Category sales data
    category_sales = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__category__name'
    ).annotate(
        category_total=Sum(F('quantity') * F('price'))
    ).order_by('-category_total')
    
    # Generate distinct colors for categories
    category_colors = generate_colors(category_sales.count())
    for i, category in enumerate(category_sales):
        category['color'] = category_colors[i]
    
    # Calculate average items per order
    total_items = OrderItem.objects.filter(
        order__in=orders
    ).aggregate(total=Sum('quantity'))['total'] or 0
    avg_items_per_order = total_items / total_orders if total_orders > 0 else 0
    
    context = {
        'today': timezone.localdate(),
        'selected_date': filter_date,
        'today_sales': current_sales,
        'growth_rate': round(growth_rate, 2),
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'avg_order_value': round(avg_order_value, 2),
        'avg_items_per_order': round(avg_items_per_order, 1),
        'top_items': top_items,
        'top_item': top_item,
        'table_performance': table_performance,
        'sales_labels': sales_labels,
        'sales_data': sales_data,
        'category_sales': category_sales,
        'category_labels': [item['menu_item__category__name'] for item in category_sales],
        'category_data': [float(item['category_total']) for item in category_sales],
    }
    
    return render(request, 'dashboard/home.html', context)


def get_date_filter(request):
    """Get and validate date from request parameters"""
    if 'date' in request.GET and request.GET['date']:
        try:
            selected_date = datetime.strptime(request.GET['date'], '%Y-%m-%d').date()
            if selected_date <= timezone.localdate():  # Only allow past dates
                return selected_date
        except (ValueError, TypeError):
            pass
    return timezone.localdate()  # Default to today


def get_date_ranges(filter_date):
    """Get date ranges for current and previous periods"""
    # For any selected date, compare with previous day
    date_range = [filter_date]
    previous_date_range = [filter_date - timedelta(days=1)]
    return date_range, previous_date_range


def generate_colors(count):
    """Generate distinct colors for categories"""
    import colorsys
    colors = []
    for i in range(count):
        hue = i * (360 / max(count, 1))
        rgb = colorsys.hsv_to_rgb(hue/360, 0.7, 0.8)
        colors.append('#%02x%02x%02x' % (int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)))
    return colors 
# def get_date_filter(request):
#     """Get date filter from request parameters"""
#     if 'date' in request.GET:
#         try:
#             return datetime.strptime(request.GET['date'], '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             pass
#     return timezone.localdate()

from datetime import datetime
from django.utils import timezone

def get_date_filter(request):
    """Get date filter from request parameters with proper validation"""
    if 'date' in request.GET and request.GET['date']:
        try:
            selected_date = datetime.strptime(request.GET['date'], '%Y-%m-%d').date()
            # Ensure date is not in the future
            if selected_date <= timezone.localdate():
                return selected_date
        except (ValueError, TypeError):
            pass
    # Default to today if no valid date provided
    return timezone.localdate()
# def get_date_ranges(filter_date):
#     """Get date ranges for current and previous periods"""
#     if filter_date == timezone.now().date():  # Today
#         date_range = [filter_date]
#         previous_date_range = [filter_date - timedelta(days=1)]
#     elif filter_date.weekday() == 0:  # Week starting Monday
#         date_range = [filter_date + timedelta(days=i) for i in range(7)]
#         previous_date_range = [filter_date - timedelta(days=7+i) for i in range(7)]
#     elif filter_date.day == 1:  # Month
#         next_month = filter_date.replace(day=28) + timedelta(days=4)
#         last_day = next_month - timedelta(days=next_month.day)
#         date_range = [filter_date + timedelta(days=i) for i in range((last_day - filter_date).days + 1)]
        
#         prev_month = filter_date.replace(day=1) - timedelta(days=1)
#         previous_date_range = [prev_month.replace(day=1) + timedelta(days=i) 
#                              for i in range((prev_month - prev_month.replace(day=1)).days + 1)]
#     else:  # Custom single date
#         date_range = [filter_date]
#         previous_date_range = [filter_date - timedelta(days=1)]
    
#     return date_range, previous_date_range

def get_date_ranges(filter_date):
    """Get date ranges for current and previous periods"""
    # For any selected date, we'll compare with the previous day
    date_range = [filter_date]
    previous_date_range = [filter_date - timedelta(days=1)]
    
    return date_range, previous_date_range

def generate_colors(count):
    """Generate distinct colors for categories"""
    colors = []
    for i in range(count):
        hue = i * (360 / max(count, 1))
        rgb = colorsys.hsv_to_rgb(hue/360, 0.7, 0.8)
        colors.append(f"rgb({int(rgb[0]*255)}, {int(rgb[1]*255)}, {int(rgb[2]*255)})")
    return colors
# views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@require_POST
def update_payment_method(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        payment_method = json.loads(request.body).get('payment_method')
        
        if payment_method in dict(Order.PAYMENT_METHODS).keys():
            order.payment_method = payment_method
            order.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Invalid payment method'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'})

# from django.shortcuts import render
# from django.db.models import Sum, Count, Avg
# from django.utils import timezone
# from .models import Order, OrderItem
# from datetime import datetime

# def daily_sales_report(request):
#     report_date = timezone.now().date()
    
#     if 'report_date' in request.GET:
#         try:
#             report_date = datetime.strptime(request.GET['report_date'], '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             pass
    
#     print(f"\n=== DEBUG ===")
#     print(f"User: {request.user}")
#     print(f"Date: {report_date}")
    
#     orders = Order.objects.filter(
#         user=request.user,
#         created_at__date=report_date,
#         status='Completed'
#     )
    
#     print(f"Orders found: {orders.count()}")
#     if orders.exists():
#         print(f"Sample order: {orders.first().id} - {orders.first().created_at}")
    
#     # Calculate totals
#     grand_total = orders.aggregate(Sum('final_total'))['final_total__sum'] or 0
#     total_orders = orders.count()
#     average_order = orders.aggregate(Avg('final_total'))['final_total__avg'] or 0
    
#     # Calculate item-wise totals
#     item_totals = OrderItem.objects.filter(
#         order__in=orders
#     ).values(
#         'item_name',
#         'price'  # Include price in the values to show unit price
#     ).annotate(
#         total_quantity=Sum('quantity'),
#         total_amount=Sum(F('quantity') * F('price'))
#     ).order_by('-total_amount')
    
#     context = {
#         'report_date': report_date,
#         'grand_total': grand_total,
#         'total_orders': total_orders,
#         'average_order': average_order,
#         'item_totals': item_totals,
#     }
    
#     return render(request, 'dashboard/home.html', context)

from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    send_mail(
        'Test Email',
        'This is a test email from Django.',
        'your-email@gmail.com',
        ['agrimapt1999@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Test email sent!")

def check_unbilled_orders(request):
    phone = request.GET.get('phone')
    restaurant = request.GET.get('restaurant')
    
    if not phone or not restaurant:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    has_unbilled = Order.objects.filter(
        customer_phone=phone,
        billed=False,
        user__username=restaurant
    ).exists()
    
    return JsonResponse({'has_unbilled_orders': has_unbilled})


@login_required
def profile(request, username):
    if request.user.username != username:
        messages.error(request, "You can only view your own profile")
        return redirect('profile', username=request.user.username)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile', username=username)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'current_user': request.user
    }

    return render(request, 'dashboard/profile.html', context)

@login_required
@require_POST
def toggle_cart_status(request, username):
    if request.user.username != username:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    profile = get_object_or_404(Profile, user=request.user)
    
    # Toggle the cart_enabled status
    profile.cart_enabled = not profile.cart_enabled
    profile.save()
    
    # Optionally update all tables for this user
    # Table.objects.filter(user=request.user).update(cart_enabled=profile.cart_enabled)
    
    return JsonResponse({
        'status': 'success',
        'cart_enabled': profile.cart_enabled,
    })

@login_required
def view_profile(request, username):
    user = get_object_or_404(User, username=username)
    # Ensure users can only view their own profile
    if request.user != user:
        return redirect('view_profile', username=request.user.username)
    return render(request, 'dashboard/profile_view.html', {'profile_user': user})

# @login_required
# def edit_profile(request, username):
#     user = get_object_or_404(User, username=username)
#     # Ensure users can only edit their own profile
#     if request.user != user:
#         return redirect('edit_profile', username=request.user.username)
    
#     if request.method == 'POST':
#         user_form = UserUpdateForm(request.POST, instance=user)
#         profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             return redirect('view_profile', username=user.username)
#     else:
#         user_form = UserUpdateForm(instance=user)
#         profile_form = ProfileUpdateForm(instance=user.profile)
    
#     return render(request, 'dashboard/profile_edit.html', {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'profile_user': user
#     })


@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)
    
    # Ensure users can only edit their own profile
    if request.user != user:
        return redirect('edit_profile', username=request.user.username)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('view_profile', username=user.username)
        else:
            # Forms are invalid - they'll be re-rendered with errors
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_user': user
    }
    return render(request, 'dashboard/profile_edit.html', context)

# @csrf_exempt
# def update_payment_method(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             order_id = data.get('order_id')
#             payment_method = data.get('payment_method')
            
#             order = Order.objects.get(id=order_id)
#             order.payment_method = payment_method
#             order.save()
            
#             return JsonResponse({'success': True})
#         except Order.DoesNotExist:
#             return JsonResponse({'success': False, 'error': 'Order not found'})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})
#     return JsonResponse({'success': False, 'error': 'Invalid request method'})



from django.shortcuts import get_object_or_404

def category_grid(request, username, table_number):
    table = get_object_or_404(Table, number=table_number, user__username=username)
    
    restaurant_profile = get_object_or_404(Profile, user=table.user)
    
    # If profile is set to category-first, redirect to the appropriate view
    if restaurant_profile.menu_display_mode == 'grid':
        return redirect('table_view', username=username, table_number=table_number)
    
    categories = Category.objects.filter(user=request.user, available=True).annotate(
        effective_sort_id=Case(
            When(sort_id__isnull=True, then=Value(999999)),
            default=F('sort_id'),
        )
    ).order_by('effective_sort_id')
    
    return render(request, 'category_grid.html', {
        'categories': categories,
        'table': table,
    })

def category_items(request, username, table_number, category_id):
    

    table = get_object_or_404(Table, number=table_number, user__username=username)
    category = get_object_or_404(Category, id=category_id, user=request.user)
    items = MenuItem.objects.filter(category=category, available=True, user=request.user)
    

    restaurant_profile = get_object_or_404(Profile, user=table.user)

     # If profile is set to category-first, redirect to the appropriate view
    # if restaurant_profile.menu_display_mode == 'grid':
    #     return redirect('table_view', username=username, table_number=table_number)
    
    return render(request, 'category_items.html', {
        'category': category,
        'items': items,
        'table': table,
        'cart_enabled': restaurant_profile.cart_enabled 
    })


# def table_view(request, username, table_number):
#     # Verify table belongs to the user
#     table = get_object_or_404(Table, number=table_number, user__username=username)
    
#     restaurant_profile = get_object_or_404(Profile, user=table.user)

#     # menu_items = MenuItem.objects.filter(available=True, user=table.user)
    
#     categories = Category.objects.filter(user=table.user,available=True).annotate(
#         effective_sort_id=Case(
#             When(sort_id__isnull=True, then=Value(999999)),
#             default=F('sort_id'),
#             #output_field=models.IntegerField()
#         )
#     ).order_by('effective_sort_id')

#     menu_items = MenuItem.objects.filter(
#         available=True,
#         user=table.user,
#         category__available=True  # Only items from available categories
        
#     )
    
#     return render(request, 'table.html', {
#         'table': table,
#         'menu_items': menu_items,
#         'categories': categories,
#         'restaurant': table.user,
#         'cart_enabled': restaurant_profile.cart_enabled 
#     })

@login_required
def menu_display_settings(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.menu_display_mode = request.POST.get('menu_display_mode', 'grid')
        profile.category_display_style = request.POST.get('category_display_style', 'buttons')
        profile.save()
        return redirect('dashboard')
    return render(request, 'dashboard/menu_display_settings.html', {
        'profile': profile
    })

def menu_display(request, username, table_number):
    table = get_object_or_404(Table, number=table_number, user__username=username)
    restaurant_profile = get_object_or_404(Profile, user=table.user)
    
    if restaurant_profile.menu_display_mode == 'category_first':
        return category_grid(request, username, table_number)
    else:
        return table_view(request, username, table_number)
    

def select_table(request, username):
    tables = Table.objects.filter(user__username=username)
    return render(request, 'table_select.html', {'tables': tables, 'username': username})



# views.py
from django.http import JsonResponse
import json

@csrf_exempt
def save_payment_methods(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id = data.get('order_id')
        payments = data.get('payments', [])

        order = Order.objects.get(id=order_id)
        order.payments.all().delete()  # Clear existing payments

        for payment in payments:
            method = payment.get('method')
            amount = payment.get('amount')
            if method and amount:
                OrderPayment.objects.create(order=order, method=method, amount=amount)

        return JsonResponse({
            'success': True,
            'display_text': ', '.join(
                f"{p['method'].capitalize()}: ₹{p['amount']}" for p in payments
            )
        })
    return JsonResponse({'success': False}, status=400)

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Order

# @csrf_exempt
# def update_payment_method(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         order_id = data.get('order_id')
#         payments = data.get('payments')

#         try:
#             order = Order.objects.get(id=order_id)
#             # Save payment methods (you may need to design how you want to store multiple methods)
#             order.payment_method = ','.join([p['method'] for p in payments])
#             order.payment_split = payments  # Optional: save as JSON field
#             order.save()
#             return JsonResponse({'success': True})
#         except Order.DoesNotExist:
#             return JsonResponse({'error': 'Order not found'}, status=404)
#     return JsonResponse({'error': 'Invalid request'}, status=400)

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# @login_required
# @require_http_methods(["GET"])
# def get_order_details(request, order_id):
#     is_combined = request.GET.get('combined', 'false').lower() == 'true'
    
#     if is_combined:
#         # Get combined order details
#         orders = Order.objects.filter(
#             combined_id=order_id,
#             user=request.user
#         )
#         total_amount = sum(order.final_total for order in orders)
#     else:
#         # Get single order details
#         order = get_object_or_404(Order, id=order_id, user=request.user)
#         total_amount = order.final_total
    
#     return JsonResponse({
#         'success': True,
#         'total_amount': str(total_amount)
#     })

@login_required
@require_http_methods(["GET"])
def get_order_details(request, order_id):
    is_combined = request.GET.get('combined', 'false').lower() == 'true'
    
    try:
        if is_combined:
            # Get combined order details
            orders = Order.objects.filter(
                combined_id=order_id,
                user=request.user
            )
            if not orders.exists():
                return JsonResponse({'success': False, 'error': 'No orders found with this combined ID'})
                
            total_amount = sum(order.final_total for order in orders)
            # Get unique payment methods from all orders in the combined order
            payment_methods = []
            for order in orders:
                payment_methods.extend(order.payment_methods)
            payment_methods = list(set(payment_methods))  # Get unique methods
            
            return JsonResponse({
                'success': True,
                'total_amount': str(total_amount),
                'payment_methods': payment_methods,
                'is_combined': True
            })
        else:
            # Get single order details
            order = get_object_or_404(Order, id=order_id, user=request.user)
            return JsonResponse({
                'success': True,
                'total_amount': str(order.final_total),
                'payment_methods': order.payment_methods,
                'is_combined': False
            })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_http_methods(["POST"])
def update_payment_methods(request, order_id):
    try:
        data = json.loads(request.body)
        methods = data.get('methods', [])
        amounts = data.get('amounts', [])
        is_combined = data.get('is_combined', False)
        
        if is_combined:
            # Update all orders in the combined order
            orders = Order.objects.filter(
                combined_id=order_id,
                user=request.user
            )
            
            # Distribute payments across orders (simplified implementation)
            for order in orders:
                order.payment_methods = methods
                order.save()
        else:
            # Update single order
            order = Order.objects.get(id=order_id, user=request.user)
            order.payment_methods = methods
            order.save()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# @login_required
# @require_http_methods(["POST"])
# def update_payment_methods(request, order_id):
#     try:
#         data = json.loads(request.body)
#         methods = data.get('methods', [])
#         amounts = data.get('amounts', [])
#         is_combined = data.get('is_combined', False)
        
#         if is_combined:
#             # Update all orders in the combined order
#             orders = Order.objects.filter(
#                 combined_id=order_id,
#                 user=request.user
#             )
#             for order in orders:
#                 order.payment_methods = methods
#                 if hasattr(order, 'payment_amounts'):
#                     order.payment_amounts = amounts
#                 order.save()
            
#             # Return complete data for all orders in the combined order
#             orders_data = []
#             for order in orders:
#                 orders_data.append({
#                     'id': order.id,
#                     'user_order_id': order.user_order_id,
#                     'payment_methods': order.payment_methods,
#                     'payment_amounts': getattr(order, 'payment_amounts', []),
#                     'final_total': str(order.final_total),
#                     'updated_at': order.updated_at.strftime("%I:%M %p")
#                 })
            
#             return JsonResponse({
#                 'success': True,
#                 'is_combined': True,
#                 'orders': orders_data,
#                 'combined_id': order_id
#             })
#         else:
#             # Update single order
#             order = Order.objects.get(id=order_id, user=request.user)
#             order.payment_methods = methods
#             if hasattr(order, 'payment_amounts'):
#                 order.payment_amounts = amounts
#             order.save()
            
#             return JsonResponse({
#                 'success': True,
#                 'is_combined': False,
#                 'order': {
#                     'id': order.id,
#                     'user_order_id': order.user_order_id,
#                     'payment_methods': order.payment_methods,
#                     'payment_amounts': getattr(order, 'payment_amounts', []),
#                     'final_total': str(order.final_total),
#                     'updated_at': order.updated_at.strftime("%I:%M %p")
#                 }
#             })
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)})