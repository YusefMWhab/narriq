import json
import os
import pandas as pd
import numpy as np
import ast

from sklearn.cluster import AgglomerativeClustering
from django.db.models import F
from django.db import transaction
from django.conf import settings

from accounts.utils import send_user_notification

from codeFrame.loaders.loader import get_map_prompt, get_split_prompt
from codeFrame.services.ai_service import API_Service_extract_codes, API_Service_mapping, API_Service_Embedding
from codeFrame.services.textProcess import normalize_text
from codeFrame.models import CodeFrame_AnalysisJob, CodeFrame_AnalysisResult, CodeFrame_CompanyUsageQuota

# Main Service Function to handle the entire workflow of CodeFrame
def CodeFrameService(temp_path, method, projectLanguage, projectResultLanguage, projectDesc, userMapping, job_id):

    print(f"Starting CodeFrameService for Job ID: {job_id}")
    # Prepare job data
    file_path = os.path.join(
    settings.MEDIA_ROOT,temp_path
)

    df = pd.read_excel(file_path)
    # Add an ID column to keep track of original row numbers after processing
    df['id'] = range(1, len(df) + 1)

    columns = ['id'] + [col["column"] for col in userMapping]

    data_df = df[columns]

    job_data = {
        "data": data_df,
        "method": method,
        "projectLanguage": projectLanguage,
        "projectResultLanguage": projectResultLanguage,
        "projectDescription": projectDesc,
        "userMapping": userMapping,
    }

    meta_data = {
        "total_rows": 0,
        "processed_responses": 0,
        "extracted_codes_count": 0
    }

    

    selected_columns = [item["column"] for item in job_data["userMapping"]]        
    processed_responses = int(job_data["data"][selected_columns].count().sum())

    # 1. Call the function to prepare data 
    task_list, language, result_language, Split_prompt, Map_Prompt = CodeFrame_PrepareData(job_data)

    # 2. Call the function to manage data and get the final output
    final_output, msg = CodeFrame_DataManagement(task_list, language, result_language, Split_prompt, Map_Prompt)


    meta_data["total_rows"] = len(job_data["data"])
    meta_data["processed_responses"] = processed_responses
    meta_data["extracted_codes_count"] = len(final_output["CodeBook"])
    print(f"Meta Data for Job ID {job_id}: {meta_data}")


    # Update the database with the results and mark the job as completed
    status = CodeFrame_UpdateDatabaseWithResults(job_id, final_output, meta_data)
    send_email_notification(job_id, status)

# This Function is responsible for preparing the data of all selected columns
def CodeFrame_PrepareData(job_data):
    # 1. Get Data from UI
    data_language = job_data["projectLanguage"]
    result_language = job_data["projectResultLanguage"]
    project_description = job_data["projectDescription"]
    
    # 2. Get Prompt for this Category
    Split_prompt = get_split_prompt()
    Map_Prompt = get_map_prompt()
    
    # 3. Extract IDs
    ids = job_data["data"]["id"].tolist()

    # 4. Create a list to manage all needed data
    prepared_tasks = []

    # 5. Get selected Column and its arabic header
    for item in job_data["userMapping"]:
        column_name = item['column']
        column_header = item['description']
        
        # Get the Data from the Original DF
        column_data = job_data["data"][column_name].fillna("").astype(str).tolist()
        
        # Create a dict. to store all needed details
        task_info = {
            "id": ids,
            "column_name": column_name,
            "column_description": column_header,
            "data": column_data,
            "project_context": project_description,
        }
        
        prepared_tasks.append(task_info)
    
    return prepared_tasks, data_language, result_language, Split_prompt, Map_Prompt

