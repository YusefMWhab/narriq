from io import BytesIO
import io
from django.contrib import messages
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, Http404
import pandas as pd
import json
from django.core.files.storage import default_storage
from datetime import datetime
from django.utils import timezone
from django.db import transaction
from codeFrame.models import CodeFrame_AnalysisJob, CodeFrame_AnalysisResult, CodeFrame_CompanyUsageQuota
from codeFrame.loaders.prompts_loader import get_all_categories
from codeFrame.services.FileManager import CodeFrame_ExportData
from codeFrame.utils import CodeFrame_CreateJob
# Create your views here.

# View to render the new job form
def codeFrame_newJob(request):

    categories = get_all_categories()
    

    context = {
        "categories": categories
    }

    return render(request, 'codeFrame_newJob.html', context)

# API endpoint to create a new job
def codeFrame_create_job(request):
    if request.method == 'POST':
        # Process the form data and create a new job
        try:
            data_file = request.FILES.get("dataFile")
            method = request.POST.get("method")
            project_category = request.POST.get("projectCategory")
            project_description = request.POST.get("projectDescription")

            # JSON string → object
            user_mapping_raw = request.POST.get("userMapping")
            user_mapping = json.loads(user_mapping_raw) if user_mapping_raw else None
            
            # FILE METHOD
            if method == "file":
                df = pd.read_excel(data_file)
                
            # TEXT METHOD
            elif method == "text":

                # read text file content
                text_content = data_file.read().decode("utf-8")
                # split lines
                lines = text_content.splitlines()

                # convert to dataframe
                df = pd.DataFrame(lines, columns=["text"])

            # Check if the user has an active company and usage quota
            # Company Quota
            try:
                user_profile = request.user.profile
                company = user_profile.company
                if not company:
                    return JsonResponse({
                        "status": "error", 
                        "message": "Your account is not associated with any company. Please contact your administrator."
                    }, status=403)
                    
                if not company.is_active:
                    return JsonResponse({
                        "status": "error", 
                        "message": "Your company's contract is inactive. Please contact your administrator."
                    }, status=403)
                
                quota, created = CodeFrame_CompanyUsageQuota.objects.get_or_create(company=company)
            except Exception as e:
                return JsonResponse({"status": "error", "message": "Error verification company profile."}, status=500)
            
            selected_columns = [item["column"] for item in user_mapping]
            
            total_records_needed = int(df[selected_columns].count().sum())
            
            if quota.used_responses + total_records_needed > quota.allowed_responses:
                return JsonResponse({
                    "status": "error",
                    "message": f"Operation denied! This file contains {total_records_needed} rows, but your company's remaining quota is only {quota.remaining_responses} rows. Please contact management to upgrade your plan."
                }, status=400)
            
            if quota.valid_until and quota.valid_until < timezone.now():
                    return JsonResponse({
                        "status": "error",
                        "message": f"Your company's plan expired on {quota.valid_until.strftime('%Y-%m-%d')}. Please renew your subscription."
                    }, status=403)
            
            

            # SAVE EXCEL
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_filename = f"job_{timestamp}.xlsx"

            # Save excel in memory
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)

            # Save to default storage
            temp_path = default_storage.save(
                f"Code_Frame/Job/{output_filename}",
                ContentFile(excel_buffer.read())
            )

            # Start processing the job
            CodeFrame_CreateJob(temp_path, method, project_category, project_description, user_mapping, request.user.id)
            

            return JsonResponse({
                "status": "success"
            })
        
        except json.JSONDecodeError:
            print("error parsing JSON data")
            return JsonResponse({
                "status": "error",
                "message": "Invalid JSON data"
            }, status=400)
        
# Dashboard page to list all jobs        
def codeFrame_jobs_list(request):
    
    jobs = CodeFrame_AnalysisJob.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'jobs': jobs
    }
    return render(request, 'codeFrame_jobsList.html', context)

