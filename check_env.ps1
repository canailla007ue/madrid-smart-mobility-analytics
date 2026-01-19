# powershell
# Archivo: `check_env.ps1`
$host.UI.RawUI.WindowTitle = "Verificador de Entorno TFG - Bus Monitor"

$vars = @(
    "API_KEY",
    "EMT_CLIENT_ID",
    "EMT_PASSWORD",
    "RABBITMQ_USER",
    "RABBITMQ_PASS",
    "RABBITMQ_HOST"

)

Write-Host "===================================================="
Write-Host "  VERIFICADOR DE VARIABLES DE ENTORNO (TFG)"
Write-Host "====================================================`n"

$missing = 0
foreach ($v in $vars) {
    $val = [Environment]::GetEnvironmentVariable($v, "User")
    if ([string]::IsNullOrEmpty($val)) {
        Write-Host "[X] ERROR: La variable $v no está definida." -ForegroundColor Red
        $missing++
    } else {
        # No mostrar valores sensibles
        if ($v -match 'PASS|PASSWORD|KEY|TOKEN') {
            Write-Host "[OK] $v está configurada correctamente (valor oculto)." -ForegroundColor Green
        } else {
            Write-Host "[OK] $v = $val" -ForegroundColor Green
        }
    }
}

Write-Host "----------------------------------------------------"
if ($missing -gt 0) {
    Write-Host "[!] ADVERTENCIA: Faltan $missing variable(s) por configurar." -ForegroundColor Yellow
    Write-Host "[!] Ejemplo (PowerShell):" -ForegroundColor Yellow
    Write-Host "    setx AEMET_API_KEY `"tu_api_key_aemet`""
    Write-Host "    setx EMT_CLIENT_ID `"tu_client_id_emt`""
    Write-Host "    setx EMT_PASSWORD `"tu_password_emt`""
    Write-Host ""
    Write-Host "[!] Después de usar setx, abre una nueva sesión de terminal para que las variables estén disponibles." -ForegroundColor Yellow
    $exitCode = 1
} else {
    Write-Host "[v] TODO CORRECTO: El entorno está listo para ejecutar el proyecto." -ForegroundColor Cyan
    $exitCode = 0
}

Write-Host "====================================================`n"
Read-Host -Prompt "Presiona Enter para salir"
exit $exitCode