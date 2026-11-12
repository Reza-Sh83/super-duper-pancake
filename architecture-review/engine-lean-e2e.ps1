$ErrorActionPreference='Stop'
$lean='D:\python_project\trade\research-repositories\github-2026-10-30\P031-quantconnect__lean-68d43d64770b'
$base=Join-Path ([IO.Path]::GetTempPath()) 'trade-lean-68d43d64770b'
$env:DOTNET_CLI_HOME=$base
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1'
$env:DOTNET_GENERATE_ASPNET_CERTIFICATE='false'
$launcher=Get-ChildItem -LiteralPath (Join-Path $lean 'Launcher/bin') -Filter 'QuantConnect.Lean.Launcher.dll' -Recurse | Where-Object { Test-Path ($_.FullName -replace '\.dll$','.runtimeconfig.json') } | Select-Object -First 1
if(!$launcher){throw 'launcher not found'}
$work=Join-Path $base 'trade-fixture'
$data=Join-Path $work 'Data'
$null=New-Item -ItemType Directory -Force $work,(Join-Path $data 'equity/usa/minute/spy'),(Join-Path $data 'equity/usa/map_files'),(Join-Path $data 'equity/usa/factor_files')
Copy-Item (Join-Path $lean 'Data/market-hours') $data -Recurse -Force
Copy-Item (Join-Path $lean 'Data/symbol-properties') $data -Recurse -Force
Copy-Item (Join-Path $lean 'Data/equity/usa/map_files/spy.csv') (Join-Path $data 'equity/usa/map_files') -Force
Copy-Item (Join-Path $lean 'Data/equity/usa/factor_files/spy.csv') (Join-Path $data 'equity/usa/factor_files') -Force
$algorithm=@'
using System;
using QuantConnect;
using QuantConnect.Algorithm;
using QuantConnect.Data;
using QuantConnect.Orders;
using QuantConnect.Orders.Fills;
public sealed class TradeFixtureAlgorithm : QCAlgorithm
{
    private Symbol symbol;
    private bool submitted;
    private decimal filled;
    public override void Initialize()
    {
        SetStartDate(2013,10,8);
        SetEndDate(2013,10,8);
        SetCash(10000);
        var security = AddEquity("SPY", Resolution.Minute, fillForward:false, dataNormalizationMode:DataNormalizationMode.Raw);
        security.SetFillModel(new ImmediateFillModel());
        symbol = security.Symbol;
    }
    public override void OnData(Slice data)
    {
        if (!data.Bars.ContainsKey(symbol)) return;
        var bar = data.Bars[symbol];
        Log($"FIXTURE_BAR {bar.EndTime:O} {bar.Low}");
        if (submitted) return;
        submitted = true;
        var ticket = LimitOrder(symbol,2,100);
        Log($"FIXTURE_SUBMIT {ticket.OrderId} {ticket.Status}");
    }
    public override void OnOrderEvent(OrderEvent evt)
    {
        filled += evt.FillQuantity;
        Log($"FIXTURE_EVENT {evt.UtcTime:O} {evt.Status} {evt.FillQuantity} {evt.FillPrice}");
    }
    public override void OnEndOfAlgorithm()
    {
        Log($"FIXTURE_RESULT submitted={submitted} filled={filled} position={Portfolio[symbol].Quantity} cash={Portfolio.Cash}");
    }
}
'@
[IO.File]::WriteAllText((Join-Path $work 'TradeFixtureAlgorithm.cs'),$algorithm)
$refs=Get-ChildItem -LiteralPath $launcher.DirectoryName -Filter '*.dll' | Where-Object { $_.Name -like 'QuantConnect*.dll' -or $_.Name -eq 'Python.Runtime.dll' } | ForEach-Object { '<Reference Include="'+$_.BaseName+'"><HintPath>'+[Security.SecurityElement]::Escape($_.FullName)+'</HintPath><Private>false</Private></Reference>' }
$proj='<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net10.0</TargetFramework></PropertyGroup><ItemGroup>'+($refs -join '')+'</ItemGroup></Project>'
[IO.File]::WriteAllText((Join-Path $work 'TradeFixture.csproj'),$proj)
dotnet build (Join-Path $work 'TradeFixture.csproj') --nologo -v quiet
if($LASTEXITCODE){exit $LASTEXITCODE}
$algoDll=Join-Path $work 'bin/Debug/net10.0/TradeFixture.dll'
$zip=Join-Path $data 'equity/usa/minute/spy/20131008_trade.zip'
$csv=Join-Path $work '20131008_spy_minute_trade.csv'
foreach($case in @('touch','cross','stale_equal')){
 $lows=switch($case){'touch'{@(101,100,101)} 'cross'{@(101,99,101)} 'stale_equal'{@(99,101,101)}}
 $rows=0..2 | ForEach-Object { '{0},1020000,1030000,{1},1020000,1000' -f (34200000+60000*$_),($lows[$_]*10000) }
 [IO.File]::WriteAllLines($csv,[string[]]$rows)
 Compress-Archive -LiteralPath $csv -DestinationPath $zip -Force
 $caseDir=Join-Path $work $case
 $null=New-Item -ItemType Directory -Force $caseDir
 $conf=Get-Content -Raw (Join-Path $lean 'Launcher/config.json') | ConvertFrom-Json -AsHashtable
 $conf['environment']='backtesting';$conf['algorithm-type-name']='TradeFixtureAlgorithm';$conf['algorithm-location']=$algoDll;$conf['data-folder']=$data;$conf['results-destination-folder']=$caseDir;$conf['close-automatically']=$true
 [IO.File]::WriteAllText((Join-Path $caseDir 'config.json'),($conf | ConvertTo-Json -Depth 20))
 Push-Location $caseDir
 try {
  $log=Join-Path $caseDir 'run.log'
  dotnet $launcher.FullName *> $log
  if($LASTEXITCODE){Get-Content $log -Tail 35; exit $LASTEXITCODE}
  Write-Output ('CASE='+$case)
  Select-String -LiteralPath $log -Pattern 'FIXTURE_|Runtime Error|Exception' | Select-Object -First 30 | ForEach-Object Line
 } finally {Pop-Location}
}