# This function extract each cell in each column and send it to API_Service_extract_codes(text, project_description, question_description, prompt_template)
def CodeFrame_DataManagement(tasks_list, data_language, result_language, Split_prompt, Map_Prompt):
    
    SplitResults_All = []
    sheet_data = {}
    row_mapping = []
    
    BATCH_SIZE = 25
    for task in tasks_list:
        
        df = pd.DataFrame()

        col_name = task["column_name"]
        data_to_process = task["data"]
        project_description = task["project_context"]
        question_description = task["column_description"]
        
        df["id"] = task["id"]
        df["Text"] = data_to_process 


        Split_results = [None] * len(data_to_process)
        texts_needing_api = []

        for i, text in enumerate(data_to_process):                
            clean_text = str(text) if text is not None else ""    
            normalized_text = normalize_text(clean_text)
            
            if normalized_text == "":
                Split_results[i] = []
            
            elif normalized_text in ["لا يوجد", "لا بوجد", "لايوجد", "لابوجد", "لا", "لا شي",
                                    "لا شئ", "لا شى", "لاشي", "لاشئ", "لاشى", "مفيش", "مافيش",
                                    "No thing", "nothing", "no thing", "no", "not", "NOTHING", "NO THING"]:
                if result_language != "English":
                    Split_results[i] = ["لا يوجد"]
                else:
                    Split_results[i] = ["Nothing"]
            
            else:
                texts_needing_api.append((i, clean_text))

        if texts_needing_api:
            for batch_start in range(0, len(texts_needing_api), BATCH_SIZE):
                
                batch = texts_needing_api[batch_start : batch_start + BATCH_SIZE]
                batch_indices = [item[0] for item in batch]
                batch_texts   = [item[1] for item in batch]

                batch_results = API_Service_extract_codes(
                    batch_texts,
                    project_description,
                    question_description,
                    Split_prompt,
                    data_language,
                    result_language
                )
                
                for original_idx, result in zip(batch_indices, batch_results):
                    Split_results[original_idx] = result

        Split_results = [r if r is not None else [] for r in Split_results]

        df["Split Results"] = [", ".join(map(str, x)) for x in Split_results]       
        
        sheet_data[col_name] = df
        
        for row_idx, row in enumerate(Split_results):
            SplitResults_All.append(row)
            row_mapping.append((col_name, row_idx))
        
            
    simplified_tags, tags_to_send_llm = CodeFrame_SimplifyTagsForLLM(SplitResults_All) # using cross and bi encoder

    
    AI_map_results = API_Service_mapping(tags_to_send_llm, project_description, question_description, Map_Prompt, data_language, result_language)
    
    
    final_text, final_ids, codebook = CodeFrame_FinalizeMappingAndCodesList(simplified_tags, AI_map_results)

    for i, (sheet_name, row_idx) in enumerate(row_mapping):


    # كل عمود ممكن يكون قائمة
        sheet_data[sheet_name].loc[row_idx, "CrossEncoder"] = ", ".join(simplified_tags[i]) if simplified_tags[i] else ""
        sheet_data[sheet_name].loc[row_idx, "Final Text"] = ", ".join(final_text[i]) if final_text[i] else ""
        sheet_data[sheet_name].loc[row_idx, "Final IDs"] = final_ids[i]


    final_output = {
                "sheet_Data": sheet_data,
                "CodeBook": codebook
            }
    
        
    return final_output, "Process is Done!"

# This function is responsible for simplifying the tags using clustering and then using the mapping results from the LLM to finalize the mapping without needing to send all 7000 rows to the LLM
def CodeFrame_SimplifyTagsForLLM (ai_output_list, bi_threshold=0.80, cross_threshold=0.97):
    
    all_tags = []
    
    # 1. تجميع كل الـ Tags من الـ 7000 سطر
    for row in ai_output_list:
        if not row: continue
        # التأكد من تحويل النص لـ List لو محتاج
        if isinstance(row, str) and row.strip().startswith('['):
            try: row = ast.literal_eval(row)
            except: pass
        
        current_row_tags = row if isinstance(row, list) else [row]
        for t in current_row_tags:
            tag_str = str(t).strip()
            if tag_str and tag_str.lower() != "nan":
                all_tags.append(tag_str)

    # 2. Extract Unique Tags
    unique_tags = list(set(all_tags))
    if not unique_tags: return [], []

    # 3. Clustering
    embeddings = API_Service_Embedding(unique_tags)

    cluster_model = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=1 - bi_threshold, 
        metric='cosine', 
        linkage='average'
    )
    cluster_labels = cluster_model.fit_predict(embeddings)

    # 4. بناء الـ Replacement Map بدون Cross-Encoder (باستخدام المصفوفات)
    replacement_map = {}
    unique_labels = np.unique(cluster_labels)

    for label in unique_labels:
        # هنجيب كل الـ indices اللي تبع الـ cluster ده
        indices = np.where(cluster_labels == label)[0]
        
        # الـ Leader هو أول tag في الكلاستر (أو ممكن تختار الأقصر طولاً)
        leader_tag = unique_tags[indices[0]]
        
        for idx in indices:
            tag = unique_tags[idx]
            replacement_map[tag] = leader_tag

    # 5. الـ Replacement السريع
    simplified_column = []
    for row in ai_output_list:
        if not row:
            simplified_column.append([])
            continue
        # استخدام الـ map مباشرة (سرعة O(1))
        new_row = list(set([replacement_map.get(str(tag).strip(), str(tag).strip()) for tag in row]))
        simplified_column.append(new_row)

    final_unique_for_llm = sorted(list(set(replacement_map.values())))
    return simplified_column, final_unique_for_llm

