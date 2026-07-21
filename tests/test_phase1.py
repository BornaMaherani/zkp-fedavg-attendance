import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import torch

from src.server.coordinator import Coordinator

def main():
    print("شروع اجرای سناریوی تست یکپارچه فاز ۱ (نقطه ادغام)...")
    
    # 1. & 2. Coordinator تنظیمات را می‌خواند و N دانشجو با کلیدهای اختصاصی ایجاد می‌کند
    coordinator = Coordinator()
    print(f"{coordinator.N} دانشجو با زوج کلیدهای اختصاصی ایجاد شدند.")
    
    # 3. هماهنگ‌کننده وزن‌های اولیه مدل جهانی را دریافت می‌کند
    global_weights = coordinator.global_model.get_global_weights()
    print("وزن‌های اولیه مدل جهانی استخراج شد.")
    
    # انتخاب یک دانشجو به صورت آزمایشی
    test_student = coordinator.students[0]
    
    # انتقال (آموزش) وزن‌ها به دانشجو به عنوان نمونه
    features = torch.tensor([[0.5, 0.2, 0.1]], dtype=torch.float32)
    labels = torch.tensor([[0.0]], dtype=torch.float32)
    weight_diffs = test_student.train_local_model(features, labels, global_weights=global_weights)
    print("وزن‌های جهانی به دانشجو پاس داده شد و آموزش محلی (تست) انجام گرفت.")
    
    # 4. دانشجو مقادیر تصادفی برای وضعیت در نظر می‌گیرد
    s_real = [85, 90, 95]
    s_hat = [80, 85, 90]
    
    alphas = [
        coordinator.settings.get("alpha1", 0.4),
        coordinator.settings.get("alpha2", 0.3),
        coordinator.settings.get("alpha3", 0.3)
    ]
    eps_max = coordinator.settings.get("epsilon_max", 0.3)
    
    # توجه: تسک ۱.۲ (ممیز ثابت و مقیاس‌دهی _scale_for_zkp) باید توسط نفر دوم تکمیل شده باشد
    # در اینجا پروسه تولید اثبات را فراخوانی می‌کنیم
    print("\nآزمایش تولید اثبات ZKP (دانشجو ۰):")
    try:
        is_valid = test_student.process_and_proof(s_real, s_hat, alphas, eps_max)
        if is_valid:
            print("اثبات ZKP با موفقیت تولید شد.")
        else:
            print("خطای پیش‌بینی بیش از حد مجاز است.")
    except Exception as e:
        print(f"خطا در تولید اثبات ZKP: {e}")

if __name__ == "__main__":
    main()
