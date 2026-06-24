from django.contrib import admin
from .models import CodeFrame_AnalysisJob, CodeFrame_AnalysisResult, CodeFrame_CompanyUsageQuota
from django.utils.safestring import mark_safe
import json

class CodeFrame_AnalysisResultInline(admin.StackedInline):
    model = CodeFrame_AnalysisResult
    extra = 0
    readonly_fields = ['created_at']

@admin.register(CodeFrame_AnalysisJob)
class CodeFrame_AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'company', 'status', 'created_at', 'updated_at']
    
    list_filter = ['status', 'created_at', 'company']
    
    search_fields = ['id', 'user__username', 'company__name'] 

    readonly_fields = ['id', 'created_at', 'updated_at']
    
    inlines = [CodeFrame_AnalysisResultInline]

@admin.register(CodeFrame_AnalysisResult)
class CodeFrame_AnalysisResultAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'get_job_id', 
        'get_company_name', 
        'total_records', 
        'processed_responses', 
        'extracted_codes_count', 
        'created_at'
    )
    
    list_filter = ('created_at', 'job__company', 'job__user')
    
    search_fields = ('job__id', 'job__company__name', 'job__user__username')
    
    readonly_fields = ('job', 'total_records', 'processed_responses', 'extracted_codes_count', 'created_at', 'pretty_results')
    
    fieldsets = (
        ('Job & Context Information', {
            'fields': ('job', 'created_at')
        }),
        ('Processing & Quota Metrics', {
            'fields': ('total_records', 'processed_responses', 'extracted_codes_count'),
            'description': 'Metrics extracted during the AI execution loop.'
        }),
        ('AI Output Data', {
            'fields': ('pretty_results',),
        }),
    )
    
    exclude = ('results',)

    def pretty_results(self, instance):
        """Formats the JSONField into a readable HTML block with syntax-like styling."""
        if not instance.results:
            return "No data available"
        
        response_json = json.dumps(instance.results, indent=4, ensure_ascii=False)
        
        return mark_safe(
            f'<pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 8px; '
            f'font-family: monospace; font-size: 0.9rem; max-height: 500px; overflow-y: auto;">'
            f'{response_json}</pre>'
        )
    pretty_results.short_description = "Analysis Results (Formatted JSON)"

    def get_job_id(self, obj):
        return f"Job #{obj.job.id}"
    get_job_id.short_description = 'Job ID'
    get_job_id.admin_order_field = 'job__id'

    def get_company_name(self, obj):
        return obj.job.company.name
    get_company_name.short_description = 'Company'

@admin.register(CodeFrame_CompanyUsageQuota)
class CodeFrame_CompanyUsageQuotaAdmin(admin.ModelAdmin):
    list_display = ('company', 'allowed_responses', 'used_responses', 'remaining_responses_display', 'valid_until', 'updated_at')
    search_fields = ('company__name',)
    list_editable = ('allowed_responses', 'used_responses')
    list_filter = ('valid_until',)

    # حركة شياكة توريق الرصيد المتبقي بلون مميز في الـ Admin
    def remaining_responses_display(self, obj):
        remaining = obj.remaining_responses
        if remaining < 500: # لو رصيد الشركة قرب يخلص ينور أحمر
            return mark_safe(f'<strong style="color: #dc3545;">{remaining} responses</strong>')
        return mark_safe(f'<strong style="color: #28a745;">{remaining} responses</strong>')
    remaining_responses_display.short_description = 'Remaining Quota'