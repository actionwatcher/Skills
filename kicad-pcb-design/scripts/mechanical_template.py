#!/usr/bin/env python3
"""Make an actual-size template from a KiCad board.

Use the Python interpreter that includes the pcbnew module.
The template shows the board outline and the holes in pads.
It does not show vias or copper.
"""
import argparse
import html
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--view', choices=['top', 'bottom'], default='top')
    a = parser.parse_args()
    board = a.board.expanduser().resolve()
    out = a.out.expanduser().resolve()
    if not board.is_file() or out.exists():
        parser.error('Give an existing board and a new output directory.')
    try:
        import pcbnew as p
    except ImportError:
        parser.error('Use the KiCad Python interpreter. The pcbnew module is necessary.')
    try:
        b = p.LoadBoard(str(board))
        poly = p.SHAPE_POLY_SET()
        if not b.GetBoardPolygonOutlines(poly) or poly.OutlineCount() == 0:
            raise ValueError('The board outline is not closed.')
        loops = []
        for i in range(poly.OutlineCount()):
            chains = [poly.COutline(i)] + [poly.CHole(i, j) for j in range(poly.HoleCount(i))]
            for chain in chains:
                loops.append([[p.ToMM(chain.CPoint(j).x), p.ToMM(chain.CPoint(j).y)]
                              for j in range(chain.PointCount())])
        pts = [xy for loop in loops for xy in loop]
        x0, y0 = min(x for x, y in pts), min(y for x, y in pts)
        x1, y1 = max(x for x, y in pts), max(y for x, y in pts)
        holes = []
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                drill = pad.GetDrillSize()
                if not drill.x or not drill.y:
                    continue
                pos = pad.GetPosition()
                holes.append({'reference': fp.GetReference(), 'pad': pad.GetNumber(),
                              'x_mm': p.ToMM(pos.x), 'y_mm': p.ToMM(pos.y),
                              'width_mm': p.ToMM(drill.x), 'height_mm': p.ToMM(drill.y),
                              'angle_degrees': pad.GetOrientationDegrees(),
                              'plated': pad.GetAttribute() != p.PAD_ATTRIB_NPTH})
        width, height = x1 - x0, y1 - y0
        page_w, page_h = max(110, width + 30), height + 80
        drawing = []
        for loop in loops:
            d = 'M ' + ' L '.join(f'{x:.6f},{y:.6f}' for x, y in loop) + ' Z'
            drawing.append(f'<path d="{d}" fill="none" stroke="black" stroke-width="0.10"/>')
        for h in holes:
            x, y, w, hh = h['x_mm'], h['y_mm'], h['width_mm'], h['height_mm']
            drawing.append(f'<rect x="{x-w/2:.6f}" y="{y-hh/2:.6f}" width="{w:.6f}" height="{hh:.6f}" rx="{min(w,hh)/2:.6f}" fill="none" stroke="black" stroke-width="0.05" transform="rotate({-h["angle_degrees"]:.6f} {x:.6f} {y:.6f})"/>')
            drawing.append(f'<path d="M{x-.2:.6f},{y:.6f}h.4 M{x:.6f},{y-.2:.6f}v.4" stroke="black" stroke-width="0.03"/>')
        mirror = f'translate({x0+x1:.6f},0) scale(-1,1)' if a.view == 'bottom' else ''
        title = html.escape(board.stem)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.6f}mm" height="{page_h:.6f}mm" viewBox="0 0 {page_w:.6f} {page_h:.6f}">
<rect width="100%" height="100%" fill="white"/>
<g font-family="sans-serif" fill="black">
<text x="10" y="10" font-size="4">{title}</text>
<text x="10" y="17" font-size="3">Print at 100%. Do not use fit-to-page.</text>
<text x="10" y="23" font-size="3">View: {a.view}. Board: {width:.3f} x {height:.3f} mm.</text>
<g transform="translate({15-x0:.6f},{32-y0:.6f})"><g transform="{mirror}">{''.join(drawing)}</g></g>
<path d="M15 {height+47:.6f}h50 m-50 -2v4 m50 -4v4" fill="none" stroke="black" stroke-width=".2"/>
<text x="15" y="{height+57:.6f}" font-size="3">The calibration line must measure 50.00 mm.</text>
<text x="15" y="{height+64:.6f}" font-size="3">Pad holes only. Vias are not included.</text>
</g></svg>'''
        out.mkdir(parents=True)
        (out / 'template.svg').write_text(svg)
        (out / 'print.html').write_text(f'<!doctype html><meta charset="utf-8"><title>{title}</title><style>@page{{size:{page_w}mm {page_h}mm;margin:0}}body{{margin:0}}svg{{display:block}}</style>' + svg)
        geometry = {'source': board.name, 'view': a.view, 'units': 'mm',
                    'board_bounds': [x0,y0,x1,y1], 'outline_loops': loops, 'pad_holes': holes,
                    'vias_included': False, 'curves': 'KiCad polygon approximation'}
        (out / 'geometry.json').write_text(json.dumps(geometry, indent=2) + '\n')
        print(json.dumps({'status': 'created', 'out': str(out), 'pad_holes': len(holes), 'width_mm': width, 'height_mm': height}))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
