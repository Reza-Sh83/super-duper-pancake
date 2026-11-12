# اجرای نسخهٔ کاغذی Kraken روی Docker

از ریشهٔ پروژه در PowerShell اجرا کنید. این مسیر برای Docker Desktop با موتور Linux و معماری amd64 آزموده شده است. image پایه با digest ثابت است و pip نسخه و SHA-256 wheel را با `requirements.lock` بررسی می‌کند. CLI همان `python -m crypto_paper` است. پردازه با UID/GID 65532 روی volume محلی Docker اجرا می‌شود.

```powershell
$ctx = 'desktop-linux'
$image = 'crypto-paper:v1-docker'
docker --context $ctx version
docker --context $ctx build --platform linux/amd64 -t $image -f Dockerfile.crypto-paper .
docker --context $ctx image inspect --format '{{.Id}}' $image
```

## پیش‌بررسی و آزمون‌ها

برای اجرای تازه نام یکتا انتخاب کنید. نام و شناسهٔ image را همراه نتیجه ثبت کنید. volume تازه در اولین اتصال مالکیت پوشهٔ `/evidence` را از image می‌گیرد. همین volume برای SQLite، ثبت خام و گزارش‌ها استفاده می‌شود.

```powershell
$id = 'docker-v1-' + (Get-Date -Format yyyyMMdd-HHmmss)
$volume = "crypto-paper-$id"
docker --context $ctx volume create --driver local --label project=crypto-paper $volume
$base = "/evidence/$id"
$mount = "type=volume,source=$volume,target=/evidence"
$opts = @('--init','--cap-drop=ALL','--security-opt=no-new-privileges','--mount',$mount)

docker --context $ctx run --rm @opts --entrypoint python $image /app/crypto_probe.py preflight "$base/preflight"
docker --context $ctx run --rm @opts $image verify --suite data --out "$base/A/report.json"
docker --context $ctx run --rm @opts $image verify --suite execution --out "$base/C/report.json"
docker --context $ctx run --rm @opts $image research --protocol crypto-v1 --stage development --out "$base/E"
```

پیش‌بررسی، DNS، HTTPS، snapshot دارای CRC از WSS، سه مرجع NTP، فضای آزاد، وابستگی و تراکنش و بازگشایی SQLite را گزارش می‌کند. نمونه‌گیری ساعت از داخل کانتینر انجام می‌شود. حد میانهٔ قدرمطلق ۵۰۰ میلی‌ثانیه و حد گسترهٔ سه نمونه ۲۵۰ میلی‌ثانیه است.

در اجرای ثبت‌شده، ساعت Windows و کانتینر هر دو حدود ۲۶ ثانیه جلو بودند. اپراتور Windows می‌تواند از **Settings → Time & language → Date & time → Sync now** ساعت را همگام کند. در صورت توقف سرویس، مدیر میزبان باید وضعیت Windows Time را بررسی کند. پس از همگامی، پیش‌بررسی را روی همان volume در مسیر تازهٔ `$base/preflight-recheck` اجرا کنید. اگر فقط کانتینر همچنان اختلاف دارد، وضعیت ساعت VM Docker Desktop را بررسی کنید. پیش از هر جمع‌آوری ۲۴ساعته، ظرفیت دیسک و نتیجهٔ پیش‌بررسی را دوباره بسنجید.

## T01 و O01

پس از قبولی پیش‌بررسی و A، B را با نام ثابت کانتینر شروع کنید. `docker wait` کد خروج را چاپ می‌کند. پایان عملیاتی با `B/report.json` سنجیده می‌شود.

```powershell
docker --context $ctx run -d --name "$id-b" @opts $image capture --duration-sec 86400 --force-reconnect-at-sec 21600 --out "$base/B"
docker --context $ctx ps --filter "name=$id-b"
docker --context $ctx wait "$id-b"
```

پس از قبولی B و C، D و بازپخش را اجرا کنید.

```powershell
docker --context $ctx run -d --name "$id-d" @opts $image paper --policy paper-alternating-v1 --duration-sec 86400 --force-reconnect-at-sec 21600 --out "$base/D"
docker --context $ctx wait "$id-d"
docker --context $ctx run --rm @opts $image replay --manifest "$base/D/manifest.json" --out "$base/D-replay"
```

مرحلهٔ D تا پایان بازپخش، O01 را معلق گزارش می‌کند. رسید نهایی O01 در `D-replay/report.json` است. پس از قبولی عملیاتی، قفل پژوهش فقط از مسیر [پروتکل پروژه](../crypto_paper/README.fa.md#پژوهش) ثبت می‌شود.

## توقف و بازیابی

برای قفل دستی در اجرای فعال، فایل STOP را در پوشهٔ D بسازید تا پردازه افزایش را قفل کند و کاهش را با دفتر معتبر پی بگیرد. برای خاتمهٔ پردازه، `docker stop` به‌واسطهٔ STOPSIGNAL تعریف‌شده SIGINT می‌فرستد. موقعیت در دفتر می‌ماند.

```powershell
docker --context $ctx exec "$id-d" touch "$base/D/STOP"
docker --context $ctx stop --time 45 "$id-d"
```

برای ثبت قفل دستی بعد از پایان پردازه، از فرمان `operator` استفاده کنید. با همان image، policy و volume، ادامهٔ تشخیصی در کانتینر تازه انجام می‌شود. پیش از ادامه، شاهد نهایی قبلی را صادر کنید زیرا گزارش مسیر ادامه به‌روز می‌شود.

```powershell
docker --context $ctx run --rm @opts $image operator --run "$base/D" --action stop --reason "operator stop" --out "$base/stop.json"
docker --context $ctx run -d --name "$id-d-resume" @opts $image paper --policy paper-alternating-v1 --duration-sec 86400 --out "$base/D" --resume
```

قبولی T01/O01 به جمع‌آوری تازه و پیوسته وابسته است. بازیابی تشخیصی در مسیر همان اجرا برای بررسی دفتر است.

## مشاهده و خروجی گرفتن شواهد

`docker logs "$id-b"` خروجی پردازه را نشان می‌دهد. برای کپی شواهد، پس از توقف نویسنده یک کانتینر صادرکننده با اتصال فقط‌خواندنی ایجاد کنید. این کانتینر را راه‌اندازی نکنید. پوشهٔ مقصد میزبان را برای هر نسخهٔ شاهد یکتا بگیرید.

```powershell
$exporter = "$id-export"
$destination = "runs/export-$id"
New-Item -ItemType Directory -Path $destination | Out-Null
docker --context $ctx create --name $exporter --mount "$mount,readonly" $image --help
docker --context $ctx cp "${exporter}:${base}/." $destination
if ($LASTEXITCODE -eq 0) { docker --context $ctx rm $exporter }
```

حذف کانتینر صادرکننده volume نام‌دار را حفظ می‌کند. روی میزبان، نسخهٔ صادرشدهٔ گزارش‌ها و capture را برای بررسی نگه دارید و برای بازیابی از SQLite اصلی روی volume استفاده کنید.

[نتیجهٔ اجرای Docker](../runs/docker-v1-20261107-01/RESULTS.fa.md) · [شواهد اجرای اولیهٔ Windows](../runs/crypto-v1-1794022916772/final-evidence/RESULTS.fa.md)
