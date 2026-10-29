"""Download the official archive into an ignored directory; never redistribute it."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://api.github.com/repos/meituan/Meituan-INFORMS-TSL-Research-Challenge'
NAME = 'all_waybill_info_meituan_0322.csv.zip'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--revision', help='Official repository commit; defaults to the recorded revision.')
    args = p.parse_args()
    manifest = ROOT / 'data/source_manifest.json'
    old = json.loads(manifest.read_text()) if manifest.exists() else {}
    revision = args.revision or old.get('revision')
    if revision is None:
        commit = subprocess.check_output(['curl', '-fsSL', REPO + '/commits/main'])
        revision = json.loads(commit)['sha']
    url = f'https://raw.githubusercontent.com/meituan/Meituan-INFORMS-TSL-Research-Challenge/{revision}/{NAME}'
    target = ROOT / 'data/private/waybills.zip'
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        subprocess.run(['curl', '-fL', '--retry', '2', '-o', str(target), url], check=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if old and not args.revision:
        assert digest == old['sha256'], 'Archive differs from recorded source; do not silently replace it.'
    record = {'publisher': 'Meituan / INFORMS TSL research challenge',
              'repository': REPO.replace('api.github.com/repos/', 'github.com/'),
              'revision': revision, 'download_url': url, 'sha256': digest,
              'license_url': f'https://github.com/meituan/Meituan-INFORMS-TSL-Research-Challenge/blob/{revision}/License.txt',
              'redistribution': 'Raw archive and order-level derivatives are not distributed here. Obtain from publisher.',
              'acknowledgment': 'This research was supported by data provided by Meituan.'}
    manifest.write_text(json.dumps(record, indent=2) + '\n')
    print('Verified official archive in ignored data/private/; revision', revision)


if __name__ == '__main__':
    main()
