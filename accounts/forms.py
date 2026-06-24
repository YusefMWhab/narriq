from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts.models import MarketResearchCompany

class CompanyCodeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.code if obj.code else f"Code-{obj.id}"

class ExtendedSignupForm(UserCreationForm):
    profile_image = forms.ImageField(required=False, label="Profile Picture")
    full_name = forms.CharField(max_length=100, required=True, label="Full Name")
    email = forms.EmailField(required=True, label="Email Address")
    
    company_code = CompanyCodeChoiceField(
        queryset=MarketResearchCompany.objects.filter(is_active=True).exclude(code__isnull=True).exclude(code=''),
        required=True, 
        label="Company Access Code",
        empty_label="-- Select Your Company Code --"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)