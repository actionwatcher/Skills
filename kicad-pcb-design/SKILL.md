---
name: kicad-pcb-design
description: Make or change printed circuit boards with KiCad. Use for schematics, component placement, routing, design checks, and manufacturing files.
---

# KiCad PCB Design

## Get the requirements

1. Record the circuit functions and external connections.
2. Record the voltage, current, and power requirements.
3. Record the timing, frequency, and temperature limits, as applicable.
4. Record the board dimensions and mechanical limits.
5. Identify the manufacturing and assembly requirements.
6. Get the missing information necessary for the design.

Use the user's requirements to select the components and the copper layer stack.
Do not use dimensions or circuit assumptions from another project.

## Prepare the circuit

1. Use the supplied schematic or connection list, if available.
2. If the task includes circuit design, make the schematic.
3. For unspecified parts, select the components from their electrical specifications.
4. Compare the schematic pin numbers with the component drawings.
5. Select the footprints from the specified packages.
6. Do a check of the pad dimensions and mounting dimensions.

If a schematic exists, do the electrical rule check (ERC).
Use `scripts/check_design.py` for the native ERC and DRC reports.
Read [Script procedures](references/scripts.md) before you use the helpers.
Correct the ERC errors before the board layout.
Record each result that you accept without a correction.

## Make the board

1. Use the installed KiCad software.
2. Keep the project files and the applicable design rules.
3. Make the board outline from the mechanical requirements.
4. Set the copper layer stack.
5. Set the track widths from the current requirements.
6. Set the electrical clearance limits from the voltage requirements.
7. Include the manufacturing limits in the design rules.
8. Put the components in positions that are satisfactory for the circuit and mechanical requirements.
9. Include the necessary return paths for the signals.
10. Complete the routing from the connection list and the routing requirements.
11. Do a check of the component clearances and the thermal requirements.
12. Remove copper zone intersections that cause DRC errors.
13. Refill the copper zones after a change.
14. Save the board.

For impedance limits, calculate the track dimensions from the specified layer stack.
For timing limits, apply the specified track length limits.
For special manufacturing processes, use the manufacturer's applicable limits.

If necessary, make a mechanical template at a scale of 1:1.
Use `scripts/mechanical_template.py` for the board outline and pad holes.
Include a calibration line and the direction of view.
Tell the user to do a fit check with the printed template.
Do not use a fit check as evidence of electrical performance.

## Do the design rule check

Use KiCad for the design rule check (DRC).

1. Start the export script from this skill directory:

   ```sh
   python3 scripts/validate_export.py --board /absolute/path/design.kicad_pcb --out /absolute/path/new-output
   ```

2. If necessary, give the executable path with `--kicad-cli`.
3. If the board has a schematic, include `--schematic-parity`.
4. Correct the DRC errors and the disconnected electrical connections.
5. Examine the warnings and the excluded results.
6. Record each result that you accept without a correction.
7. Do the DRC again after each correction.

If there is no schematic, compare the board connections with the connection list.
Do not decrease the design limits only to remove reported errors.
If KiCad is not available, identify the missing DRC in the report.
Keep the files in draft status until you complete this check.

A new output directory is necessary for the script.
The script stops export if the DRC reports a problem.
The script exports all copper layers.
The script does not refill the copper zones.
The script does not do the ERC.
The script prepares files for board manufacture only.

## Examine the exported files

1. Use `scripts/inspect_manufacturing.cjs` to make images from the Gerber and Excellon files.
2. Examine the board images and each layer image.
3. Do a check of the board outline and its dimensions.
4. Compare the copper layers with the specified layer stack.
5. Compare the copper connections with the schematic or connection list.
6. Do a check of the holes and the solder mask openings.
7. Make sure that the drill files and the Gerber files use the same origin.
8. Include the data for plated and non-plated holes, as applicable.
9. After a board change, prepare a new set of files.
10. Record the file hashes for the ZIP archive for manufacture.


Use another Gerber viewer if the inspection helper cannot process the files.
After the visual check, use `scripts/package_manufacturing.py` for the ZIP archive.
Use the packaged archive for the manufacturing handoff.

For a stencil, prepare the solder paste layers in different files.
For assembly, prepare the parts list and the component placement data in different files.

## Supply the results

Supply these items, as applicable:

- The editable schematic and board.
- The project files and component libraries.
- The ZIP archive for manufacture.
- The board image.
- The mechanical template.
- The parts list and assembly files.
- The results of the checks.

Identify each check that you did not complete.
Keep the order process separate from the design work.
