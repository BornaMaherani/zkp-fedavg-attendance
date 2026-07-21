pragma circom 2.0.0;

// وارد کردن کتابخانه برای مقایسه اعداد
include "node_modules/circomlib/circuits/comparators.circom";

template ErrorValidator() {
    // ورودی‌های خصوصی (وضعیت واقعی دستگاه که نباید فاش شود)
    signal input s_real[3]; // [E_real, Q_real, D_real]

    // ورودی‌های عمومی (تخمین هماهنگ‌کننده، ضرایب و آستانه مجاز)
    signal input s_hat[3];  // [E_hat, Q_hat, D_hat]
    signal input alphas[3];
    signal input eps_max;

    // خروجی مدار (۱ به معنای تایید و ۰ به معنای رد)
    signal output is_valid;

    // متغیرهای میانی برای محاسبات
    signal diff[3];
    signal sq[3];
    signal term[3];
    signal total_error;

    // محاسبه تفاضل، مجذور و اعمال ضرایب
    diff[0] <== s_real[0] - s_hat[0];
    sq[0] <== diff[0] * diff[0];
    term[0] <== alphas[0] * sq[0];

    diff[1] <== s_real[1] - s_hat[1];
    sq[1] <== diff[1] * diff[1];
    term[1] <== alphas[1] * sq[1];

    diff[2] <== s_real[2] - s_hat[2];
    sq[2] <== diff[2] * diff[2];
    term[2] <== alphas[2] * sq[2];

    // محاسبه مجموع خطای پیش‌بینی
    total_error <== term[0] + term[1] + term[2];

    // بررسی کوچکتر بودن خطا از آستانه مجاز
    component lt = LessThan(32);
    lt.in[0] <== total_error;
    lt.in[1] <== eps_max;

    is_valid <== lt.out;
}

// تعریف تابع اصلی و مشخص کردن ورودی‌های عمومی
component main {public [s_hat, alphas, eps_max]} = ErrorValidator();