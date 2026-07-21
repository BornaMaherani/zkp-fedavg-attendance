import torch
import torch.nn as nn
import torch.optim as optim

class LocalModel(nn.Module):
    def __init__(self):
        super(LocalModel, self).__init__()
        # سه گره ورودی، یک لایه پنهان با هشت گره
        self.hidden = nn.Linear(3, 8)
        # تابع فعال‌ساز یکسوساز
        self.relu = nn.ReLU()
        # یک گره خروجی
        self.output = nn.Linear(8, 1)
        # تابع فعال‌ساز سیگموئید
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.hidden(x)
        x = self.relu(x)
        x = self.output(x)
        x = self.sigmoid(x)
        return x

class LocalML:
    def __init__(self, global_weights=None):
        self.model = LocalModel()
        if global_weights:
            self.model.load_state_dict(global_weights)
        
        # تابع زیان آنتروپی متقاطع دودویی
        self.criterion = nn.BCELoss()
        # الگوریتم بهینه‌ساز گرادیان کاهشی تصادفی
        self.optimizer = optim.SGD(self.model.parameters(), lr=0.01)

    def train_and_get_diff(self, features, labels):
        initial_weights = {name: param.clone() for name, param in self.model.named_parameters()}
        
        # آموزش برای دو دوره
        for epoch in range(2):
            self.optimizer.zero_grad()
            outputs = self.model(features)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()
            
        # استخراج تفاضل وزن‌ها جهت ارسال
        weight_diff = {}
        for name, param in self.model.named_parameters():
            weight_diff[name] = (param.data - initial_weights[name].data).numpy().tolist()
            
        return weight_diff