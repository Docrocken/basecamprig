param (
    [string]$Domain = "basecamprig.com",
    [string]$BlogDir = "C:\Automation\basecamprig\src\content\blog",
    [string]$KeyFile = "C:\Automation\basecamprig\indexnow_key.txt"
)

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " STARTAR INDEXERINGSPING FÖR $Domain" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

if (-not (Test-Path $KeyFile)) {
    Write-Error "Hittade inte indexnow_key.txt i projektmappen! Kör initieringssteget först."
    exit 1
}

$apiKey = (Get-Content $KeyFile -Raw).Trim()

# 1. Hämta alla aktiva artikel-slugs från bloggmappen
$mdFiles = Get-ChildItem -Path $BlogDir -Filter "*.md"
$urlList = @("https://$Domain/")

foreach ($file in $mdFiles) {
    # Matchar filnamnsstrukturen: YYYY-MM-DD-slug.md eller slug.md
    $slug = $file.BaseName
    if ($slug -match '^\d{4}-\d{2}-\d{2}-(.*)$') {
        $slug = $matches[1]
    }
    # Ändra till /posts/ eller /blog/ beroende på din exakta Astro-routing
    $urlList += "https://$Domain/blog/$slug/"
}

Write-Host "`nHittade $($urlList.Count) URL:er att skicka för indexering." -ForegroundColor Yellow

# 2. Skicka batch till Bing / IndexNow
$indexNowPayload = @{
    host        = $Domain
    key         = $apiKey
    keyLocation = "https://$Domain/$apiKey.txt"
    urlList     = $urlList
} | ConvertTo-Json -Compress

try {
    Write-Host "`nSkickar batch-ping till Bing (IndexNow)..." -NoNewline
    $response = Invoke-RestMethod -Uri "https://api.indexnow.org/IndexNow" `
                                  -Method Post `
                                  -ContentType "application/json; charset=utf-8" `
                                  -Body $indexNowPayload
    Write-Host " [OK]" -ForegroundColor Green
    Write-Host "Bing/IndexNow tog emot förfrågan (HTTP 200/202). URL:erna prioriteras för crawlning." -ForegroundColor Green
}
catch {
    Write-Host " [STATUS: $($_.Exception.Response.StatusCode.value__)]" -ForegroundColor Yellow
    Write-Host "Detaljer: $($_.Exception.Message)"
}

# 3. Verifiera Sitemap & Robots för Google / Bing botar
$sitemapUrl = "https://$Domain/sitemap-index.xml"
Write-Host "`nKontrollerar status för sitemap: $sitemapUrl"
try {
    $sitemapCheck = Invoke-WebRequest -Uri $sitemapUrl -Method Head -UseBasicParsing
    if ($sitemapCheck.StatusCode -eq 200) {
        Write-Host "Sitemap är aktiv (HTTP 200). Googlebot och Bingbot hämtar automatiskt uppdateringar via robots.txt." -ForegroundColor Green
    }
}
catch {
    Write-Host "Varning: Sitemapen svarade inte med 200 OK. Säkerställ att @astrojs/sitemap är konfigurerad." -ForegroundColor Yellow
}

Write-Host "`nIndexering klar!" -ForegroundColor Cyan
