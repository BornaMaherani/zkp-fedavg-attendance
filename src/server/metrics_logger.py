import csv
import os

class MetricsLogger:
    def __init__(self, filepath="evaluation_metrics.csv"):
        self.filepath = filepath
        self.headers = [
            "session_id", 
            "scenario", 
            "execution_time", 
            "zkp_verification_time", 
            "zkp_success_rate",
            "model_mse",
            "model_accuracy"
        ]
        
        # اگر فایل وجود ندارد، هدرها را بنویسیم
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log_metrics(self, metrics):
        """
        metrics: دیکشنری حاوی مقادیر هدرها
        """
        with open(self.filepath, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(metrics)
