import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.server.coordinator import Coordinator

def main():
    print("=== شروع اجرای تست یکپارچه فاز ۴ ===")
    
    coordinator = Coordinator()
    print(f"Coordinator: جلسه شماره ۱ با {coordinator.N} دانشجو آماده است.")
    
    # اجرای سریع فازهای قبلی
    client_states = coordinator.simulator.generate_client_states()
    s_hat_base = [90.0, 90.0, 90.0]
    ready_packets = coordinator.broadcast_to_clients(session_id="SESSION_001")
    
    valid_candidates = coordinator.filter_valid_candidates(ready_packets)
    selected_candidates = coordinator.select_candidates(valid_candidates, s_hat_base)
    coordinator.federated_averaging(selected_candidates)
    coordinator.update_estimated_state(selected_candidates, coordinator.students, s_hat_base)
    
    # ---------------------------------------------------------
    # فاز ۴
    # ---------------------------------------------------------
    
    # تسک ۴.۶: بستن حلقه (شامل تسک‌های ۴.۴ و ۴.۵ و فراخوانی ماژول‌های فاز ۴)
    coordinator.end_session(
        session_id="SESSION_001", 
        selected_candidates=selected_candidates, 
        total_proofs=len(ready_packets), 
        valid_proofs=len(valid_candidates)
    )

if __name__ == "__main__":
    main()
