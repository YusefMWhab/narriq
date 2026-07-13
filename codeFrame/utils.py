from celery import shared_task
from codeFrame.services.codeframe_service import CodeFrameService
from django.contrib.auth.models import User
from .models import CodeFrame_AnalysisJob

@shared_task
def CodeFrame_StartProcess(job_id):
    job = None
    try:
        job = CodeFrame_AnalysisJob.objects.get(id=job_id)
        
        job.status = 'processing'
        job.save()

        method = job.inputs.get("method")
        projectLanguage = job.inputs.get("project_language")
        projectResultLanguage = job.inputs.get("project_resultLanguage")
        projectDesc = job.inputs.get("project_description")
        userMapping = job.inputs.get("user_mapping")
        temp_path = job.original_file.name
        userId = job.user.id

        CodeFrameService(temp_path, method, projectLanguage, projectResultLanguage, projectDesc, userMapping, job_id=job.id)

    except Exception as e:
        print(f"Error in Celery Task Execution: {str(e)}")
        if job:
            job.status = 'failed'
            if isinstance(job.inputs, dict):
                job.inputs["error_log"] = str(e)
            job.save()


def CodeFrame_CreateJob(temp_path, method, project_Language, projectResultLanguage, projectDesc, userMapping, userId):
    try:
        user = User.objects.get(id=userId)
        user_company = user.profile.company 
        
        job_inputs = {
            "method": method,
            "project_language": project_Language,
            "project_resultLanguage": projectResultLanguage,
            "project_description": projectDesc,
            "user_mapping": userMapping
        }
        
        job = CodeFrame_AnalysisJob.objects.create(
            user=user,
            company=user_company,
            status='pending',
            inputs=job_inputs,
            original_file=temp_path
        )
        
        CodeFrame_StartProcess.apply_async(args=[str(job.id)])
        
        return
        
    except Exception as e:
        print(f"Error creating job in database: {str(e)}")
        raise