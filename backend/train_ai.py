import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib # لحفظ النموذج

# 1. تجهيز بيانات وهمية (بإمكانك استبدالها بملف CSV لاحقاً)
data = {
    'area': [50, 80, 100, 120, 150, 200, 250, 300],
    'city_code': [1, 2, 1, 2, 1, 2, 1, 2], # 1 لبيروت، 2 لطرابلس مثلاً
    'price': [75000, 64000, 150000, 96000, 225000, 160000, 375000, 240000]
}

df = pd.DataFrame(data)

# 2. تحديد المدخلات (X) والهدف (y)
X = df[['area', 'city_code']]
y = df['price']

# 3. تدريب النموذج
model = LinearRegression()
model.fit(X, y)

# 4. حفظ النموذج في ملف
joblib.dump(model, 'property_model.pkl')
print("✅ AI Model Trained and Saved as property_model.pkl")