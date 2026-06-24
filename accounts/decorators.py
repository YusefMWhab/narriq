from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages


def tool_access_required(permission_field,redirect_page):
   
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # 1. User existed in DB
            if not request.user.is_authenticated:
                return redirect('auth_page')

            # 2. Tool Accessability
            has_access = getattr(request.user.profile, permission_field, False)

            if not has_access:
                messages.error(request,'You have no access to this Option')
                return redirect(redirect_page)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator