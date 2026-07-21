import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server.coordinator import Coordinator

def main():
    print("=== شروع اجرای تست یکپارچه فاز ۳ ===")
    
    coordinator = Coordinator()
    print(f"Coordinator: جلسه شماره ۱ با {coordinator.N} دانشجو آماده است.")
    
    # شبیه‌ساز وضعیت‌ها را تولید می‌کند
    client_states = coordinator.simulator.generate_client_states()
    
    # سرور بردار تخمینی و چالش را ارسال می‌کند (فاز ۲)
    s_hat_base = [90.0, 90.0, 90.0]
    ready_packets = coordinator.broadcast_to_clients(session_id="SESSION_001")
    
    # ---------------------------------------------------------
    # فاز ۳
    # ---------------------------------------------------------
    
    # تسک ۳.۳: اعتبارسنجی
    valid_candidates = coordinator.filter_valid_candidates(ready_packets)
    
    # تسک ۳.۴: انتخاب
    selected_candidates = coordinator.select_candidates(valid_candidates, s_hat_base)
    
    # تسک ۳.۵: یادگیری فدرالی
    coordinator.federated_averaging(selected_candidates)
    
    # تسک ۳.۶: به‌روزرسانی بردار تخمینی
    coordinator.update_estimated_state(selected_candidates, coordinator.students, s_hat_base)
    
    print("\n=== پایان فاز ۳ ===")

if __name__ == "__main__":
    main()
