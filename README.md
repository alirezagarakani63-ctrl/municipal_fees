# ابنیار — محاسبه عوارض ساختمانی تهران

برنامه تحت‌وب برای اعمال مصوبه عوارض ساختمانی، ارزش‌افزوده و بهای خدمات حوزه شهرسازی تهران (سال ۱۴۰۵).

## اجرا

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## داده‌ها

| فایل | نقش |
|------|-----|
| `Avarez.pdf` | متن مصوبه و فرمول‌ها |
| `Table27.pdf` | ضرایب C(s) راسته‌های تجاری |
| `ارزش-معاملاتي-...xlsx` | ارزش معاملاتی P(r)/P(m)/P(s) سال ۱۴۰۵ |
| `data/kr_coefficients.json` | ضریب K(r) جدول ۱ |
| `data/cs_table27.json` | ضریب C(s) استخراج‌شده از جدول ۲۷ |
| `data/transaction_values_1405.json` | ارزش‌های معاملاتی |

برای بازسازی JSONها:

```bash
python scripts/extract_data.py
```

## تم

رنگ‌ها از لوگوی ابنیار: سرمه‌ای `#003050` و نارنجی `#F09000`.
