from django.contrib.auth.forms import AuthenticationForm
from .forms import ExtendedSignupForm
from django.contrib.auth import login as auth_login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache

@never_cache
def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    login_form = AuthenticationForm()
    signup_form = ExtendedSignupForm()
    active_tab = 'login' 

    if request.method == 'POST':
        if 'signup_submit' in request.POST:
            active_tab = 'signup'
            signup_form = ExtendedSignupForm(request.POST, request.FILES) 
            
            if signup_form.is_valid():
                user = signup_form.save(commit=False)
                
                full_name = signup_form.cleaned_data.get('full_name', '')
                email_address = signup_form.cleaned_data.get('email')
               
                selected_company = signup_form.cleaned_data.get('company_code') 
                
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                user.email = email_address
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                user.save() 
                
                
                profile = user.profile
                profile.full_name = full_name
                profile.email = email_address
                
                profile.company = selected_company 
                
                if 'profile_image' in request.FILES:
                    profile.image = request.FILES['profile_image']

                profile.save()

                messages.success(request, "Account has been created successfully. Wait for activation")
                return redirect('auth_page')
            else:
                messages.error(request, "Error in form validation.")
        
        elif 'login_submit' in request.POST:
            active_tab = 'login'
            login_form = AuthenticationForm(request, data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                if hasattr(user, 'profile') and user.profile.is_active:
                    user_profile = user.profile
                    if user_profile.company and not user_profile.company.is_active:
                        messages.error(request, "Your company's contract is inactive. Please contact your administrator.")
                    else:
                        auth_login(request, user)
                        return redirect('dashboard')
                else:
                    messages.warning(request, "Your account is pending for activation")
            else:
                messages.error(request, "Username or Password is not correct")

    context = {
        'login_form': login_form,
        'signup_form': signup_form,
        'active_tab': active_tab,
    }
    return render(request, 'auth.html', context)

def logout_view(request):
    logout(request)
    return redirect('auth_page')