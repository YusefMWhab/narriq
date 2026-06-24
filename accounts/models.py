from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

# For Market Research Companies
class MarketResearchCompany(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Company Name")
    code = models.CharField(max_length=50, unique=True, null=False, blank=False, verbose_name="Company Code")
    is_active = models.BooleanField(default=False, verbose_name="Is Active Contract?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Market Research Company"
        verbose_name_plural = "Market Research Companies"

# ====================================================================================
# For User Profiles
class UserProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    full_name = models.CharField(max_length=255, null=True, blank=True)

    email = models.EmailField(max_length=255, null=True, blank=True)
    
    image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    company = models.ForeignKey(
        MarketResearchCompany, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='employees',
        verbose_name="Affiliated Company"
    )

    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.full_name or ''} ({self.company.name if self.company else 'No Company'})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

