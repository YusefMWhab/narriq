from django.urls import path
from . import views

urlpatterns = [
    path('welcome/', views.auth_view, name='auth_page'),
    path('logout/', views.logout_view, name='logout'),

]