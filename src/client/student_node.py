import torch
from src.client.local_ml import LocalML
from src.client.state_manager import StateManager
from src.client.signer import Signer

class StudentNode:
    def __init__(self, student_id, private_key):
        self.student_id = student_id
        self.private_key = private_key
        # ۱. کلید خصوصی فقط به شیء دانشجو (کلاینت) پاس داده شده است
        self.signer = Signer(private_key=self.private_key)
        self.local_ml = LocalML()
        
    def process_and_proof(self, s_real, s_hat, alphas, eps_max):
        manager = StateManager(alphas=alphas, eps_max=eps_max, zkp_dir="zkp")
        
        # توجه: بخش _scale_for_zkp باید توسط نفر دوم به کلاس StateManager اضافه شود (تسک ۱.۲)
        # در صورت پیاده‌سازی آن توسط نفر دوم، اینجا فراخوانی می‌شود
        
        is_valid = manager.process_state_and_prepare_proof(s_real, s_hat)
        if is_valid:
            manager.generate_proof()
        return is_valid
        
    def sign_challenge(self, challenge_str):
        signature_data = self.signer.sign_challenge(challenge_str)
        return signature_data
        
    def train_local_model(self, features, labels, global_weights=None):
        if global_weights:
            self.local_ml.model.load_state_dict(global_weights)
        weight_diffs = self.local_ml.train_and_get_diff(features, labels)
        return weight_diffs

    def receive_broadcast(self, payload):
        """
        تسک ۲.۳، ۲.۴ و ۲.۵ (وظایف نفر دوم)
        این متد توسط دانشجو برای دریافت اطلاعات Coordinator اجرا می‌شود.
        """
        s_hat = payload["s_hat"]
        challenge = payload["challenge"]
        global_weights = payload["global_weights"]
        
        # ۱. دسترسی به S_real که توسط Simulator تزریق شده
        s_real = getattr(self, 's_real', [90, 90, 90])
        
        # مقادیر فرضی برای آستانه و ضرایب (باید از StateManager یا کانفیگ خوانده شود)
        alphas = [0.4, 0.3, 0.3]
        eps_max = 0.3
        
        # محاسبه ساده خطا برای تست (چون StateManager باید توسط نفر دوم تکمیل شود)
        error = sum([alphas[i] * ((s_real[i] - s_hat[i])/100.0)**2 for i in range(3)])
        is_ready = error < eps_max
        
        public_addr = getattr(self, 'public_address', self.student_id)
        short_addr = public_addr[:8] if isinstance(public_addr, str) else str(public_addr)[:8]
        
        is_cheater = getattr(self, 'is_cheater', False)
        
        if is_ready or is_cheater:
            if is_cheater:
                print(f"Client (دانشجو {short_addr}...): در حال تقلب! ارسال بسته آمادگی نامعتبر بدون ZKP واقعی.")
                # تولید وزن‌های مخرب برای تقلب
                delta_W = {}
                for key in global_weights.keys():
                    delta_W[key] = (torch.rand_like(global_weights[key]) * 10 - 5).tolist() # نویز بالا
                zkp_proof = None # بدون اثبات معتبر
            else:
                print(f"Client (دانشجو {short_addr}...): خطا مجاز است. در حال ساخت ZKP و استخراج \u0394 W ... بسته آمادگی ارسال شد.")
                # آموزش فدرالی (به صورت موقت با داده تستی)
                features = torch.tensor([[0.5, 0.2, 0.1]], dtype=torch.float32)
                labels = torch.tensor([[1.0]], dtype=torch.float32)
                delta_W = self.train_local_model(features, labels, global_weights)
                zkp_proof = {"dummy": "proof_json"} # نیازمند ماژول ZKP نفر دوم
                
            signature = self.sign_challenge(challenge)
            
            ready_packet = {
                "student_address": public_addr,
                "is_ready": True,
                "signature": signature,
                "zkp_proof": zkp_proof,
                "zkp_public": {"dummy": "public_json"},
                "weight_diffs": delta_W
            }
            return ready_packet
        else:
            print(f"Client (دانشجو {short_addr}...): خطا غیرمجاز است. بسته آمادگی تولید نخواهد شد.")
            return {
                "student_address": public_addr,
                "is_ready": False
            }

def run_test():
    print("آغاز ارزیابی مستقل گره دانشجو...")
    
    dummy_private_key = "0x" + "1" * 64
    student = StudentNode(student_id="test_01", private_key=dummy_private_key)
    
    # ۱. استخراج وضعیت و تولید مدارک دانایی صفر
    s_real = [85, 90, 95]
    s_hat = [80, 85, 90]
    is_valid = student.process_and_proof(s_real, s_hat, alphas=[1, 1, 1], eps_max=1000)
        
    # ۲. پردازش چالش امنیتی و تولید امضای دیجیتال
    signature_data = student.sign_challenge("چالش_امنیتی_آزمایشی")
    print(f"امضای دیجیتال تولید شد: {signature_data['signature'][:30]}...")
    
    # ۳. یادگیری محلی و استخراج تفاضل وزن‌ها
    features = torch.tensor([[0.5, 0.2, 0.1], [0.9, 0.8, 0.7]], dtype=torch.float32)
    labels = torch.tensor([[0.0], [1.0]], dtype=torch.float32)
    
    weight_diffs = student.train_local_model(features, labels)
    print("تفاضل وزن‌ها با موفقیت استخراج و آماده ارسال گردید.")

if __name__ == "__main__":
    run_test()