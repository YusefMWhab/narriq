from django.template import loader
from django.shortcuts import render
from django.db.models import Sum

from codeFrame.models import CodeFrame_AnalysisJob, CodeFrame_CompanyUsageQuota, CodeFrame_AnalysisResult

# Create your views here.

def dashboard(request):
    user = request.user
    profile = user.profile
    company = profile.company

    user_jobs_count = CodeFrame_AnalysisJob.objects.filter(
        user=user, 
        status='completed'
    ).count()

    user_stats = CodeFrame_AnalysisResult.objects.filter(
        job__user=user,
        job__status='completed'
    ).aggregate(
        total_rec=Sum('total_records'),
        total_resp=Sum('processed_responses'),
        total_codes=Sum('extracted_codes_count')
    )

    # استخراج القيم المجمعة وأمان الـ None بـ "or 0"
    user_total_records = user_stats['total_rec'] or 0
    user_total_responses = user_stats['total_resp'] or 0
    user_total_codes = user_stats['total_codes'] or 0


    quota, created = CodeFrame_CompanyUsageQuota.objects.get_or_create(company=company)



    


    context = {
        # User-specific stats
        'user_jobs_count': user_jobs_count,
        'user_total_records': user_total_records,
        'user_total_responses': user_total_responses,
        'user_total_codes': user_total_codes,

        # Company quota details
        'allowed_responses': quota.allowed_responses,
        'used_responses': quota.used_responses,
        'remaining_responses': quota.remaining_responses,
        'valid_until': quota.valid_until,
        'quota_pct': (quota.used_responses / quota.allowed_responses) * 100 if quota.allowed_responses > 0 else 0,

    }

    return render(request, 'dashboard.html', context)


def documentation_view(request):

    template = loader.get_template('documentation.html')

    context = {
        
    }
    return render(request, 'documentation.html')