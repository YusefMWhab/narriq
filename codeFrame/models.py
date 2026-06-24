import uuid
from django.db import models
from django.contrib.auth.models import User
from accounts.models import MarketResearchCompany
import os
def get_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return os.path.join('upload', f"{instance.id}_original.{ext}")


# To record the job and its status, we create a model that includes fields for the user, company, status, inputs, and the original file. The status field uses choices to restrict it to specific values (pending, processing, completed, failed). The inputs field is a JSONField that can store any relevant data needed for processing the job. The original_file field allows users to upload their files, and the get_upload_path function ensures that files are stored in a structured way based on the job ID.
class CodeFrame_AnalysisJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_jobs')
    company = models.ForeignKey(MarketResearchCompany, on_delete=models.CASCADE, related_name='company_analysis_jobs')    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    inputs = models.JSONField(default=dict, blank=True)
    
    original_file = models.FileField(upload_to=get_upload_path)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} - {self.user.username} ({self.status})"
    
# The result model is linked to the job with a OneToOne relationship, ensuring that each job has at most one result.
class CodeFrame_AnalysisResult(models.Model):
    job = models.OneToOneField(CodeFrame_AnalysisJob, on_delete=models.CASCADE, related_name='result')
    results = models.JSONField(default=dict, blank=True)

    total_records = models.IntegerField(default=0, verbose_name="All records in the dataset")
    processed_responses = models.IntegerField(default=0, verbose_name="All responses that were processed by the AI")
    extracted_codes_count = models.IntegerField(default=0, verbose_name="All codes extracted by the AI")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result for Job {self.job.id}"

class CodeFrame_CompanyUsageQuota(models.Model):
    
    company = models.OneToOneField(
        MarketResearchCompany, 
        on_delete=models.CASCADE, 
        related_name='usage_quota'
    )
    
    allowed_responses = models.IntegerField(default=0)
    used_responses = models.IntegerField(default=0)
    
    valid_until = models.DateTimeField(blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def remaining_responses(self):
        return max(0, self.allowed_responses - self.used_responses)

    def __str__(self):
        return f"{self.company.name} Quota: {self.used_responses}/{self.allowed_responses} responses used"