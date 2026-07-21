import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server.coordinator import Coordinator
from src.server.metrics_logger import MetricsLogger
from src.server.global_model import GlobalModel

import matplotlib.pyplot as plt

def run_scenario(scenario_name, M=40, cheat_mode=False, disable_zkp=False, random_mode=False):
    print(f"\n======================================")
    print(f"شروع سناریو: {scenario_name}")
    print(f"======================================")
    
    coordinator = Coordinator()
    # ریست کردن مدل جهانی برای شروع تمیز
    coordinator.global_model = GlobalModel()
    logger = MetricsLogger()
    
    s_hat_base = [90.0, 90.0, 90.0]
    
    for session in range(1, M + 1):
        start_time = time.time()
        session_id = f"{scenario_name}_Session_{session}"
        
        # 1. شبیه‌ساز وضعیت‌ها
        client_states = coordinator.simulator.generate_client_states(cheat_mode=cheat_mode)
        
        # شروع زمان‌گیری دقیق اعتبارسنجی ZKP و ساخت آن در کلاینت (تسک ۵.۱)
        zkp_start_time = time.time()
        
        # 2. برودکست
        ready_packets = coordinator.broadcast_to_clients(session_id=session_id)
        
        # 3. اعتبارسنجی
        valid_candidates, _, zkp_success_rate = coordinator.filter_valid_candidates(
            ready_packets, disable_zkp=disable_zkp
        )
        
        # پایان زمان‌گیری دقیق
        zkp_end_time = time.time()
        execution_time = zkp_end_time - zkp_start_time
        zkp_time = execution_time # برای سازگاری با لاگر
        
        # 4. انتخاب
        selected_candidates = coordinator.select_candidates(
            valid_candidates, s_hat_base, random_mode=random_mode
        )
        
        # 5. یادگیری فدرالی
        coordinator.federated_averaging(selected_candidates)
        
        # 6. به‌روزرسانی بردار تخمینی
        coordinator.update_estimated_state(selected_candidates, coordinator.students, s_hat_base)
        
        # ارزیابی مدل
        mse, accuracy = coordinator.evaluate_global_model()
        
        metrics = {
            "session_id": session_id,
            "scenario": scenario_name,
            "execution_time": execution_time,
            "zkp_verification_time": zkp_time,
            "zkp_success_rate": zkp_success_rate,
            "model_mse": mse,
            "model_accuracy": accuracy
        }
        logger.log_metrics(metrics)
        
        print(f"[{scenario_name}] پایان جلسه {session}/{M} - MSE: {mse:.4f}, Acc: {accuracy:.2f}")

def plot_results():
    import pandas as pd
    
    if not os.path.exists("evaluation_metrics.csv"):
        print("هیچ دیتایی برای رسم نمودار یافت نشد.")
        return
        
    df = pd.read_csv("evaluation_metrics.csv")
    
    plt.figure(figsize=(10, 6))
    for scenario in df['scenario'].unique():
        subset = df[df['scenario'] == scenario]
        plt.plot(range(1, len(subset) + 1), subset['model_accuracy'], label=f"{scenario} Accuracy")
        
    plt.title("مدل هوش مصنوعی در سناریوهای مختلف (Accuracy)")
    plt.xlabel("Sessions")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(True)
    plt.savefig("accuracy_comparison.png")
    print("نمودار Accuracy در accuracy_comparison.png ذخیره شد.")
    
    plt.figure(figsize=(10, 6))
    for scenario in df['scenario'].unique():
        subset = df[df['scenario'] == scenario]
        plt.plot(range(1, len(subset) + 1), subset['model_mse'], label=f"{scenario} MSE")
        
    plt.title("خطای میانگین مربعات مدل (MSE)")
    plt.xlabel("Sessions")
    plt.ylabel("MSE")
    plt.legend()
    plt.grid(True)
    plt.savefig("mse_comparison.png")
    print("نمودار MSE در mse_comparison.png ذخیره شد.")

def main():
    M = 40
    # پاک کردن لاگ قبلی برای اجرای جدید
    if os.path.exists("evaluation_metrics.csv"):
        os.remove("evaluation_metrics.csv")
        
    # سناریوی ۱: حالت پیشنهادی (Greedy + ZKP)
    run_scenario("Proposed", M=M, cheat_mode=False, disable_zkp=False, random_mode=False)
    
    # سناریوی ۲: حالت تصادفی (Random + ZKP)
    run_scenario("Random", M=M, cheat_mode=False, disable_zkp=False, random_mode=True)
    
    # سناریوی ۳: حالت بدون ZKP (با حضور متقلبان)
    run_scenario("No-ZKP", M=M, cheat_mode=True, disable_zkp=True, random_mode=False)
    
    # رسم نمودارها
    print("\nدر حال رسم نمودارها...")
    plot_results()

if __name__ == "__main__":
    main()
