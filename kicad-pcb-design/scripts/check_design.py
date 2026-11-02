#!/usr/bin/env python3
"""Do the schematic and board checks with KiCad.

Use a new output directory.
The script does not change the source files.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def count_erc(data):
    if not isinstance(data.get('sheets'), list):
        raise ValueError('The ERC report has an unknown format.')
    count = 0
    for sheet in data['sheets']:
        if not isinstance(sheet.get('violations'), list):
            raise ValueError('The ERC report has an unknown sheet format.')
        count += len(sheet['violations'])
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', type=Path)
    p.add_argument('--schematic', type=Path)
    p.add_argument('--schematic-parity', action='store_true')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--kicad-cli', default='kicad-cli')
    a = p.parse_args()
    inputs = {k: v.expanduser().resolve() for k, v in [('board', a.board), ('schematic', a.schematic)] if v}
    if not inputs or any(not f.is_file() for f in inputs.values()):
        p.error('Give an existing board or schematic file.')
    if a.schematic_parity and ('board' not in inputs or inputs.get('schematic') != inputs['board'].with_suffix('.kicad_sch')):
        p.error('The parity check needs a board and a schematic with the same base name.')
    out = a.out.expanduser().resolve()
    if out.exists():
        p.error('Use a new output directory.')
    cli = shutil.which(a.kicad_cli)
    if not cli:
        p.error('KiCad CLI is not available. Use --kicad-cli.')
    out.mkdir(parents=True)
    env = os.environ.copy()
    env.setdefault('KICAD_CONFIG_HOME', str(out / '_kicad-config'))
    results = {}
    commands = []
    try:
        for kind, file in inputs.items():
            check = 'erc' if kind == 'schematic' else 'drc'
            report = out / (check + '.json')
            cmd = [cli, 'sch' if check == 'erc' else 'pcb', check,
                   '--format', 'json', '--severity-all', '--output', str(report)]
            if check == 'drc' and a.schematic_parity:
                cmd.append('--schematic-parity')
            cmd.append(str(file))
            run = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)
            commands.append({'argv': cmd, 'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr})
            (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
            if run.returncode:
                raise RuntimeError('KiCad stopped. Read commands.json.')
            data = json.loads(report.read_text())
            if check == 'erc':
                results[check] = {'violations': count_erc(data)}
            else:
                keys = ['violations', 'unconnected_items', 'schematic_parity']
                if any(not isinstance(data.get(k), list) for k in keys):
                    raise ValueError('The DRC report has an unknown format.')
                results[check] = {k: len(data[k]) for k in keys}
        blocked = any(n for group in results.values() for n in group.values())
        summary = {'status': 'blocked' if blocked else 'passed', 'checks': results,
                   'schematic_parity_requested': a.schematic_parity,
                   'zone_refill_performed': False}
        (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))
        return 3 if blocked else 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
