Add-Type -AssemblyName Microsoft.VisualBasic
$token = [Microsoft.VisualBasic.Interaction]::InputBox('Please paste your Hugging Face Access Token (starting with hf_...) here:', 'Deploy to Hugging Face', '')

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "Deployment cancelled."
    exit 1
}

Write-Host "Token received. Deploying to Hugging Face Spaces..."
git config credential.helper ""
git remote set-url hf "https://twdavidtw:$($token.Trim())@huggingface.co/spaces/twdavidtw/victor-snake-battle"
git push -f hf main:main

if ($LASTEXITCODE -eq 0) {
    Write-Host "Deployment successful!"
} else {
    Write-Host "Deployment failed. Check if your token has Write permission."
}