# Job details page
def codeFrame_job_details(request, job_id):
    # 1. Get the Job
    job = get_object_or_404(CodeFrame_AnalysisJob, id=job_id, user=request.user)
    
    # Prepare Context
    context = {
        'job': job,
        'total_records': 0,        # Total records
        'total_responses': 0,    # Total responses
        'total_codes': 0,          # Total codes
        'avg_codes_per_response': 0,  # Average codes per response
        'available_columns': [],   # Available columns
        'full_result_json': '{}'   # Full result JSON
    }

    try:
        # 1. Get the analysis result for the job
        analysis_result = job.result
        result_json = analysis_result.results
        
        if result_json:

            context['total_records'] = analysis_result.total_records
            context['total_responses'] = analysis_result.processed_responses
            context['total_codes'] = analysis_result.extracted_codes_count
            
            # Get all columns data 
            sheet_data = result_json.get('sheet_Data', {})
            available_columns = list(sheet_data.keys())
            context['available_columns'] = available_columns
            
            project_total_statements = 0
            for col_name, col_content in sheet_data.items():
                    
                    entries = col_content if isinstance(col_content, list) else []
                    for entry in entries:
                        final_ids_str = entry.get('Final IDs', '')
                        if final_ids_str:
                            final_ids = [id.strip() for id in final_ids_str.split(',') if id.strip()]
                            project_total_statements += len(final_ids)
                    
            context['avg_codes_per_response'] = round(project_total_statements / context['total_responses'], 2) if context['total_responses'] > 0 else 0
            
            context['full_result_json'] = json.dumps(result_json)

    except CodeFrame_AnalysisResult.DoesNotExist:
        pass

    return render(request, 'codeFrame_job_details.html', context)

# View to update codebook
def codeFrame_update_codebook(request):   
    try:
        body_data = json.loads(request.body)
        job_id = body_data.get('job_id')
        action = body_data.get('action') # 'update', 'delete', 'merge'
        
        if not job_id or not action:
            return JsonResponse({'status': 'error', 'message': 'Missing job_id or action.'}, status=400)
        
        with transaction.atomic():
            
            job = CodeFrame_AnalysisJob.objects.select_for_update().get(id=job_id, user=request.user)
            analysis_result = job.result
            result_json = analysis_result.results

            if isinstance(result_json, str):
                result_json = json.loads(result_json)
                
            codebook = result_json.get("CodeBook", {})
            sheet_data = result_json.get("sheet_Data", {})

            # ====================================================================
            # ACTION: UPDATE 
            # ====================================================================
            if action == 'update':
                code_id = str(body_data.get('code_id'))
                new_text = body_data.get('new_text')
                
                if not code_id or not new_text:
                    return JsonResponse({'status': 'error', 'message': 'Missing code_id or new_text'}, status=400)
                if code_id not in codebook:
                    return JsonResponse({'status': 'error', 'message': 'Code ID not found in CodeBook.'}, status=404)
                
                codebook[code_id] = new_text
                
                for sheet_name, rows in sheet_data.items():
                    for row in rows:
                        ids_list = [x.strip() for x in str(row.get('Final IDs', '')).split(',') if x.strip()]
                        texts_list = [x.strip() for x in str(row.get('Final Text', '')).split(',') if x.strip()]
                        
                        if code_id in ids_list:
                            for idx, current_id in enumerate(ids_list):
                                if current_id == code_id and idx < len(texts_list):
                                    texts_list[idx] = new_text
                            row['Final Text'] = ", ".join(texts_list)

            # ====================================================================
            # ACTION: DELETE
            # ====================================================================
            elif action == 'delete':
                code_id = str(body_data.get('code_id'))
                if not code_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing code_id'}, status=400)
                if code_id not in codebook:
                    return JsonResponse({'status': 'error', 'message': 'Code ID not found in CodeBook.'}, status=404)
                
                del codebook[code_id]
                
                for sheet_name, rows in sheet_data.items():
                    for row in rows:
                        ids_list = [x.strip() for x in str(row.get('Final IDs', '')).split(',') if x.strip()]
                        texts_list = [x.strip() for x in str(row.get('Final Text', '')).split(',') if x.strip()]
                        
                        if code_id in ids_list:
                            new_ids = []
                            new_texts = []
                            for idx, current_id in enumerate(ids_list):
                                if current_id != code_id:
                                    new_ids.append(current_id)
                                    if idx < len(texts_list):
                                        new_texts.append(texts_list[idx])
                                        
                            row['Final IDs'] = ", ".join(new_ids)
                            row['Final Text'] = ", ".join(new_texts)
                            
                analysis_result.extracted_codes_count = len(codebook)

            # ====================================================================
            # ACTION: MERGE
            # ====================================================================
            elif action == 'merge':
                source_id = str(body_data.get('source_code_id'))
                target_id = str(body_data.get('target_code_id'))
                
                if not source_id or not target_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing source_code_id or target_code_id'}, status=400)
                if source_id not in codebook or target_id not in codebook:
                    return JsonResponse({'status': 'error', 'message': 'One or both Code IDs not found in CodeBook.'}, status=404)
                
                target_text = codebook[target_id]
                del codebook[source_id]
                
                for sheet_name, rows in sheet_data.items():
                    for row in rows:
                        ids_list = [x.strip() for x in str(row.get('Final IDs', '')).split(',') if x.strip()]
                        texts_list = [x.strip() for x in str(row.get('Final Text', '')).split(',') if x.strip()]
                        
                        if source_id in ids_list:
                            new_ids = []
                            new_texts = []
                            
                            for idx, current_id in enumerate(ids_list):
                                if current_id == source_id:
                                    if target_id not in new_ids:
                                        new_ids.append(target_id)
                                        new_texts.append(target_text)
                                else:
                                    new_ids.append(current_id)
                                    if idx < len(texts_list):
                                        new_texts.append(texts_list[idx])
                                        
                            row['Final IDs'] = ", ".join(new_ids)
                            row['Final Text'] = ", ".join(new_texts)
                            
                analysis_result.extracted_codes_count = len(codebook)

            # ====================================================================
            # ACTION: ADD NEW CODE
            # ====================================================================
            elif action == 'add_code':
                new_text = body_data.get('new_text', '').strip()
                
                if not new_text:
                    return JsonResponse({'status': 'error', 'message': 'Code text cannot be empty.'}, status=400)
                
                
                if new_text.lower() in [v.lower() for v in codebook.values()]:
                    return JsonResponse({'status': 'error', 'message': 'Code already exists.'}, status=400)
                
                existing_ids = [int(k) for k in codebook.keys() if k.isdigit()]
                new_id = str(max(existing_ids) + 1) if existing_ids else '1'
                
                if new_id == 99:
                    new_id += 1  # Skip ID 99 reserved for "Unassigned"
                
                codebook[new_id] = new_text
                analysis_result.extracted_codes_count = len(codebook)

            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action type.'}, status=400)

            
            result_json["CodeBook"] = codebook
            result_json["sheet_Data"] = sheet_data
            analysis_result.results = result_json
            analysis_result.save()

            total_responses = analysis_result.processed_responses 
            total_assigned_codes = 0
            
            for col_name, rows in sheet_data.items():
                entries = rows if isinstance(rows, list) else []
                for row in entries:
                    final_ids_str = row.get('Final IDs', '')
                    if final_ids_str:
                        ids = [x.strip() for x in str(final_ids_str).split(',') if x.strip()]
                        total_assigned_codes += len(ids)

            avg_codes_per_response = round(total_assigned_codes / total_responses, 2) if total_responses > 0 else 0

            return JsonResponse({
                'status': 'success', 
                'message': f'Codebook updated successfully via {action}.',
                'new_codebook': codebook,
                'new_sheet_data': sheet_data,
                'current_codes_count': analysis_result.extracted_codes_count, 
                'new_avg_codes': avg_codes_per_response                    
            })

    except CodeFrame_AnalysisJob.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Job not found or unauthorized.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'}, status=500)
    
