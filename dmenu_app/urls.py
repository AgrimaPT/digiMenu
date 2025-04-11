from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('',views.SignupPage,name='signup'),
    path('login/',views.LoginPage,name='login'),
    path('logout/',views.LogoutPage,name='logout'),


    # path('table/<int:table_number>/', views.customer_details, name='customer_details'),
    path('table/<int:table_number>/', views.table_view, name='table_view'),
    # path('order/<int:order_id>/', views.order_summary, name='order_summary'),
    # path('resolve_call/<int:table_id>/', views.resolve_call, name='resolve_call'),
    
    path('dashboard/', views.dashboard_home, name='dashboard_home'),
    path('<str:username>/dashboard/', views.dashboard_home, name='dashboard_home'),
    
    path('dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),

    #path('confirm_order/<int:table_id>/', views.confirm_order, name='confirm_order'),
    path('order_success/',views.order_success,name='order_success'),
    path('dashboard/orders/',views.dashboard_orders,name='dashboard_orders'),
    path('dashboard/categories/', views.dashboard_categories, name='dashboard_categories'),
    path('dashboard/categorie/add/', views.add_category, name='add_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'), 


    path('dashboard/items/', views.dashboard_items, name='dashboard_items'),
    path('dashboard/item/add/', views.add_item, name='add_item'),
    path('items/delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('items/edit/<int:item_id>/', views.edit_item, name='edit_item'), 
    path('menu/item/<int:item_id>/update-availability/', views.update_availability, name='update_availability'), 

    #path('table/<int:table_id>/pending-orders/', views.table_pending_orders, name='table_pending_orders'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('table/<int:table_id>/completed-orders/', views.completed_orders, name='completed_orders'),
    # path('order/<int:order_id>/complete/', views.mark_order_completed, name='mark_order_completed'),
    path('update-item-status/', views.update_item_status, name='update_item_status'),
    path('order-details/<int:order_id>/', views.order_details, name='order_details'),
    path('mark-items-completed/', views.mark_items_completed, name='mark_items_completed'),

    path('generate-bill/<int:order_id>/',views.generate_bill, name='generate_bill'),
    path('generate-combined-bill/', views.generate_combined_bill, name='generate_combined_bill'),
    path('api/get-initial-table-state/', views.get_initial_table_state, name='get_initial_table_state'),
    path('api/orders/state/', views.get_orders_state, name='orders_state'),

    path('billed-orders/<int:table_number>/', views.billed_orders, name='billed_orders'),




    path('<str:username>/table/<str:table_number>/', views.table_view, name='table_view'),
    path('<str:username>/table/<str:table_number>/confirm/', views.confirm_order, name='confirm_order'),
    path('<str:username>/table/<str:table_number>/success/', views.order_success, name='order_success'),
    
    
    path('<str:username>/dashboard/', views.dashboard_home, name='dashboard_home'),
    path('<str:username>/dashboard/categories/', views.dashboard_categories, name='dashboard_categories'),
    path('<str:username>/dashboard/items/', views.dashboard_items, name='dashboard_items'),
    path('<str:username>/dashboard/categories/add/', views.add_category, name='add_category'),
    path('<str:username>/dashboard/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('<str:username>/dashboard/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),    
    path('<str:username>/dashboard/items/add/', views.add_item, name='add_item'),
    path('<str:username>/dashboard/items/delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('<str:username>/dashboard/items/edit/<int:item_id>/', views.edit_item, name='edit_item'),
    path('<str:username>/items/availability/<int:item_id>/', views.update_availability, name='update_availability'),
    

    path('<str:username>/tables/add/', views.add_table, name='add_table'),

    path('<str:username>/dashboard/orders/', views.dashboard_orders, name='dashboard_orders'),
    path('<str:username>/table/<int:table_id>/pending-orders/', views.table_pending_orders, name='table_pending_orders'),
    path('<str:username>/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('<str:username>/table/<int:table_id>/completed-orders/', views.completed_orders, name='completed_orders'),
    path('<str:username>/order-details/<int:order_id>/', views.order_details, name='order_details'),
    path('<str:username>/update-item-status/', views.update_item_status, name='update_item_status'),
    path('update-payment-method/<int:order_id>/', views.update_payment_method, name='update_payment_method'),

    path('reset_password/',auth_views.PasswordResetView.as_view(template_name="dashboard/password_reset.html"),name="reset_password"),
    path('reset_password_sent/',auth_views.PasswordResetDoneView.as_view(template_name="dashboard/password_reset_done.html"),name="password_reset_done"),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="dashboard/password_reset_confirm.html"),name="password_reset_confirm"),
    path('reset_password_complete/',auth_views.PasswordResetCompleteView.as_view(template_name="dashboard/password_reset_complete.html"),name="password_reset_complete"),

    path('test-email/', views.test_email, name='test_email'),
    path('api/check-unbilled-orders/', views.check_unbilled_orders, name='check_unbilled_orders'),
    # path('reports/sales/', views.daily_sales_report, name='sales_report'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
