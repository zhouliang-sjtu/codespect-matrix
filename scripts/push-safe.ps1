$ErrorActionPreference = "Stop"

Write-Host "`n=== Safe Push: Excludes docs/ directory from remote ===`n"

try {
    $branch = git rev-parse --abbrev-ref HEAD
    Write-Host "Current branch: $branch"
    
    $commitHash = git rev-parse HEAD
    Write-Host "Commit: $commitHash"
    
    Write-Host "`nStashing docs/ for safe push..."
    git stash push --include-untracked -m "safe-push-stash" docs/
    
    Write-Host "Pushing to remote..."
    git push origin $branch
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nRestoring docs/ locally..."
        git stash pop
        Write-Host "`nSUCCESS: Push completed."
        Write-Host "  - docs/ was NOT pushed to remote"
        Write-Host "  - docs/ is restored locally for tracking"
    } else {
        Write-Host "`nPush failed, restoring docs/..."
        git stash pop
        Write-Host "ERROR: Push failed. Check error above."
        exit 1
    }
} catch {
    Write-Host "`nERROR: $_"
    git stash pop 2>$null | Out-Null
    exit 1
}
