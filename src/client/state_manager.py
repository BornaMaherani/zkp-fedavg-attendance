import json
import os
import subprocess

class StateManager:
    def __init__(self, alphas, eps_max, zkp_dir="../zkp"):
        self.alphas = alphas
        self.eps_max = eps_max
        self.zkp_dir = zkp_dir

    def calculate_weighted_mse(self, s_real, s_hat):
        """محاسبه خطای میانگین مربعات با اعمال ضرایب وزنی"""
        total_error = 0
        for r, h, a in zip(s_real, s_hat, self.alphas):
            total_error += a * ((r - h) ** 2)
        return total_error

    def process_state_and_prepare_proof(self, s_real, s_hat):
        """روال تصمیم‌گیری محلی و تولید پرونده ورودی مدار"""
        error = self.calculate_weighted_mse(s_real, s_hat)
        
        if error <= self.eps_max:
            print(f"وضعیت مجاز ارزیابی شد. (مقدار خطا: {error})")
            
            input_data = {
                "s_real": s_real,
                "s_hat": s_hat,
                "alphas": self.alphas,
                "eps_max": self.eps_max
            }
            
            input_path = os.path.join(self.zkp_dir, "input.json")
            with open(input_path, 'w') as f:
                json.dump(input_data, f, indent=4)
            
            return True
        else:
            print(f"خطا غیرمجاز است (مقدار خطا: {error}). بسته آمادگی تولید نخواهد شد.")
            return False
        
    def generate_proof(self):
        """اجرای خودکار ابزارهای خط فرمان برای تولید اثبات دانایی صفر"""
        print("در حال محاسبه متغیرهای میانی و تولید فایل شاهد (Witness)...")
        
        witness_script = os.path.join(self.zkp_dir, "circuit_js", "generate_witness.js")
        wasm_file = os.path.join(self.zkp_dir, "circuit_js", "circuit.wasm")
        input_file = os.path.join(self.zkp_dir, "input.json")
        witness_file = os.path.join(self.zkp_dir, "witness.wtns")
        
        try:
            # اجرای دستور node از درون پایتون
            subprocess.run(["node", witness_script, wasm_file, input_file, witness_file], check=True)
            print("فایل شاهد با موفقیت تولید شد.")
        except subprocess.CalledProcessError as e:
            print("خطا در اجرای فایل جاوااسکریپت:", e)
            return False

        print("در حال استخراج سند اثبات رمزنگاری‌شده (Proof)...")
        zkey_file = os.path.join(self.zkp_dir, "circuit_final.zkey")
        proof_file = os.path.join(self.zkp_dir, "proof.json")
        public_file = os.path.join(self.zkp_dir, "public.json")
        
        try:
            # اجرای دستور snarkjs (با shell=True برای سازگاری بهتر در سیستم‌عامل ویندوز)
            prove_cmd = f"snarkjs groth16 prove {zkey_file} {witness_file} {proof_file} {public_file}"
            subprocess.run(prove_cmd, shell=True, check=True)
            print("پرونده‌های proof.json و public.json با موفقیت آماده ارسال شدند!")
            return True
        except subprocess.CalledProcessError as e:
            print("خطا در تولید اثبات نهایی:", e)
            return False