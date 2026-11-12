# راه‌اندازی سامانهٔ معاملهٔ کاغذی Kraken

این بسته برای حساب مجازی ۱۰٬۰۰۰ دلاری و جفت `BTC/USD` است. حالت پیش‌فرض `observe` است. برای تمرین IOC، سیاست `paper-alternating-v1` را صریحاً انتخاب کنید. [تنظیمات نمونه](config.example.json) مقادیر ثابت قرارداد و معادل پرچم‌های CLI را نشان می‌دهد. برنامه مقادیر مصوب را از کد اعمال می‌کند و این فایل را به‌عنوان ورودی اجرا نمی‌خواند.

## نصب و پیش‌شرط

از ریشهٔ مخزن، در PowerShell روی میزبان هدف اجرا کنید. `python` در خط اول باید Python 3.12 باشد.

```powershell
python --version
python -m venv .venv-crypto-v1
$py = ".\.venv-crypto-v1\Scripts\python.exe"
& $py -m pip install --require-hashes -r crypto_paper/requirements.lock
& $py -m crypto_paper --help
```

میزبان باید به Kraken عمومی روی HTTPS و WSS و به سه مرجع NTP روی UDP/123 دسترسی داشته باشد. ساعت را با ابزار میزبان همگام کنید. برنامه فقط اختلاف را اندازه می‌گیرد. اجرای پذیرش به دیسک محلی با ظرفیت کافی برای سقف ۵ GiB اجرا و حد آزاد ۲ GiB نیاز دارد. منبع و مدل کارمزد در [fee-source.json](fee-source.json) و هش آن در manifest ثبت می‌شود.

## ترتیب پذیرش

برای هر تلاش پوشهٔ تازه انتخاب کنید. زیرپوشه‌های فازها را در یک ریشه نگه دارید تا بازپخش پذیرش و قفل پژوهش بتوانند رسیدهای همین ساخت را بررسی کنند.

```powershell
$run = "runs/crypto-v1-" + (Get-Date -Format yyyyMMdd-HHmmss)
& $py -m crypto_paper verify --suite data --fixtures fixtures/crypto --out "$run/A/report.json"
& $py -m crypto_paper capture --duration-sec 86400 --force-reconnect-at-sec 21600 --out "$run/B"
& $py -m crypto_paper verify --suite execution --fixtures fixtures/crypto --out "$run/C/report.json"
```

پس از قبولی A، B و C اجرا کنید.

```powershell
& $py -m crypto_paper paper --policy paper-alternating-v1 --duration-sec 86400 --force-reconnect-at-sec 21600 --out "$run/D"
& $py -m crypto_paper replay --manifest "$run/D/manifest.json" --out "$run/D-replay"
```

گزارش `D` تا مقایسهٔ دفتر، `O01` را در انتظار بازپخش می‌گذارد. گزارش `D-replay` وضعیت نهایی `O01` را ثبت می‌کند. `raw/*.jsonl` فریم‌ها و کنترل‌ها، `bars.jsonl` نسخه‌های کندل، `ledger.sqlite3` تصمیم‌ها و رخدادهای حساب، `metrics.json` سن و پوشش، و `manifest.json` هش قطعه‌ها و کد را نگه می‌دارند. کد خروج غیرصفر و گزارش `FAIL` یا `BLOCKED` باید بررسی شود.

## توقف و بازیابی

- برای قفل دستی حین اجرا، فایل `STOP` را در پوشهٔ D با علت متنی UTF-8 بگذارید. پردازه آن را ثبت می‌کند، افزایش را لغو می‌کند و کاهش به صفر را با دفتر معتبر دنبال می‌کند. `Ctrl+C` جمع‌آوری را خاتمه می‌دهد و سفارش‌های باز محلی را لغو می‌کند. توقف پردازه خودش موقعیت را نمی‌بندد.
- بعد از خروج پردازه، برای قفل دستی ثبت‌شده فرمان `operator --action stop` را اجرا کنید. برای رفع هر قفل، یک فرمان با علت و تأیید اپراتور لازم است. گزینه‌ها `daily`، `drawdown` و `manual` هستند. رفع روزانه به روز UTC بعدی، ساعت مرجع معتبر و تطبیق دفتر وابسته است.
- برای ادامه بعد از قطع یا crash، همان مسیر، سیاست و نسخهٔ کد را با `--resume` بدهید. پیشوند commit‌شده با ثبت خام مقایسه و پسوند قابل بازیابی یک‌بار اعمال می‌شود. پردازه epoch تازه می‌گیرد و قفل‌ها، نقد و موقعیت را از دفتر نگه می‌دارد. نتیجهٔ اجرای ادامه‌یافته برای پذیرش ۲۴ساعتهٔ تازه استفاده نمی‌شود.
- در خرابی هش، قطعهٔ ناقص یا اختلاف دفتر، پردازه متوقف می‌شود. پوشهٔ شاهد را حفظ کنید. برای پذیرش تازه از پوشهٔ جدید استفاده کنید.

```powershell
& $py -m crypto_paper operator --run "$run/D" --action stop --reason "operator stop" --out "$run/stop.json"
& $py -m crypto_paper paper --policy paper-alternating-v1 --duration-sec 86400 --out "$run/D" --resume
```

## پژوهش

آزمون توسعه فقط دادهٔ مصنوعی دارد. پس از پذیرش عملیاتی، فرمان دوم اجازهٔ ثبت قفل را بررسی می‌کند.

```powershell
& $py -m crypto_paper research --protocol crypto-v1 --stage development --out "$run/E"
& $py -m crypto_paper research --protocol crypto-v1 --stage freeze --out "$run/F"
```

اگر `F/manifest.json` و `F/lock.json` ایجاد شدند، زمان شروع و پایان را از همان manifest بگیرید. دادهٔ خام `observe` از بعد از قفل را در `F/captures/<segment>` ثبت کنید. قطعه‌ها باید به ترتیب UTC، بدون هم‌پوشانی و با پوشش مرزهای روز باشند. برای نمونه، جمع‌آوری قبل از اولین نیمه‌شب آغاز شود و چرخش قطعه‌ها دور از نیمه‌شب انجام شود. برای دورهٔ تأییدی، ورودی‌ها و کد قفل‌شده حفظ می‌شوند. تا پایان بازه تنها سلامت و پوشش جمع‌آوری بررسی می‌شود. دفاتر جداگانهٔ عملکرد پس از موعد از ثبت خام ساخته می‌شوند.

```powershell
& $py -m crypto_paper research --protocol crypto-v1 --stage unseal --manifest "$run/F/manifest.json"
```

مقایسهٔ موتور اختیاری است و فرمان `verify --suite candidate` در این تحویل وضعیت مسدود را گزارش می‌کند. اجرای نامزد به capture پذیرفته‌شده و آداپتور پین‌شده نیاز دارد.
