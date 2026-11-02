#!/usr/bin/env python3
"""Use KiCad for the design rule check before export.

The script uses the Python standard library.
The script does not change the source board.
Examine the exported files before manufacture.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copper_layers(board):
    """Read only the board-level layer table, independent of KiCad ordinal changes."""
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', board.read_text())
    depth = 0
    for index, token in enumerate(tokens):
        if token == '(':
            depth += 1
            if depth == 2 and tokens[index + 1] == 'layers':
                break
        elif token == ')':
            depth -= 1
    else:
        raise ValueError('Board-level layer table not found')
    found = []
    level = 0
    for offset in range(index, len(tokens)):
        token = tokens[offset]
        if token == '(':
            level += 1
            if level == 2:
                name = tokens[offset + 2].strip('"')
                if name.endswith('.Cu'):
                    if not re.fullmatch(r'F\.Cu|B\.Cu|In[1-9][0-9]?\.Cu', name):
                        raise ValueError('Unrecognized copper layer: ' + name)
                    found.append(name)
        elif token == ')':
            level -= 1
            if level == 0:
                break
    if len(found) != len(set(found)) or 'F.Cu' not in found or 'B.Cu' not in found:
        raise ValueError('Incomplete or duplicate copper layer table')
    return sorted(found, key=lambda n: 0 if n == 'F.Cu' else 100 if n == 'B.Cu' else int(n[2:-3]))


def check_exports(files, layers):
    functions = []
    for file in files:
        if file.suffix != '.drl' and file.suffix != '.gbrjob':
            matches = re.findall(r'%TF\.FileFunction,([^*]+)\*%', file.read_text())
            if len(matches) != 1:
                raise ValueError('Missing or ambiguous Gerber X2 layer identity: ' + file.name)
            functions.extend(matches)
    expected = {f'Copper,L{i},{"Top" if name == "F.Cu" else "Bot" if name == "B.Cu" else "Inr"}'
                for i, name in enumerate(layers, 1)}
    actual = [f for f in functions if f.startswith('Copper,')]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError('Exported copper layers do not match the board layer stack')
    required = {'Soldermask,Top', 'Soldermask,Bot', 'Legend,Top', 'Legend,Bot'}
    if not required.issubset(functions) or not any(f.startswith('Profile,') for f in functions):
        raise ValueError('Incomplete mask, legend or outline exports')
    return functions


def source_hashes(board):
    base = board.parent
    paths = [board]
    paths += [board.with_suffix(ext) for ext in ('.kicad_pro', '.kicad_dru', '.kicad_sch')]
    paths += [base / 'fp-lib-table', base / 'sym-lib-table']
    paths += list(base.glob('*.pretty/*.kicad_mod'))
    paths += list(base.glob('*.kicad_sym'))
    return {str(p.resolve()): digest(p) for p in sorted(set(paths)) if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path, help='New output directory; must not already exist')
    parser.add_argument('--kicad-cli', default='kicad-cli', help='CLI executable name or absolute path')
    parser.add_argument('--schematic-parity', action='store_true', help='Check the corresponding maintained schematic too')
    args = parser.parse_args()
    board = args.board.expanduser().resolve()
    out = args.out.expanduser().resolve()
    if board.suffix != '.kicad_pcb' or not board.is_file():
        parser.error('--board must name an existing .kicad_pcb file')
    if out.exists():
        parser.error('--out must be new, to avoid stale exports')
    cli = shutil.which(args.kicad_cli)
    if not cli:
        parser.error('KiCad CLI not found; provide --kicad-cli. Nothing was installed.')
    if args.schematic_parity and not board.with_suffix('.kicad_sch').is_file():
        parser.error('--schematic-parity requires the corresponding .kicad_sch file')
    before = source_hashes(board)
    try:
        layers = copper_layers(board)
    except (ValueError, IndexError) as error:
        parser.error(str(error))
    out.mkdir(parents=True)
    env = os.environ.copy()
    env.setdefault('KICAD_CONFIG_HOME', str(out / '_kicad-config'))
    commands = []

    def run(arguments):
        command = [cli] + arguments
        result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=180)
        commands.append({'argv': command, 'exit_code': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        if result.returncode:
            raise RuntimeError('KiCad command failed; see commands.json')
        return result

    try:
        version = run(['version']).stdout.strip()
        report = out / 'native-drc.json'
        drc = ['pcb', 'drc', '--format', 'json', '--severity-all', '--output', str(report)]
        if args.schematic_parity:
            drc.append('--schematic-parity')
        run(drc + [str(board)])
        data = json.loads(report.read_text())
        required = ('violations', 'unconnected_items', 'schematic_parity')
        if any(key not in data or not isinstance(data[key], list) for key in required):
            raise RuntimeError('Unrecognized DRC schema; inspect report and adapt to installed KiCad version')
        findings = {key: len(data[key]) for key in required}
        if any(findings.values()):
            print(json.dumps({'status': 'blocked', 'findings': findings, 'report': str(report)}, indent=2))
            return 3
        fab = out / 'manufacturing'
        fab.mkdir()
        run(['pcb', 'export', 'gerbers', '--output', str(fab), '--layers',
             ','.join(layers + ['F.Mask', 'B.Mask', 'F.Silkscreen', 'B.Silkscreen', 'Edge.Cuts']),
             '--exclude-refdes', '--exclude-value', str(board)])
        run(['pcb', 'export', 'drill', '--output', str(fab), '--format', 'excellon',
             '--drill-origin', 'absolute', '--excellon-units', 'mm',
             '--excellon-zeros-format', 'decimal', '--excellon-separate-th', str(board)])
        files = sorted(p for p in fab.iterdir() if p.is_file())
        if not files or not any(p.suffix == '.drl' for p in files):
            raise RuntimeError('Expected manufacturing/drill output was not created')
        functions = check_exports(files, layers)
        after = source_hashes(board)
        if before != after:
            raise RuntimeError('Source files changed during validation/export; rerun from the final saved state')
        archive = out / (board.stem + '-manufacturing-candidate.zip')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for file in files:
                z.write(file, file.name)
        manifest = {
            'status': 'candidate: independent Gerber/drill review and relevant fit confirmation still required',
            'kicad_version': version,
            'native_drc': findings,
            'native_drc_sha256': digest(report),
            'schematic_parity_requested': args.schematic_parity,
            'board_copper_layers': layers,
            'exported_file_functions': functions,
            'zone_refill_performed_by_script': False,
            'source_sha256': before,
            'manufacturing_sha256': {p.name: digest(p) for p in files},
            'archive': archive.name,
            'archive_sha256': digest(archive),
        }
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        print(json.dumps({'status': 'candidate created', 'archive': str(archive), 'manifest': str(out / 'manifest.json')}, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print('Validation/export stopped: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
