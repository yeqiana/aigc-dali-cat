param(
    [Parameter(Mandatory=$true)][ValidateSet('complete-handshake')][string]$Action,
    [Parameter(Mandatory=$true)][string]$RequestId,
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$true)][string]$HostInstanceId,
    [Parameter(Mandatory=$true)][string]$RunnerInstanceId
)
$ErrorActionPreference = 'Stop'

function Get-Sha256Hex([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

$repo = (git rev-parse --show-toplevel).Trim()
if (-not $repo) { throw 'Host workspace is not a Git repository' }
$repoIdentityInput = $repo.Replace('\','/').TrimEnd('/').ToLowerInvariant()
$workspaceIdentity = Get-Sha256Hex ([System.Text.Encoding]::UTF8.GetBytes($repoIdentityInput))
$evidenceRoot = Join-Path $repo '.storyos/host-handshake'
$attachmentPath = Join-Path $repo '.storyos/runtime-launcher/webcodex-host-attachment.json'
$requestPath = Join-Path $evidenceRoot ($RequestId + '.request.json')
$claimPath = Join-Path $evidenceRoot ($RequestId + '.claim.json')
$completionPath = Join-Path $evidenceRoot ($RequestId + '.completion.json')
if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) { throw 'StoryOS handshake request is missing' }
$requestRaw = [System.IO.File]::ReadAllBytes($requestPath)
$requestHash = Get-Sha256Hex $requestRaw
$request = [System.Text.Encoding]::UTF8.GetString($requestRaw) | ConvertFrom-Json
if ($request.request_id -ne $RequestId) { throw 'request identity mismatch' }
if ($request.provider -ne 'webcodex' -or $request.transport -ne 'WEBCODEX' -or $request.execution_mode -ne 'host_mcp_runner') { throw 'request provider contract mismatch' }
if ($request.workspace_identity -ne $workspaceIdentity -or $request.repository_root_identity -ne $workspaceIdentity) { throw 'request belongs to a different workspace' }
if ((Get-Date).ToUniversalTime() -ge [DateTime]::Parse($request.expires_at).ToUniversalTime()) { throw 'StoryOS handshake challenge expired' }
if (Test-Path -LiteralPath $completionPath -PathType Leaf) {
    $existing = Get-Content -LiteralPath $completionPath -Raw | ConvertFrom-Json
    if ($existing.request_sha256 -ne $requestHash) { throw 'existing completion does not match request' }
    Write-Output '{"status":"ALREADY_COMPLETED","completion_count":1}'
    exit 0
}

$claimedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
$claim = [ordered]@{
    schema_version = 1; request_id = $RequestId; request_sha256 = $requestHash
    claim_identity = $RunnerInstanceId; claimed_at = $claimedAt
    provider = 'webcodex'; transport = 'WEBCODEX'; execution_mode = 'host_mcp_runner'
    workspace_identity = $workspaceIdentity; project_id = $ProjectId
}
$claimBytes = [System.Text.Encoding]::UTF8.GetBytes(($claim | ConvertTo-Json -Depth 8))
try {
    $claimStream = [System.IO.File]::Open($claimPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try { $claimStream.Write($claimBytes, 0, $claimBytes.Length) } finally { $claimStream.Dispose() }
} catch [System.IO.IOException] {
    if (Test-Path -LiteralPath $completionPath -PathType Leaf) { Write-Output '{"status":"ALREADY_COMPLETED","completion_count":1}'; exit 0 }
    throw 'handshake request was already claimed; refusing duplicate completion'
}

$completed = (Get-Date).ToUniversalTime()
$nonceHash = Get-Sha256Hex ([System.Text.Encoding]::UTF8.GetBytes([string]$request.nonce))
$completion = [ordered]@{
    schema_version = 1; status = 'COMPLETED'; request_id = $RequestId
    request_sha256 = $requestHash; nonce_sha256 = $nonceHash
    provider = 'webcodex'; transport = 'WEBCODEX'; execution_mode = 'host_mcp_runner'
    workspace_identity = $workspaceIdentity; repository_root_identity = $workspaceIdentity
    project_id = $ProjectId; host_instance_id = $HostInstanceId; runner_instance_id = $RunnerInstanceId
    claim_identity = $RunnerInstanceId; claimed_at = $claimedAt
    completed_at = $completed.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
    capabilities = [ordered]@{ repository_access = $true; host_request_consumer = $true; completion_writer = $true }
    side_effects = [ordered]@{ model_calls = 0; image_calls = 0; authority_writes = 0; episode_transitions = 0 }
}
$completionJson = $completion | ConvertTo-Json -Depth 8 -Compress
$completionBytes = [System.Text.Encoding]::UTF8.GetBytes($completionJson)
$completionSha = Get-Sha256Hex $completionBytes
try {
    $completionStream = [System.IO.File]::Open($completionPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try { $completionStream.Write($completionBytes, 0, $completionBytes.Length) } finally { $completionStream.Dispose() }
} catch [System.IO.IOException] {
    throw 'completion already exists; refusing duplicate completion'
}

$attachment = [ordered]@{
    schema_version = 1; provider = 'webcodex'; transport = 'WEBCODEX'; execution_mode = 'host_mcp_runner'
    workspace_identity = $workspaceIdentity; repository_root_identity = $workspaceIdentity
    project_id = $ProjectId; host_instance_id = $HostInstanceId; runner_instance_id = $RunnerInstanceId
    request_id = $RequestId; attached_at = $completion.completed_at; heartbeat_at = $completion.completed_at
    expires_at = $completed.AddSeconds(60).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"); ttl_seconds = 60
    capabilities = $completion.capabilities; completion_sha256 = $completionSha
    source = 'webcodex_runner_non_model_handshake'
}
$attachmentDir = Split-Path -Parent $attachmentPath
New-Item -ItemType Directory -Force -Path $attachmentDir | Out-Null
$attachmentTemp = $attachmentPath + '.tmp-' + [guid]::NewGuid().ToString('N')
[System.IO.File]::WriteAllText($attachmentTemp, ($attachment | ConvertTo-Json -Depth 8 -Compress), [System.Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $attachmentTemp -Destination $attachmentPath -Force
Write-Output (([ordered]@{ status='COMPLETED'; request_id=$RequestId; request_sha256=$requestHash; completion_sha256=$completionSha; workspace_identity=$workspaceIdentity; ttl_seconds=60; completion_count=1; side_effects=$completion.side_effects } | ConvertTo-Json -Compress))
