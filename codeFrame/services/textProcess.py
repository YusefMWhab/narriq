# textProcess.py
import re

def normalize_text(text: str) -> str:
    text = text.lower()

    # توحيد الألف
    text = re.sub("[إأآا]", "ا", text)
    
    # حذف الـ التعريف من بداية الكلمات
    text = re.sub(r"\bال", "", text)

    # توحيد الياء
    text = re.sub("[يى]", "ي", text)
    
    # توحيد التاء المربوطة والهاء
    text = re.sub("[ةه]", "ه", text)

    # إزالة التشكيل
    text = re.sub("[ًٌٍَُِّْ]", "", text)

    # إزالة أي رموز
    text = re.sub(r"[^\w\s]", " ", text)

    # مسافات زيادة
    text = re.sub(r"\s+", " ", text).strip()
    
    # إزالة التطويل (مثل كلمة صببببباح)
    text = re.sub(r"ـ+", "", text)

    return text
