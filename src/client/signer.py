from eth_account.messages import encode_defunct
from web3 import Web3

class Signer:
    def __init__(self, private_key):
        self.private_key = private_key
        self.w3 = Web3()

    def sign_challenge(self, challenge_string):
        """
        دریافت چالش امنیتی از هماهنگ‌کننده و امضای آن با استفاده از کلید خصوصی
        """
        # استانداردسازی پیام برای امضا در محیط‌های مبتنی بر ماشین مجازی اتریوم (EVM)
        message = encode_defunct(text=challenge_string)
        
        # تولید امضای دیجیتال غیرقابل جعل
        signed_message = self.w3.eth.account.sign_message(message, private_key=self.private_key)
        
        print(f"چالش امنیتی با موفقیت تایید و امضا شد.")
        return {
            "challenge": challenge_string,
            "signature": signed_message.signature.hex()
        }