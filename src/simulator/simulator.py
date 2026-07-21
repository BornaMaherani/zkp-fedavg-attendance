import numpy as np

class Simulator:
    def __init__(self, students):
        self.students = students

    def generate_client_states(self, cheat_mode=False):
        """
        تسک ۲.۱ و ۵.۲: تولید وضعیت کلاینت‌ها و اعمال سناریوی تقلب (Cheat Mode)
        """
        # مقادیر پایه برای سطح انرژی (E)، کیفیت اتصال (Q) و پایداری شبکه (D)
        base_E, base_Q, base_D = 90.0, 90.0, 90.0
        
        stable_count = 0
        unstable_count = 0
        
        client_states = {}
        for student in self.students:
            # تخصیص احتمال: 70% پایدار، 30% ناپایدار
            is_stable = np.random.rand() < 0.70
            
            if is_stable:
                # نویز کمتر برای دانشجویان پایدار
                noise_scale = 2.0
                stable_count += 1
            else:
                # نویز شدیدتر برای دانشجویان ناپایدار (خطا بالا می‌رود)
                noise_scale = 15.0
                unstable_count += 1
                
            # تولید نویز گاوسی روی مقادیر پایه
            E = np.clip(np.random.normal(base_E, noise_scale), 0, 100)
            Q = np.clip(np.random.normal(base_Q, noise_scale), 0, 100)
            D = np.clip(np.random.normal(base_D, noise_scale), 0, 100)
            
            s_real = [E, Q, D]
            
            # تزریق مستقیم وضعیت به عنوان سنسور محلی دانشجو
            student.s_real = s_real 
            student.is_cheater = False
            client_states[student.student_id] = s_real
            
        # اعمال حالت تقلب (تسک ۵.۲)
        if cheat_mode and unstable_count > 0:
            unstable_students = [s for s in self.students if client_states[s.student_id][0] > 95 or client_states[s.student_id][0] < 85]
            # در اینجا برای سادگی کسانی که نویز بالا گرفتند را به عنوان ناپایدار می‌شناسیم
            num_cheaters = max(1, int(0.2 * len(unstable_students))) if unstable_students else 0
            cheaters = np.random.choice(unstable_students, num_cheaters, replace=False)
            for cheater in cheaters:
                cheater.is_cheater = True
            print(f"Simulator: حالت تقلب (Cheat Mode) فعال است. {num_cheaters} دانشجو تصمیم به تقلب گرفتند.")
            
        print(f"Simulator (نفر اول): تولید نویز گاوسی... {stable_count} دانشجو وضعیت پایدار و {unstable_count} دانشجو وضعیت ناپایدار دریافت کردند.")
        return client_states