# Mapping and Generate IDs
def CodeFrame_FinalizeMappingAndCodesList(simplified_tags_list, final_master_dict):
    # 1. بناء خريطة البحث (القديم -> الجديد)
    apply_map = {}
    for standard_name, old_list in final_master_dict.items():
        for old_val in old_list:
            apply_map[str(old_val).strip()] = standard_name

    # 2. إنشاء الـ Codebook مع استبعاد "لا يوجد" من الترتيب التلقائي
    # بنشيلها من القائمة عشان نضمن إن المسلسل مبيحسبهاش
    unique_standards = sorted([name for name in final_master_dict.keys() if name != "لا يوجد"])
    
    standard_to_id = {}
    current_id = 1
    for name in unique_standards:
        if current_id == 99: 
            current_id = 100
        standard_to_id[name] = current_id
        current_id += 1

    # حجز رقم 99 حصرياً لـ "لا يوجد"
    standard_to_id["لا يوجد"] = 99
    
    final_text_out = []
    final_ids_out = []

    # 3. المرور على القائمة ومعالجتها سطر بسطر
    for tags in simplified_tags_list:
        # تحويل كل عنصر لنص بدون مسافات
        cleaned_tags = [str(t).strip() for t in tags if str(t).strip()]
        
        # لو فيه "لا يوجد" يرجع ["لا يوجد"] مع الكود 99
        if "لا يوجد" in cleaned_tags:
            final_text_out.append(["لا يوجد"])
            final_ids_out.append("99")
            continue
        
        # لو النص كله فاضي، نسيبه فاضي
        if not cleaned_tags:
            final_text_out.append([])
            final_ids_out.append("")  # ممكن تسيبها فاضية كده أو Null حسب احتياجك
            continue
            
         # تحويل النصوص للأسماء الموحدة
        mapped_text = list(set([apply_map.get(t, t) for t in cleaned_tags]))

        # IDs رقمية مرتبة
        mapped_ids_list = sorted([standard_to_id[t] for t in mapped_text if t in standard_to_id])
        
        if not mapped_ids_list:
            final_text_out.append([])
            final_ids_out.append("")
        else:
            mapped_ids_str = ", ".join(map(str, mapped_ids_list))
            final_text_out.append(mapped_text)
            final_ids_out.append(mapped_ids_str)

    # 4. بناء قاموس الكود بوك النهائي (ID: Text)
    codebook_dict = {v: k for k, v in standard_to_id.items()}

    return final_text_out, final_ids_out, codebook_dict

# Mark the job as completed and save the final output in the result model
def CodeFrame_UpdateDatabaseWithResults(job_id, final_output, meta_data):
    try:
        print(f"Updating database for Job ID: {job_id} with results.")
        final_output_serializable = json.loads(json.dumps(final_output, default=json_serializable_converter))
        
        with transaction.atomic():
            job = CodeFrame_AnalysisJob.objects.select_for_update().get(id=job_id)
            job.status = 'completed'
            job.save()
            
            CodeFrame_AnalysisResult.objects.create(
                job=job,
                results=final_output_serializable,
                total_records=meta_data.get("total_rows", 0),
                processed_responses=meta_data.get("processed_responses", 0),
                extracted_codes_count=meta_data.get("extracted_codes_count", 0)
            )
            
            quota = CodeFrame_CompanyUsageQuota.objects.select_for_update().get(company=job.company)
            quota.used_responses = F('used_responses') + meta_data.get("processed_responses", 0)
            quota.save()
            
        print(f"Job {job_id} completed, counters updated, and results saved successfully.")
        return True
        
    except CodeFrame_AnalysisJob.DoesNotExist:
        print(f"Job with ID {job_id} not found.")
        return False
    except Exception as e:
        print(f"Failed to update status and save results: {str(e)}")
        raise e
    
# Helper function to convert non-serializable objects (like DataFrames) to a JSON-serializable format
def json_serializable_converter(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

# Function to send email notification to the user about the job status
def send_email_notification(job_id, IsSuccess):
    try:
        # Get the job and user email
        job = CodeFrame_AnalysisJob.objects.get(id=job_id)
        user_email = job.user.email

        if IsSuccess:
            subject = 'NarrIQ: Your analysis is ready!'
            message = (f'Hello {job.user.username},\n\n'
                       f'Great news! The analysis for your file uploaded at "{job.created_at}" '
                       'has been completed successfully. You can now view the results on your dashboard.')
        else:
            subject = 'NarrIQ: Analysis encountered an issue'
            message = (f'Hello {job.user.username},\n\n'
                       'We apologize, but we were unable to complete the analysis for your file. '
                       'Please check your file format or try uploading again. '
                       'If the problem persists, please contact our support team.')
            
        success = send_user_notification(subject, message, user_email)
        
        if success:
            print(f"Notification email sent to {user_email} (Job: {job_id})")
        else:
            print(f"Failed to send notification email to {user_email}")
            
        return success

    except CodeFrame_AnalysisJob.DoesNotExist:
        print(f"Job with ID {job_id} not found.")
        return False
    except Exception as e:
        print(f"An error occurred in send_email_notification: {str(e)}")
        return False
