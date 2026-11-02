# Script procedures

Use the commands from the skill directory.
Use absolute paths for the design files and output directories.
Each command needs a new output directory.
The helpers do not change the source files.
They do not refill copper zones.

## Software

The Python helpers use Python 3.
The template helper needs the KiCad Python interpreter with `pcbnew`.
The check and export helpers need `kicad-cli`.
Use `--kicad-cli /absolute/path/kicad-cli` if necessary.

The inspection helper needs Node.js and the supplied package files.
Install its fixed dependencies from this skill directory:

```sh
npm ci --ignore-scripts
```

## Schematic and board checks

Select the inputs necessary for the task:

```sh
python3 scripts/check_design.py --schematic /absolute/path/design.kicad_sch --board /absolute/path/design.kicad_pcb --schematic-parity --out /absolute/path/checks
```

For ERC only, omit `--board` and `--schematic-parity`.
For DRC only, omit `--schematic` and `--schematic-parity`.
The parity check needs both files with the same base name.
Examine `summary.json`, the native reports, and `commands.json`.
The helper blocks the workflow if a native report contains findings.
It includes warnings and excluded findings.
Record accepted findings in the design report.
Do not describe a blocked helper result as a pass.

## Mechanical template

Use the KiCad Python interpreter in place of `python3`:

```sh
python3 scripts/mechanical_template.py --board /absolute/path/design.kicad_pcb --out /absolute/path/template --view top
```

Use `--view bottom` for a view from below.
Open `print.html` and print at 100%.
Measure the 50 mm calibration line before the fit check.
Examine `geometry.json` for the dimensions and hole data.
The template includes pad holes and board cutouts.
It does not include vias or copper.
KiCad converts outline curves to polygons for this template.
The template does not replace the component drawings.

## Manufacturing candidate

Save the board after the copper zone refill.
If a schematic exists, complete its ERC before export.

```sh
python3 scripts/validate_export.py --board /absolute/path/design.kicad_pcb --schematic-parity --out /absolute/path/candidate
```

Omit `--schematic-parity` only if the board has no maintained schematic.
The helper blocks export if the native DRC contains findings.
It exports every copper layer, both masks, both legends, the outline, and the drill files.
It prepares board fabrication data only.
Its ZIP archive is a candidate until the visual check is complete.

## Gerber and drill inspection

```sh
node scripts/inspect_manufacturing.cjs --input /absolute/path/candidate/manufacturing --out /absolute/path/inspection
```

Examine `top.svg`, `bottom.svg`, and each layer image.
Compare the outline, cutouts, holes, mask openings, and copper with the design.
The helper records parser findings and file hashes in `inspection.json`.
It blocks unknown layers, open outlines, and unsupported drill spans.
Its composite images support through holes only.
For blind or buried holes, use a viewer with drill span support.
The images do not prove electrical connectivity or manufacturing acceptance.

## Manufacturing package

After you examine the images, use `--reviewed`:

```sh
python3 scripts/package_manufacturing.py --candidate /absolute/path/candidate --inspection /absolute/path/inspection/inspection.json --out /absolute/path/package --reviewed
```

The helper compares the source, manufacturing, inspection, and DRC hashes.
It blocks files that changed after export or inspection.
It makes the manufacturing ZIP and `package.json` with the archive hash.
The source hashes cover the board and detected project files in its directory.
For external libraries or hierarchical sheets, preserve those source files separately.
If the inspection helper cannot process the files, complete and document the checks with another viewer.
Then prepare the archive and its hashes separately.
Do not bypass a failed check by changing a report.
