"""Validate and package only source runtime files; never read an installed profile."""
from pathlib import Path
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parent.parent
files = [
    '.agents/plugins/marketplace.json',
    'codex-plugin/.codex-plugin/plugin.json', 'codex-plugin/.mcp.json',
    'codex-plugin/assets/logo.svg', 'codex-plugin/scripts/server.mjs',
    'codex-plugin/scripts/library.mjs', 'codex-plugin/scripts/windows-actions.ps1',
    'codex-plugin/ui/app.html', 'codex-plugin/ui/translations.json',
    'README.md', 'VALIDATION.md', 'codex-plugin/LICENSE',
]
manifest = json.loads((root / files[1]).read_text(encoding='utf-8'))
version = manifest['version']
assert version == '0.1.7'
marketplace = json.loads((root / files[0]).read_text(encoding='utf-8'))
assert marketplace['plugins'][0]['source']['path'] == './codex-plugin'
json.loads((root / 'codex-plugin/.mcp.json').read_text(encoding='utf-8'))
for name in ['server.mjs', 'library.mjs']:
    subprocess.run(['node', '--check', str(root / 'codex-plugin/scripts' / name)], check=True)
result = subprocess.run(
    ['node', '--input-type=module', '-e',
     "import {tools,VERSION} from './codex-plugin/scripts/server.mjs';"
     "if(tools.some(t=>JSON.stringify(t._meta.ui.visibility)!=='[\"app\"]'))process.exit(1);"
     "console.log(VERSION)"], cwd=root, check=True, text=True, capture_output=True)
assert result.stdout.strip() == version
html = (root / 'codex-plugin/ui/app.html').read_text(encoding='utf-8')
assert 'v' + version in html and "version:'" + version + "'" in html
license_bytes = (root / 'codex-plugin/LICENSE').read_bytes()
assert license_bytes.startswith(b'MIT License')
assert b'Permission is hereby granted, free of charge' in license_bytes
assert '(codex-plugin/LICENSE)' in (root / 'README.md').read_text(encoding='utf-8')
output = root / '.test-output'
output.mkdir(exist_ok=True)
archive = output / ('codex-library-' + version + '.zip')
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for name in files:
        assert (root / name).is_file() and not (root / name).is_symlink()
        package.write(root / name, name)
    package.writestr('LICENSE', license_bytes)
with zipfile.ZipFile(archive) as package:
    assert package.namelist() == files + ['LICENSE']
    assert package.testzip() is None
    assert package.read('LICENSE') == package.read('codex-plugin/LICENSE') == license_bytes
print(json.dumps({'version': version, 'files': len(files) + 1, 'appOnly': True, 'archive': archive.name}))
