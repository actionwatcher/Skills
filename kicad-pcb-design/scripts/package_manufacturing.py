#!/usr/bin/env python3
"""Make a manufacturing ZIP after the file inspection.

Use --reviewed only after you examine the rendered images.
The script compares the source and export hashes before packaging.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from validate_export import digest, source_hashes, check_exports


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--inspection', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--reviewed', action='store_true')
    a = p.parse_args()
    if not a.reviewed:
        p.error('Examine the images first. Then use --reviewed.')
    out = a.out.expanduser().resolve()
    if out.exists():
        p.error('Use a new output directory.')
    try:
        candidate = a.candidate.expanduser().resolve()
        manifest = json.loads((candidate/'manifest.json').read_text())
        inspection_file = a.inspection.expanduser().resolve()
        inspection = json.loads(inspection_file.read_text())
        if inspection.get('status') != 'passed' or inspection.get('errors'):
            raise ValueError('The manufacturing inspection did not pass.')
        drc = json.loads((candidate/'native-drc.json').read_text())
        for key in ['violations','unconnected_items','schematic_parity']:
            if not isinstance(drc.get(key),list) or drc[key]:
                raise ValueError('The native DRC did not pass.')
        if digest(candidate/'native-drc.json') != manifest['native_drc_sha256']:
            raise ValueError('The DRC report changed after export.')
        sources = manifest['source_sha256']
        boards = [Path(s) for s in sources if s.endswith('.kicad_pcb')]
        if len(boards)!=1 or source_hashes(boards[0]) != sources:
            raise ValueError('The source changed after validation.')
        files = sorted((candidate/'manufacturing').iterdir())
        if any(not f.is_file() or f.is_symlink() for f in files):
            raise ValueError('The manufacturing directory must contain ordinary files only.')
        actual = {f.name:digest(f) for f in files}
        if actual != manifest['manufacturing_sha256']:
            raise ValueError('The manufacturing files changed after export.')
        reviewed = {f['name']:f['sha256'] for f in inspection['files']}
        if len(reviewed)!=len(inspection['files']) or actual != reviewed:
            raise ValueError('The inspection does not match these manufacturing files.')
        check_exports(files,manifest['board_copper_layers'])
        out.mkdir(parents=True)
        archive = out/(boards[0].stem+'-manufacturing.zip')
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for file in files:
                content = file.read_bytes()
                if hashlib.sha256(content).hexdigest() != actual[file.name]:
                    raise ValueError('The manufacturing files changed during packaging.')
                z.writestr(file.name,content)
        record = {'status':'packaged','archive':archive.name,'archive_sha256':digest(archive),
                  'manufacturing_sha256':actual,'source_sha256':sources,
                  'inspection_sha256':digest(inspection_file),'native_drc_sha256':digest(candidate/'native-drc.json'),
                  'visual_review_recorded':True,
                  'limits':'This package does not prove prototype performance or manufacturer acceptance.'}
        (out/'package.json').write_text(json.dumps(record,indent=2)+'\n')
        print(json.dumps({'status':'packaged','archive':str(archive)},indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr)
        return 2


if __name__=='__main__':
    sys.exit(main())
