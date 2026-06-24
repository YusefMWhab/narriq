from django.urls import path
from . import views

urlpatterns = [
    path('jobs/new/', views.codeFrame_newJob, name='CodeFrame_newJob'),
    path('jobs/create/', views.codeFrame_create_job, name='codeFrame_create_job'),
    path('jobs/list/', views.codeFrame_jobs_list, name='CodeFrame_jobs_list'), 
    path('jobs/<uuid:job_id>/details/', views.codeFrame_job_details, name='CodeFrame_details'),
    path('jobs/update-codebook/', views.codeFrame_update_codebook, name='CodeFrame_update_codebook'),
    path('jobs/update-dataset/', views.codeFrame_update_dataset, name='CodeFrame_update_dataset'),
    path('jobs/<uuid:job_id>/download/', views.codeFrame_download_results, name='CodeFrame_download_results'),
]