# View to update dataset
def codeFrame_update_dataset(request):
    try:
        body_data = json.loads(request.body)
        job_id     = body_data.get('job_id')
        action     = body_data.get('action')   # 'remove', 'add', 'replace'
        column     = body_data.get('column')   
        record_id  = body_data.get('record_id')  # ID of the response/row being updated

        if not all([job_id, action, column, record_id  is not None]):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields.'}, status=400)
        
        with transaction.atomic():
            job = CodeFrame_AnalysisJob.objects.select_for_update().get(id=job_id, user=request.user)
            analysis_result = job.result
            result_json = analysis_result.results

            if isinstance(result_json, str):
                result_json = json.loads(result_json)

            codebook   = result_json.get("CodeBook", {})
            sheet_data = result_json.get("sheet_Data", {})

            if column not in sheet_data:
                return JsonResponse({'status': 'error', 'message': 'Column not found.'}, status=404)
            
            rows = sheet_data[column]

            record_id = int(record_id)
            row = next((r for r in rows if int(r.get('id', -1)) == record_id), None)
            if not row:
                return JsonResponse({'status': 'error', 'message': 'Record not found.'}, status=404)

            ids_list   = [x.strip() for x in str(row.get('Final IDs',  '')).split(',') if x.strip()]
            texts_list = [x.strip() for x in str(row.get('Final Text', '')).split(',') if x.strip()]


            # ================================================================
            # ACTION: REMOVE Code Assignment from Response
            # ================================================================
            if action == 'remove':

                code_id = str(body_data.get('code_id'))
                if not code_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing code_id.'}, status=400)

                new_ids, new_texts = [], []
                for idx, cid in enumerate(ids_list):
                    if cid != code_id:
                        new_ids.append(cid)
                        if idx < len(texts_list):
                            new_texts.append(texts_list[idx])

                row['Final IDs']  = ", ".join(new_ids)
                row['Final Text'] = ", ".join(new_texts)
            
            # ================================================================
            # ACTION: ADD Code Assignment to Response
            # ================================================================
            elif action == 'add':
                code_id = str(body_data.get('code_id'))
                if not code_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing code_id.'}, status=400)
                if code_id not in codebook:
                    return JsonResponse({'status': 'error', 'message': 'Code ID not found in CodeBook.'}, status=404)

                # منع التكرار
                if code_id not in ids_list:
                    ids_list.append(code_id)
                    texts_list.append(codebook[code_id])

                row['Final IDs']  = ", ".join(ids_list)
                row['Final Text'] = ", ".join(texts_list)

            # ================================================================
            # ACTION: REPLACE Code Assignment in Response
            # ================================================================
            elif action == 'replace':
                old_code_id = str(body_data.get('old_code_id'))
                new_code_id = str(body_data.get('new_code_id'))

                if not old_code_id or not new_code_id:
                    return JsonResponse({'status': 'error', 'message': 'Missing old_code_id or new_code_id.'}, status=400)
                if new_code_id not in codebook:
                    return JsonResponse({'status': 'error', 'message': 'New Code ID not found in CodeBook.'}, status=404)

                new_ids, new_texts = [], []
                for idx, cid in enumerate(ids_list):
                    if cid == old_code_id:
                        # استبدل بس لو الكود الجديد مش موجود أصلاً
                        if new_code_id not in new_ids:
                            new_ids.append(new_code_id)
                            new_texts.append(codebook[new_code_id])
                        # لو موجود — امسح القديم بس
                    else:
                        new_ids.append(cid)
                        if idx < len(texts_list):
                            new_texts.append(texts_list[idx])

                row['Final IDs']  = ", ".join(new_ids)
                row['Final Text'] = ", ".join(new_texts)

            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)

            # حفظ
            result_json["sheet_Data"] = sheet_data
            analysis_result.results   = result_json
            analysis_result.save()

            total_responses = analysis_result.processed_responses 
            total_assigned_codes = 0
            
            for col_name, rows in sheet_data.items():
                entries = rows if isinstance(rows, list) else []
                for row in entries:
                    final_ids_str = row.get('Final IDs', '')
                    if final_ids_str:
                        ids = [x.strip() for x in str(final_ids_str).split(',') if x.strip()]
                        total_assigned_codes += len(ids)

            avg_codes_per_response = round(total_assigned_codes / total_responses, 2) if total_responses > 0 else 0

            return JsonResponse({
                'status':        'success',
                'message':       f'Response updated via {action}.',
                'new_sheet_data': sheet_data,
                'new_codebook':   codebook,
                'current_codes_count': analysis_result.extracted_codes_count, 
                'new_avg_codes': avg_codes_per_response 
            })

    except CodeFrame_AnalysisJob.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Job not found or unauthorized.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Server Error: {str(e)}'}, status=500)



