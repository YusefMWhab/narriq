from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile, MarketResearchCompany

# 1. Custom Admin for MarketResearchCompany
@admin.register(MarketResearchCompany)
class MarketResearchCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)

# 2. Custom Admin for UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'show_photo',         
        'user', 
        'get_email', 
        'full_name',
        'company',           
        'is_active', 
    )
    
    list_editable = (
        'is_active', 
    )
    
    search_fields = (
        'full_name', 
        'email', 
        'user__username',
        'company__name'      
    )
    
    list_filter = (
        'is_active', 
        'company',           
    )

  
    def show_photo(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />', obj.image.url)
        return "No Photo"
    show_photo.short_description = 'Photo'

    # دالة جلب الإيميل
    def get_email(self, obj):
        return obj.email or obj.user.email 
    get_email.short_description = 'Email Address'