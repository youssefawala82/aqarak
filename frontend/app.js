/**
 * Aqarak - ملف الجافاسكريبت الرئيسي
 * أوامر التشغيل:
 * python -m uvicorn backend.main:app --reload
 * python backend/train_ai.py
 * python -m backend.seed
 */
const API_URL = 'https://aqarak-backend-vehj.onrender.com';
// ====================================================================
// دوال مساعدة (Helper Functions)
// ====================================================================
/**
 * دالة جلب هيدر المصادقة (التوكن)
 * تُستخدم في كل الطلبات التي تحتاج تسجيل دخول
 */
function getAuthHeaders() {
    const token = localStorage.getItem('token');
    if (!token) return {};
    return { 'Authorization': `Bearer ${token}` };
}
// ====================================================================
// 1. منطق تسجيل الدخول (Login Logic)
// ====================================================================

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = loginForm.querySelector('button');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Authenticating...';
        submitBtn.disabled = true;

        // إعداد بيانات الفورم (الباك إند يستقبل username و password كـ FormData)
        const formData = new FormData();
        formData.append('username', document.getElementById('email').value);
        formData.append('password', document.getElementById('password').value);

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // حفظ التوكن ورتبة المستخدم في المتصفح
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('user_role', data.role || 'user');
                window.location.href = "index.html";
            } else {
                alert("Login Error: " + (data.detail || "Invalid credentials"));
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        } catch (error) {
            alert("Backend server is unreachable.");
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}
// ====================================================================
// 2. اقتراح السعر بالذكاء الاصطناعي (AI Price Prediction)
// ====================================================================

const suggestPriceBtn = document.getElementById('suggestPriceBtn');
if (suggestPriceBtn) {
    suggestPriceBtn.addEventListener('click', async () => {
        const area = document.getElementById('area').value;
        const city = document.getElementById('city').value;

        // التحقق من إدخال المساحة والمدينة قبل الإرسال
        if (!area || !city) {
            alert("Please enter area and city first for AI valuation.");
            return;
        }

        suggestPriceBtn.innerText = "Analyzing Market...";

        // إرسال البيانات كـ FormData لأن الباك إند يستقبل Form()
        const formData = new FormData();
        formData.append('area', parseFloat(area));
        formData.append('city', city);

        try {
            const response = await fetch(`${API_URL}/ai/predict-price`, {
                method: 'POST',
                headers: getAuthHeaders(),
                body: formData
            });
            const data = await response.json();

            // وضع السعر المقترح في خانة السعر مع تمييزها بلون أزرق
            const priceInput = document.getElementById('price');
            priceInput.value = data.suggested_price;
            priceInput.style.border = "2px solid #0061FF";
            alert(`AI Suggestion: $${data.suggested_price} (Based on current market data)`);
        } catch (e) {
            console.error("AI Service Error:", e);
            alert("AI service is currently unavailable.");
        } finally {
            suggestPriceBtn.innerText = "Suggest Price (AI)";
        }
    });
}
// ====================================================================
// 3. إضافة عقار جديد (Add Property Logic)
// ====================================================================

// ====================================================================
// 4. رفع صورة العقار (Image Upload Helper)
// ====================================================================

async function uploadImage(propertyId, file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        // ملاحظة: الرابط ينتهي بـ / ليتطابق مع تعريف المسار في الباك إند
        await fetch(`${API_URL}/properties/${propertyId}/upload-image/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });
    } catch (e) {
        console.error("Media upload failed:", e);
    }
}
// ====================================================================
// 5. معاينة الصورة قبل الرفع (Image Preview)
// ====================================================================

const imageInput = document.getElementById('main_image');
const previewImg = document.getElementById('preview');
if (imageInput && previewImg) {
    imageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                // عرض الصورة المختارة كمعاينة
                previewImg.src = event.target.result;
                previewImg.style.display = 'block';

                // إخفاء النص التوضيحي إذا كان موجوداً
                const placeholder = document.querySelector('.upload-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            };
            reader.readAsDataURL(file);
        }
    });
}


// ====================================================================
// 6. حماية الصفحات الخاصة (Session Guard)
// توجيه المستخدم لصفحة الدخول إذا حاول الوصول بدون تسجيل
// ====================================================================

function checkSession() {
    const protectedPages = [
        'add_property.html',
        'dashboard.html',
        'booking.html',
        'admin_dashboard.html',
        'profile.html',
        'favorites.html',
        'edit_property.html'
    ];
    const currentPage = window.location.pathname.split("/").pop();

    if (protectedPages.includes(currentPage) && !localStorage.getItem('token')) {
        window.location.href = "login.html";
    }
}
checkSession();