# View to download results as Excel
def codeFrame_download_results(request, job_id):
    job = get_object_or_404(CodeFrame_AnalysisJob, id=job_id, user=request.user)
    
    try:
        analysis_result = job.result
        result_json = analysis_result.results

        if isinstance(result_json, str):
            result_json = json.loads(result_json)

        structured_data = {
            "CodeBook": result_json.get("CodeBook", {}), 
            "sheet_Data": {}
        }

        sheet_data_raw = result_json.get('sheet_Data', {})

        for sheet_name, rows_list in sheet_data_raw.items():

            df_sheet = pd.DataFrame(rows_list)

            # Drop columns that are not needed in the Excel export
            columns_to_hide = ["CrossEncoder", "Split Results"]
            df_sheet = df_sheet.drop(columns=columns_to_hide, errors='ignore')

            structured_data["sheet_Data"][sheet_name] = df_sheet

        success, result_output = CodeFrame_ExportData(structured_data) 
        
        if isinstance(result_output, io.BytesIO):
            file_stream = result_output.getvalue()
        else:
            file_stream = result_output


        response = HttpResponse(
            file_stream,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        safe_job_name = "".join([c if c.isalnum() else "_" for c in job.name]) if hasattr(job, 'name') else f"Job_{job_id}"
        filename = f"NarrIQ_Results_{safe_job_name}.xlsx"
        
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        print(f"📥 [NarrIQ] Whole JSON converted to DF and sent to Excel builder for Job {job_id}")
        return response

    except AttributeError:
        raise Http404("Analysis results are not available for this job yet.")
    except Exception as e:
        print(f"❌ [DOWNLOAD ERROR] Job {job_id}: {str(e)}")
        return HttpResponse(f"Server Error while generating Excel: {str(e)}", status=500)           