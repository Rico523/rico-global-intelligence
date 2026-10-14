"""Fail closed before upload if data limits/schema or static file bounds fail."""
import json
from collect import ROOT, MAX_JSON, validate_payload

def main():
    site = ROOT / 'site'
    size = 0
    for file in site.rglob('*'):
        if file.is_symlink():
            raise ValueError('No symlinks in deployment')
        if not file.is_file():
            continue
        size += file.stat().st_size
        if file.suffix == '.json':
            if file.stat().st_size > MAX_JSON:
                raise ValueError('JSON too large')
            if file.is_relative_to(site / 'data'):
                validate_payload(json.loads(file.read_text()))
            else:
                json.loads(file.read_text())
    if len(list((site / 'data/history').glob('*.json'))) > 2 or size > 4_000_000:
        raise ValueError('Deployment/history size limit')
    print(f'Static payload validated: {size} bytes')

if __name__ == '__main__':
    main()
