import torch
import torch.nn as nn

class GlobalModel(nn.Module):
    def __init__(self):
        super(GlobalModel, self).__init__()
        # سه گره ورودی، یک لایه پنهان با هشت گره
        self.hidden = nn.Linear(3, 8)
        self.relu = nn.ReLU()
        # یک گره خروجی
        self.output = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.hidden(x)
        x = self.relu(x)
        x = self.output(x)
        x = self.sigmoid(x)
        return x

    def get_global_weights(self):
        """
        استخراج وزن‌های فعلی مدل مرکزی به صورت یک دیکشنری
        """
        return self.state_dict()
