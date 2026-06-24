import io
import pandas as pd
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Export Code Frame reults
def CodeFrame_ExportData(entries_list):
    output = io.BytesIO()
    
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, rows_data in entries_list["sheet_Data"].items():
                safe_name = "".join([c for c in sheet_name if c.isalnum() or c in ' _-'])[:25]
                
                df_main = pd.DataFrame(rows_data)
                
                for col in ["Split Phrases", "CrossEncoder", "Final Text", "Final IDs"]:
                    if col in df_main.columns:
                        df_main[col] = df_main[col].apply(
                            lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
                        )
                
                df_main.to_excel(writer, sheet_name=f"{safe_name}_Results", index=False)

            codebook_dict = entries_list.get("CodeBook", {})
            df_codebook = pd.DataFrame({
                "ID": list(codebook_dict.keys()),
                "Standard Attribute": list(codebook_dict.values())
            })
            
            df_codebook["ID"] = pd.to_numeric(df_codebook["ID"])
            df_codebook = df_codebook.sort_values(by="ID")

            df_codebook.to_excel(writer, sheet_name="CodeFrame", index=False)
        
        output.seek(0)
        return True, output 
         
    except Exception as e:
        print(f"Export Error: {str(e)}")
        return False, f"Error during save: {e}"