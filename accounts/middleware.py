from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import reverse
from django.urls import reverse, resolve
from django.urls.exceptions import Resolver404
import os


class GlobalAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Superusers have unrestricted access, so we can skip all checks for them
        if request.user.is_authenticated and request.user.is_superuser:
            return self.get_response(request)
        
        ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'secure-admin-fallback/')
        if not ADMIN_URL.startswith('/'):
            ADMIN_URL = '/' + ADMIN_URL
            
        if not request.user.is_authenticated:

            try:
                resolve(request.path)
            except Resolver404:
                return self.get_response(request)
            
            is_allowed = (
                request.path == reverse('home') or
                request.path == reverse('contact') or
                request.path == reverse('auth_page') or 
                request.path.startswith(ADMIN_URL) or 
                request.path.startswith('/static/')
            )
            
            if not is_allowed:
                return redirect('auth_page')
        
        else:
            allowed_paths = [reverse('auth_page'), reverse('contact'), ADMIN_URL]
            if request.path not in allowed_paths and not request.path.startswith(ADMIN_URL):
                if not hasattr(request.user, 'profile') or not request.user.profile.is_active:
                    logout(request)
                    return redirect('auth_page')
                user_profile = request.user.profile
                if user_profile.company and not user_profile.company.is_active:
                    logout(request)
                    return redirect('auth_page')

        return self.get_response(request)