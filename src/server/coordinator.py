import json
import os
import sys
from eth_account import Account

# اطمینان از اینکه مسیر ریشه پروژه در sys.path قرار دارد
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.client.student_node import StudentNode
from src.server.global_model import GlobalModel
from src.simulator.simulator import Simulator
import hashlib
import uuid
import time
import random
import torch
import json
import subprocess
import os
from src.server.ipfs_manager import IPFSManager
from src.server.web3_manager import Web3Manager

class Coordinator:
    def __init__(self, config_path=None):
        if config_path is None:
            # مسیر پیش‌فرض را به صورت مطلق بر اساس مکان فایل coordinator.py می‌سازیم
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'settings.json'))
        
        # خواندن فایل تنظیمات
        with open(config_path, 'r') as f:
            self.settings = json.load(f)
            
        self.N = self.settings.get("N", 100)
        self.K = self.settings.get("K", 20)
        self.eta = self.settings.get("eta", 0.1)
        
        self.students = []
        self.public_keys = {}
        self.session_count = 0
        self.successful_attendance = {}
        
        # تولید کلاینت‌ها و اختصاص زوج کلید
        for i in range(self.N):
            # تولید زوج کلید با استفاده از eth_account
            acct = Account.create()
            private_key = acct.key.hex()
            public_address = acct.address
            
            student_id = f"student_{i}"
            
            # ذخیره آدرس عمومی در یک دیکشنری در Coordinator
            self.public_keys[student_id] = public_address
            self.successful_attendance[public_address] = 0
            
            # ایجاد شیء دانشجو و پاس دادن کلید خصوصی به آن
            student = StudentNode(student_id=student_id, private_key=private_key)
            student.public_address = public_address  # برای دسترسی کلاینت به آدرس خودش
            self.students.append(student)
            
        # پیاده‌سازی مدل جهانی
        self.global_model = GlobalModel()
        
        # پیاده‌سازی شبیه‌ساز (تسک ۲.۱)
        self.simulator = Simulator(self.students)
        
        # ماژول‌های فاز ۴
        self.ipfs_manager = IPFSManager()
        self.web3_manager = Web3Manager()

    def broadcast_to_clients(self, session_id):
        """
        تسک ۲.۲: تولید بردار وضعیت تخمینی و چالش امنیتی
        ارسال بردار تخمینی، چالش امنیتی و مدل جهانی به تمامی کلاینت‌ها
        """
        # تولید S_hat پایه (تخمینی)
        s_hat = [90.0, 90.0, 90.0]
        
        # تولید چالش امنیتی
        nonce = uuid.uuid4().hex
        challenge_str = f"{session_id}_{nonce}"
        challenge = hashlib.sha256(challenge_str.encode()).hexdigest()
        
        # استخراج وزن‌های مدل جهانی
        global_weights = self.global_model.get_global_weights()
        
        payload = {
            "session_id": session_id,
            "s_hat": s_hat,
            "challenge": challenge,
            "global_weights": global_weights
        }
        
        print(f"Coordinator: ارسال بردار تخمینی و چالش به {self.N} کلاینت...")
        
        ready_packets = []
        # ارسال پیام به تمامی دانشجویان
        for student in self.students:
            packet = student.receive_broadcast(payload)
            if packet and packet.get("is_ready"):
                ready_packets.append(packet)
                
        print(f"Coordinator: دریافت بسته‌ها به اتمام رسید. {len(ready_packets)} بسته آمادگی دریافت شد.")
        return ready_packets

    def filter_valid_candidates(self, ready_packets, disable_zkp=False):
        """
        تسک ۳.۳: اعتبارسنجی اثبات‌ها (ZKP Verification)
        در سناریوی تقلب (تسک ۵.۲)، با غیرفعال کردن ZKP متقلبان نیز تایید می‌شوند.
        """
        valid_candidates = []
        validation_times = []
        
        # مسیرهای فایل‌های موقت و اسکریپت
        temp_proof = "temp_proof.json"
        temp_public = "temp_public.json"
        vkey = "zkp/verification_key.json"
        verifier_script = "zkp/verify_proof.js"
        
        # ساخت فایل vkey ساختگی اگر وجود نداشت برای جلوگیری از خطا در تست
        if not os.path.exists(vkey):
            if not os.path.exists("zkp"):
                os.makedirs("zkp")
            with open(vkey, 'w') as f:
                json.dump({"dummy": "vkey"}, f)
                
        for packet in ready_packets:
            start_time = time.time()
            
            if disable_zkp:
                is_valid = True
            else:
                zkp_proof = packet.get("zkp_proof")
                zkp_public = packet.get("zkp_public")
                
                if zkp_proof and zkp_public:
                    with open(temp_proof, 'w') as f:
                        json.dump(zkp_proof, f)
                    with open(temp_public, 'w') as f:
                        json.dump(zkp_public, f)
                        
                    try:
                        # فراخوانی ساب‌پروسس
                        result = subprocess.run(
                            ["node", verifier_script, temp_proof, temp_public, vkey],
                            capture_output=True,
                            text=True
                        )
                        is_valid = (result.returncode == 0)
                    except Exception as e:
                        # در صورت عدم نصب Node.js یا خطای دیگر، به صورت پیش‌فرض رد می‌شود
                        is_valid = False
                else:
                    is_valid = False
            
            end_time = time.time()
            validation_times.append(end_time - start_time)
            
            if is_valid:
                valid_candidates.append(packet)
                
        # پاکسازی فایل‌های موقت
        if os.path.exists(temp_proof): os.remove(temp_proof)
        if os.path.exists(temp_public): os.remove(temp_public)
        
        avg_time = sum(validation_times) / len(validation_times) if validation_times else 0
        total_time = sum(validation_times)
        success_rate = len(valid_candidates) / len(ready_packets) if ready_packets else 0
        
        print(f"Coordinator: شروع اعتبارسنجی ZKP... (میانگین زمان: {avg_time:.4f} ثانیه)... {len(valid_candidates)} اثبات معتبر شناخته شد.")
        return valid_candidates, total_time, success_rate

    def select_candidates(self, valid_candidates, s_hat, random_mode=False):
        """
        تسک ۳.۴: الگوریتم انتخاب حریصانه (Greedy Selection)
        در حالت random_mode (تسک ۵.۳)، انتخاب کاملاً تصادفی انجام می‌شود.
        """
        K = min(self.K, len(valid_candidates))
        
        if random_mode:
            selected = random.sample(valid_candidates, K)
            print(f"Coordinator: حالت انتخاب تصادفی فعال است. K={K} نفر کاملاً تصادفی انتخاب شدند.")
            return selected
            
        beta1 = self.settings.get("beta1", 0.5)
        beta2 = self.settings.get("beta2", 0.5)
        
        scored_candidates = []
        for packet in valid_candidates:
            # احتمال حضور P_i از شبکه عصبی سرور
            with torch.no_grad():
                # تبدیل مقیاس به بین صفر و یک برای شبکه عصبی
                scaled_s_hat = [x/100.0 for x in s_hat]
                input_tensor = torch.tensor([scaled_s_hat], dtype=torch.float32)
                p_attend = self.global_model(input_tensor).item()
            
            # ارزش مشارکت قبلی (تعداد حضورهای موفق به کل جلسات)
            addr = packet["student_address"]
            if self.session_count > 0:
                v_gsj = self.successful_attendance.get(addr, 0) / self.session_count
            else:
                v_gsj = 1.0 # در جلسه اول فرض بر حضور کامل است
            
            u_i = beta1 * p_attend + beta2 * v_gsj
            scored_candidates.append((u_i, packet))
            
        # مرتب‌سازی نزولی
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        K = min(self.K, len(scored_candidates))
        greedy_count = int(0.6 * K)
        random_count = K - greedy_count
        
        selected = [item[1] for item in scored_candidates[:greedy_count]]
        remaining_pool = [item[1] for item in scored_candidates[greedy_count:]]
        
        if random_count > 0 and len(remaining_pool) >= random_count:
            selected += random.sample(remaining_pool, random_count)
        elif random_count > 0:
            selected += remaining_pool
            
        print(f"Coordinator: محاسبه امتیازات و مرتب‌سازی... انتخاب K={len(selected)} نفر ({greedy_count} نفر برتر، {len(selected) - greedy_count} نفر تصادفی).")
        return selected

    def federated_averaging(self, selected_candidates):
        """
        تسک ۳.۵: یادگیری فدرالی (FedAvg)
        """
        if not selected_candidates:
            return
            
        global_state = self.global_model.state_dict()
        num_candidates = len(selected_candidates)
        avg_delta = {}
        
        for packet in selected_candidates:
            delta_w = packet.get("weight_diffs", {})
            for key, val in delta_w.items():
                tensor_val = torch.tensor(val, dtype=torch.float32)
                if key not in avg_delta:
                    avg_delta[key] = tensor_val / num_candidates
                else:
                    avg_delta[key] += tensor_val / num_candidates
                    
        for key in global_state.keys():
            if key in avg_delta:
                global_state[key] += avg_delta[key]
                
        self.global_model.load_state_dict(global_state)
        print(f"Coordinator: استخراج \u0394 W از {num_candidates} نفر منتخب... اجرای میانگین‌گیری فدرالی (FedAvg)...")
        print("Coordinator: وزن‌های مدل جهانی با موفقیت آپدیت شد.")

    def update_estimated_state(self, selected_candidates, all_students, s_hat_base):
        """
        تسک ۳.۶: به‌روزرسانی بردار تخمینی
        """
        selected_addresses = {p["student_address"] for p in selected_candidates}
        
        # افزایش تعداد کل جلسات برگزار شده
        self.session_count += 1
        
        if not hasattr(self, "s_hats"):
            self.s_hats = {student.public_address: s_hat_base.copy() for student in all_students}
            
        for student in all_students:
            addr = student.public_address
            current_s_hat = self.s_hats[addr]
            
            if addr in selected_addresses:
                # افزایش رکورد حضور موفق برای ارزش مشارکت (V_i)
                self.successful_attendance[addr] = self.successful_attendance.get(addr, 0) + 1
                for i in range(len(current_s_hat)):
                    current_s_hat[i] = current_s_hat[i] + self.eta * (100.0 - current_s_hat[i])
            else:
                for i in range(len(current_s_hat)):
                    current_s_hat[i] = current_s_hat[i] - self.eta * current_s_hat[i]
                    
            self.s_hats[addr] = current_s_hat
            
        print("Coordinator: به‌روزرسانی بردار تخمینی S_hat برای جلسه آینده.")

    def evaluate_global_model(self):
        """
        ارزیابی مدل جهانی برای استخراج خطای MSE و دقت Accuracy (تسک ۵.۱)
        """
        # تولید یک دیتاست تست تصادفی بزرگتر برای ارزیابی بهتر (مثلاً ۵۰ نمونه)
        num_samples = 50
        
        # مقادیر ویژگی‌ها تصادفی بین ۰ تا ۱
        test_features = torch.rand((num_samples, 3), dtype=torch.float32)
        
        # برچسب‌گذاری فرضی: اگر مجموع ویژگی‌ها بزرگتر از ۱.۵ بود یعنی وضعیت خوب است (۱) وگرنه (۰)
        test_labels = (test_features.sum(dim=1) > 1.5).float().view(-1, 1)
        
        self.global_model.eval()
        with torch.no_grad():
            predictions = self.global_model(test_features)
            loss_fn = torch.nn.MSELoss()
            mse = loss_fn(predictions, test_labels).item()
            
            # برای accuracy ساده با آستانه 0.5
            preds_binary = (predictions >= 0.5).float()
            correct = (preds_binary == test_labels).sum().item()
            accuracy = correct / len(test_labels)
            
        self.global_model.train()
        return mse, accuracy

    def generate_session_report(self, session_id, selected_candidates, total_proofs, valid_proofs):
        """
        تسک ۴.۴: تدوین گزارش نهایی جلسه (Session Report)
        """
        attendees_list = [p["student_address"] for p in selected_candidates]
        report = {
            "session_id": session_id,
            "attendees_list": attendees_list,
            "total_proofs": total_proofs,
            "valid_proofs": valid_proofs,
            "s_hats": getattr(self, "s_hats", {}), # به‌روزرسانی شده در تسک ۳.۶
            "timestamp": time.time()
        }
        return report

    def anchor_model(self, session_id):
        """
        تسک ۴.۵: ذخیره و هش‌گذاری مدل جهانی (Model Anchoring)
        """
        model_filename = f"global_model_v{session_id}.pt"
        torch.save(self.global_model.state_dict(), model_filename)
        
        # محاسبه هش فایل
        sha256_hash = hashlib.sha256()
        with open(model_filename, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return model_filename, sha256_hash.hexdigest()

    def end_session(self, session_id, selected_candidates, total_proofs, valid_proofs):
        """
        تسک ۴.۶: بستن حلقه (The Final Orchestrator Loop)
        """
        print("Coordinator: پایان یادگیری فدرالی. در حال تولید گزارش جلسه...")
        
        # تدوین گزارش جلسه (تسک ۴.۴)
        report = self.generate_session_report(session_id, selected_candidates, total_proofs, valid_proofs)
        
        # ذخیره و هش‌گذاری مدل (تسک ۴.۵)
        model_filename, model_hash = self.anchor_model(session_id)
        report["global_model_hash"] = model_hash
        
        # آپلود فایل‌ها به IPFS
        report_cid = self.ipfs_manager.upload_json(report)
        print(f"Coordinator: آپلود گزارش در IPFS... موفقیت‌آمیز. CID: `{report_cid}`")
        
        model_cid = self.ipfs_manager.upload_file(model_filename)
        print(f"Coordinator: آپلود مدل جهانی در IPFS... موفقیت‌آمیز. CID: `{model_cid}`")
        
        # ارتباط با بلاکچین
        print("Coordinator: در حال ارسال تراکنش به بلاکچین...")
        tx_hash, gas_used = self.web3_manager.submit_session_to_blockchain(session_id, report_cid, model_cid)
        
        # ثبت هزینه‌ها
        with open("gas_logs.csv", "a") as f:
            f.write(f"{session_id},{tx_hash},{gas_used}\n")
            
        print(f"Coordinator: تراکنش تایید شد! هش تراکنش: `{tx_hash}` | گاز مصرفی: `{gas_used} wei`.")
        print("Coordinator: جلسه با موفقیت خاتمه یافت و رکوردها ایمن شدند.")
