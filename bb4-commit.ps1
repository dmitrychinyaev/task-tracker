$ErrorActionPreference = 'Continue'
Set-Location 'c:\Users\Dmitry\Desktop\task-tracker'
$tmp = Join-Path $env:TEMP 'bb4'
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
Remove-Item 'c:\Users\Dmitry\Desktop\task-tracker\bb4-rules-diff.txt' -Force -ErrorAction SilentlyContinue
git status --short *> (Join-Path $tmp 'status-before.txt')
git add . *> (Join-Path $tmp 'add.txt')
git status --short *> (Join-Path $tmp 'status-staged.txt')
git commit -m "feat: structured logging and global error handlers (BB-0004)" *> (Join-Path $tmp 'commit.txt')
git push origin master *> (Join-Path $tmp 'push.txt')
git --no-pager log --oneline -3 *> (Join-Path $tmp 'log.txt')
git status --short *> (Join-Path $tmp 'status-after.txt')
'DONE' | Out-File (Join-Path $tmp 'done.txt') -Encoding utf8
