import os
from openai import OpenAI
from google import genai
from google.genai import types
import json
import re
import numpy as np
import time

openai_api_key = os.getenv("API_KEY_OpenAI")
gemini_api_key = os.getenv("API_KEY_Gemini")

openai_client = OpenAI(api_key=openai_api_key)
gemini_client = genai.Client(api_key=gemini_api_key)



""" # Function to Split the Text...
def API_Service_extract_codes(text, project_description, question_description, prompt_template):

    system_prompt = prompt_template.format(
        project_description = project_description,
        question_description = question_description
    )
    
    
    user_prompt = f"النص المراد معالجته\n{text}"
    
    response = openai_client.chat.completions.create(
    model = "gpt-4.1-mini-2025-04-14",
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": user_prompt}],
    temperature=0.1,
    response_format={"type": "json_object"}
    )
    
    output_text = response.choices[0].message.content
    clean_json = re.sub(r'```json\s*|```', '', output_text).strip()
    codes = json.loads(clean_json)["result"] 


    return codes
"""
# Function to optimize the code...
def API_Service_mapping(attributes_list, project_description, question_description, prompt_template, data_language, result_language, batch_size = 100, passes = 4):
    
    print(f"Starting mapping")
    if result_language == "Data Language":
        actual_output_lang = data_language 
    else:
        actual_output_lang = result_language
    threshold = 0.01
    current_list = sorted([str(attr) for attr in attributes_list])
    mapping_history = {}

    mapping_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "group_name": {"type": "STRING"},
            "items": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        },
        "required": ["group_name", "items"]
        }
    }
     
    
    # Dynamic Batch size
    for p in range(passes):
         
        previous_count = len(current_list)
        batch_master_dict = {}
        current_list = sorted(set(current_list))
        print(f"Pass {p+1}: Processing {len(current_list)} unique codes...")

        for i in range(0, len(current_list), batch_size):
            
            batch = current_list[i : i + batch_size]
            
            system_prompt = prompt_template["system"].format(
                project_description = project_description,
                data_language = data_language,
                result_language = actual_output_lang
            )
            
            user_prompt = prompt_template["user"].format(
                question_description = question_description,
                phrases_batch = batch,
                result_language = actual_output_lang,
            )
            
            try:
                response = gemini_client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.0, 
                        response_mime_type="application/json",
                        response_schema=mapping_schema 
                    )
                )
                raw_data = json.loads(response.text)
                print(raw_data)
                
                batch_dict = {obj["group_name"]: obj["items"] for obj in raw_data}
                
                # ====================================================================
                returned_originals = []
                for vals in batch_dict.values():
                    returned_originals.extend(vals)

                returned_count = len(set(returned_originals))
                input_count = len(set(batch))

                print(f"Input batch size: {input_count} | Returned originals: {returned_count}")

                input_batch_cleaned = [str(b).strip() for b in batch]
                missing_phrases = set(input_batch_cleaned) - set(returned_originals)
                
                if missing_phrases:
                    print(f"Warning: Found {len(missing_phrases)} missing phrases. Recovering...")
                    for phrase in missing_phrases:
                        if phrase not in batch_dict:
                            batch_dict[phrase] = [phrase]
                        else:
                            batch_dict[phrase].append(phrase)
                # ====================================================================

                
                # Merge batch results
                for new_key, old_vals in batch_dict.items():
                    if new_key in batch_master_dict:
                        batch_master_dict[new_key] = list(set(batch_master_dict[new_key] + old_vals))
                    else:
                        batch_master_dict[new_key] = list(set(old_vals))
                        
            except Exception as e:
                print(f"Error in Pass : {p+1}: {e}")
                continue
        
        # Hierarchical merging with previous pass    
        if not mapping_history:
            # first pass: initialize mapping_history
            mapping_history = {k: v for k, v in batch_master_dict.items()}
        else:
            # second+ pass: resolve merges
            new_history = {}
            for final_key, intermediate_keys in batch_master_dict.items():
                all_originals = []
                for inter_key in intermediate_keys:
                    # Get all originals mapped to this intermediate key
                    originals = mapping_history.get(inter_key, [inter_key])
                    all_originals.extend(originals)
                new_history[final_key] = list(set(all_originals))
            mapping_history = new_history
        
        # Update current_list for next pass
        current_list = sorted(list(mapping_history.keys()))
        current_count = len(current_list)
        
        reduction_rate = (previous_count - current_count) / previous_count if previous_count > 0 else 0
        print(f"Pass {p+1} finished. Remaining codes: {current_count} (Reduction: {reduction_rate:.2%})")

        if p > 0: 
            if current_count >= previous_count:
                print("Stopping: No further merging possible.")
                break
            if reduction_rate < threshold:
                print(f"Stopping: Improvement rate ({reduction_rate:.2%}) is below threshold ({threshold:.2%}).")
                break
                
    print(f"Mapping completed. Final unique codes: {len(mapping_history)}")
    return mapping_history
                 
# ===============================================================================================================
# Embedding function...
def API_Service_Embedding(tag_list):
    BATCH_SIZE = 1000 
    all_embeddings = []

    for i in range(0, len(tag_list), BATCH_SIZE):
        batch = tag_list[i:i + BATCH_SIZE]
        
        response = openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=batch
        )
        
        batch_embeddings = [d.embedding for d in response.data]
        all_embeddings.extend(batch_embeddings)

    return np.array(all_embeddings)

# Gemini version
# 1. Extract Attributes from OE Data
def API_Service_extract_codes(batch_texts, project_description, question_description, 
                               Split_prompt, data_language, result_language):

    numbered_texts = "\n".join([f"[{i+1}] {text}" for i, text in enumerate(batch_texts)])
    if result_language == "Data Language":
        actual_output_lang = data_language 
    else:
        actual_output_lang = result_language
    
    system_prompt = Split_prompt["system"].format(
        project_description  = project_description,
        question_description = question_description,
        data_language        = data_language,
        result_language      = actual_output_lang
    )
    print(system_prompt)

    user_prompt = Split_prompt["user"].format(
        question_description = question_description,
        numbered_texts       = numbered_texts,
        batch_size           = len(batch_texts)
    )

    response_schema = {
        "type": "ARRAY",
        "items": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        }
    }

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction = system_prompt,
                temperature        = 0.0,
                response_mime_type = "application/json",
                response_schema    = response_schema
            )
        )

        results = json.loads(response.text)

        results = [r if isinstance(r, list) else [str(r)] for r in results]

        return results  

    except Exception as e:
        print(f"[Split] Gemini API Error: {str(e)}")
        return [[] for _ in batch_texts]  
    

