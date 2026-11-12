# نقطهٔ ورود ایجنت پیاده‌ساز کریپتو

**شروع ساخت مجاز** برای کاغذی محلی Kraken Spot BTC/USD. همهٔ انتخاب‌های کاربر برای نسخهٔ اول ثبت شده‌اند. این بسته سند، فیکسچر و شواهد آزمون است. مسیر محصول طبق قرارداد فرمان‌های زیر ساخته می‌شود.

ترتیب مرجع. ابتدا این فایل، سپس [قرارداد ساخت](CRYPTO_BUILD_CONTRACT.fa.md)، [معماری](CRYPTO_ARCHITECTURE_SPEC.fa.md)، [پروتکل تأییدی](CRYPTO_TEST_PROTOCOL.fa.md) و [ماتریس اجزا](CRYPTO_COMPONENT_MATRIX.fa.md). قرارداد ساخت مرجع مقادیر عملیاتی و تعاریف دقیق است. معماری مرجع دامنه و حدود مصوب است.

## انتخاب قطعی وابستگی

Python 3.12، `websockets==15.0.1` با asyncio برای WS عمومی، و کتابخانهٔ استاندارد `urllib.request`، `decimal`، `sqlite3`، `json`، `zlib` و `unittest`. CLI با argparse. در ساخت، نسخه و هش wheel در lockfile ثبت و از محیط جدا نصب شود. JSONL چرخشی و SQLite روی دیسک محلی. API خصوصی در نسخهٔ کاغذی وجود ندارد. NautilusTrader و Hummingbot به‌دلیل نبود شاهد پین‌شدهٔ هم‌ارز روی capture مشترک و اضافه‌کردن چرخهٔ نصب و مدل سفارش مستقل، وابستگی نسخهٔ اول نیستند. CCXT برای Time/Depth شاهد مفید دارد اما در مسیر پایه سه endpoint بومی کافی‌اند و wrapper و normalization اضافه می‌کند. هیچ ادعای کاهش اندازهٔ کد از بازاستفادهٔ این بسته‌ها وجود ندارد. مقایسهٔ M01 یک شاخهٔ بعدی است و نتیجهٔ آن انتخاب نسخهٔ اول را معلق نمی‌کند. [websockets 15.0.1](https://pypi.org/project/websockets/15.0.1/)

## مراحل و قرارداد فرمان

فرمان‌های محصول در این جدول **قرارداد پیاده‌سازی** هستند. همه exit code صفر فقط در قبولی، و JSON نتیجه با `schema_version, run_id, checks[{id,status,expected,observed}], input_hashes, started_utc, finished_utc` بنویسند. وضعیت هر آزمون PASS، FAIL یا BLOCKED باشد. FAIL و BLOCKED کد غیرصفر و علت دارند. مسیر خروجی نسبی به پوشهٔ اجراست. ایجنت پیاده‌ساز مالک مراحل A تا F است و اپراتور مالک ساعت/دیسک میزبان و رفع توقف. اجرای تازه در مسیر منحصربه‌فرد انجام شود.

| فاز و پیش‌نیاز | فرمان و ورودی | خروجی و آزمون | عبور و بازگشت |
|---|---|---|---|
| A. قرارداد داده و fixture، Python و lockfile | `python -m crypto_paper verify --suite data --fixtures fixtures/crypto --out runs/A/report.json` | D01/D02، schema فریم و book، checksum معلوم، qty صفر، تغییر/تکرار سطح، epoch قدیمی، gap و snapshot. آزمون کندل F01 از مرز UTC و dedup. | PASS کامل، در خرابی توقف پردازش و ثبت payload یا quarantine. |
| B. capture میزبان، A و NTP همگام و دیسک کافی | `python -m crypto_paper capture --duration-sec 86400 --force-reconnect-at-sec 21600 --out runs/B` | manifest، `raw/*.jsonl`، `bars.jsonl`، `metrics.json` و `report.json`. T01/T02 با حدود قرارداد، سن، پوشش و resync. | از UTC قابل ثبت شروع شود و ۶ مرز ۴ساعته در بازهٔ باز-بستهٔ آزمون محاسبه شوند. FAIL به capture تشخیصی و تکرار روی مسیر جدید برگردد. |
| C. موتور، دفتر و ریسک، A | `python -m crypto_paper verify --suite execution --fixtures fixtures/crypto --out runs/C/report.json` | X01/X02، R01/R02. SQLite schema و دفتر اثر؛ تطبیق مقادیر دقیق فیکسچر، crash، قفل، حداقل و dust. | صفر اختلاف، صفر fill تکراری و صفر اثر دادهٔ کهنه. در شکست snapshot مشتق با replay دفتر بازسازی شود. |
| D. پذیرش کاغذی، B و C | `python -m crypto_paper paper --policy paper-alternating-v1 --duration-sec 86400 --force-reconnect-at-sec 21600 --out runs/D` سپس `python -m crypto_paper replay --manifest runs/D/manifest.json --out runs/D-replay` | O01، `ledger.sqlite3`، capture و گزارش تطبیق؛ دست‌کم یک قصد ورود و یک قصد خروج از سیاست عملیاتی، دست‌کم یک fill معتبر و صفر اختلاف توالی مالی بعد از replay. | در شکست، HALTED یا observe و ثبت علت؛ دفتر قبلی حفظ شود. قبولی D مجوز private نیست. |
| E. پژوهش، A تا D | `python -m crypto_paper research --protocol crypto-v1 --stage development --out runs/E` سپس `python -m crypto_paper research --protocol crypto-v1 --stage freeze --out runs/F` | P01 و manifest قفل P02. پس از پایان و ثبت پذیرش پوشش، `--stage unseal --manifest runs/F/manifest.json` یک‌بار مجاز. | نتیجهٔ زودهنگام ممنوع. اگر P02 رد یا نامعتبر شد، فقط پژوهش/observe. |
| F. مقایسهٔ اختیاری موتور، capture قبولی D | `python -m crypto_paper verify --suite candidate --candidate <pinned-id> --manifest runs/D/manifest.json --out runs/M/report.json` | M01، همان ورودی و سفارش و دفتر قابل مقایسه. commit، package hash، مجوز و موارد اختلاف. | fallback همیشگی موتور پایه. نبود runtime یا اختلاف معتبر نتیجهٔ BLOCKED/FAIL با علت دارد. |

### فیکسچر و انتظار

[فیکسچر عددی JSON](build-contract-fixture.json) ورودی و خروجی دقیق F01، X01 و R01 را دارد. آن را همراه fixtureهای زیر وارد تست محصول کن.

- **D01/D02 و T02:** از [capture عمومی Kraken](kraken-crc-probe.json) استفاده کن. checksum دستکاری‌شده، update قبل snapshot، حذف سطح، تکرار timestamp مجاز، overflow، epoch قدیمی و مرز age ۱۹۹۹/۲۰۰۰/۲۰۰۱ ms و زمان آینده در مرز ۵۰۰ ms. READY تنها با snapshot جدید. CRC از [راهنمای رسمی](https://docs.kraken.com/exchange/guides/websockets/book-checksum-v2) به‌عنوان کنترل معلوم هم آزموده شود.
- **X02 و R02:** یک fill را پس از commit دوباره تحویل بده و نقد/مقدار را با فیکسچر مقایسه کن. crash قبل و بعد commit تزریق شود. دو سفارش از عمق یک سطح یک‌بار مصرف کنند. NAV اولیه ۱۰٬۰۰۰، NAV ابتدای روز ۱۰٬۰۰۰، NAV=۹۹۰۰ دقیقاً قفل روزانه و NAV=۹۶۰۰ نسبت به اوج اولیه قفل افت می‌دهد. با هر دو قفل، رفع روزانه به‌تنهایی صفر خرید مجاز. restart قفل را نگه دارد. باقی‌ماندهٔ زیر qty_min با DUST بدون fill ساختگی ثبت شود.
- **M01:** همان fixture و capture O01، با manifest یکسان. معیارهای پایهٔ X01/X02 با log و ledger مقایسه شوند. قابلیت‌های خروجی هر موتور را جدا ثبت کن. تطبیق IO و تغییرات حساب معیار است. تست import یا تست helper جای آزمون مسیر را نمی‌گیرد.

## وضعیت دروازه‌ها

**مانع شروع:** مورد تصمیم‌گیری کاربر باقی نمانده است. برای شروع C یا replay خوراک زنده لازم نیست. نیازهای host برای B/D از آزمون آفلاین جدا هستند.

**پس از ساخت:** D01 تا O01 روی محصول، آزمون ۲۴ساعته روی ساعت همگام، بررسی ظرفیت دیسک و اعتبارسنجی manifest، P02 بعد از قفل، و M01 فقط برای بررسی جایگزینی. شواهد فعلی شامل [آزمون واقعی REST و محاسبهٔ مرجع](build-public-rest-probe-result.json)، [قطع و بازیابی عمومی](kraken-forced-reconnect-result.json) و [IOC روی capture](reference-captured-ioc-result.json) است. اتصال REST و حساب مرجع، قبولی O01 یا آزمون ۲۴ساعته را اثبات نمی‌کنند.

**خارج از کاغذی:** حساب و کشور و کلید، اجرای واقعی، مسیر کیف پول، مشتقه و بودجهٔ پولی. شروط اجرای واقعی در سند معماری ثبت شده‌اند. برای هزینه یا فعال‌سازی خصوصی تأیید جداگانه لازم است.

[نتیجهٔ آزمون مرجع فیکسچر](build-fixture-reference-result.json) · [کد آزمون فیکسچر](build-fixture-reference.py) · [رسید تلاش محیط نامزدها](candidate-runtime-attempt.json)
