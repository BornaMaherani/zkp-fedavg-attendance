import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server.coordinator import Coordinator

def main():
    print("=== شروع اجرای تست یکپارچه فاز ۲ ===")
    
    # برای جلوگیری از کندی در تست اولیه پیشنهاد شده N روی عدد کوچکتری مثل 10 یا 100 باشد.
    # در تنظیمات (settings.json) تعداد 100 مشخص شده است.
    coordinator = Coordinator()
    print(f"Coordinator: جلسه شماره ۱ با {coordinator.N} دانشجو آماده است.")
    
    # 1. شبیه‌ساز وضعیت‌ها را تولید می‌کند (تسک ۲.۱)
    print("\nCoordinator: آغاز فاز شبیه‌سازی...")
    client_states = coordinator.simulator.generate_client_states()
    
    # 2. سرور بردار تخمینی و چالش را ارسال می‌کند (تسک ۲.۲)
    print("\nCoordinator: جلسه شماره ۱ آغاز شد. تولید چالش امنیتی...")
    ready_packets = coordinator.broadcast_to_clients(session_id="SESSION_001")
    
    print("\n=== پایان فاز ۲ ===")

if __name__ == "__main__":
    main()
