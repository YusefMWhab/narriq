from django.shortcuts import redirect, render
from django.contrib import messages
from accounts.utils import send_user_notification
from django.http import HttpResponse

# Create your views here.
def landingPage(request):

    context = {
        
    }
    return render(request, 'landing.html', context)


def contact_view(request):
    print("Contact view called")
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company = request.POST.get('company')
        email = request.POST.get('email')
        interest = request.POST.get('interest')
        message = request.POST.get('message')

        subject = f"New Access Request: {company}"
        body = f"User {first_name} {last_name} ({email}) is interested in {interest}.\n\nMessage: {message}"
        
        # Calling your function
        success = send_user_notification(subject, body, 'youssefmwhab@gmail.com')

        if success:
            messages.success(request, "Request sent successfully!")
            # Send a confirmation email to the user
            confirmation_subject = "NarrIQ: Your Access Request has been received"
            confirmation_body = f"Dear {first_name},\n\nThank you for your interest in our product.\n We have received your request and will get back to you shortly.\n\nBest regards,\nNarrIQ Team"
            send_user_notification(confirmation_subject, confirmation_body, email)
        else:
            messages.error(request, "Failed to send email. Please try again later.")
            
        return redirect('home')
    