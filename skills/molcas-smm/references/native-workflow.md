# MOLCAS: Dy(III) SMM Input Preparation

## Goal

Generate a reproducible OpenMolcas input for a Dy(III) single-molecule magnet (SMM) from a metal-centered coordinate file. Preserve every supplied coordinate value unless the user explicitly requests a geometry change. Follow the user's reference calculation rather than silently changing the computational protocol.

## Critical input-format rule

The established workflow uses **native MOLCAS coordinate input**, not XYZ mode. The input must begin with `&GATEWAY`, followed by one or more `Basis set` blocks. Each block contains a basis label, atom labels with Cartesian coordinates, and `End of basis`.

Use this structure:

```text
&GATEWAY
Basis set
Dy.ANO-RCC-VTZP
Dy1       0.00000     0.00000     0.00000   Angstrom
End of basis

* Add one Basis set block for every other element present.

ANGM
0.000 0.000 0.000

&SEWARD
...
```

**Do not put `Group`, `Group = NoSym`, or `NoSym` in this native-format input.** In MOLCAS 8, `Group` belongs to the XYZ-style GATEWAY mode; mixing it with native `Basis set` coordinate blocks can make GATEWAY expect a `COORD` keyword and stop with `COORD keyword is not found`. For native input, omit symmetry directives when no symmetry is intended; the default is no symmetry.

**Never remove `&GATEWAY` to work around a GATEWAY parsing error.** If the marker is omitted, GATEWAY may be skipped and SEWARD can stop with a missing runfile record such as `Record not found in runfile: iArray labels`. Fix the input mode while retaining the module marker.

Do not mix native coordinate blocks with XYZ-mode `COORD`/`BASIS` directives. If switching to XYZ mode is explicitly requested, convert the entire geometry and basis specification consistently instead of mixing modes.

## Default use case

The established method targets a Dy(III) CAS(9e,7o) model followed by RASSI and SINGLE_ANISO. The user-supplied example is labeled 165 / CCDC 2558780 and has composition `Dy1 Si5 C32 N1 H71` (110 atoms), charge `+1`, and spin multiplicity `6`.

Reuse these case assignments only when the user or an identified reference establishes the same modeled species; matching composition alone does not establish identity. Reassess charge, spin, active space, and inactive orbitals for different compositions, counterions, oxidation states, or electronic states.

## Inputs

- Coordi-transformed coordinates, usually with the metal at `(0, 0, 0)`.
- A reference OpenMolcas input or the method/basis settings specified below.
- A compatible initial orbital file for `lumorb` (see the entry point). Its origin, center/basis ordering, and selected Dy 4f active orbitals must be established. This package does not supply that file.
- Optional compound label, CCDC number, charge, spin state, or requested calculation changes.

A coordinate source may begin with an atom count and a comment/formula line. Treat those as metadata, not atoms. Each coordinate record must contain an element and three finite Cartesian coordinates in Angstrom.

## Workflow

### 1. Parse and validate the structure

1. Read all coordinate records and preserve their numeric strings exactly.
2. Confirm the declared atom count matches the parsed records.
3. Identify the central metal using the source and user instruction, not atom order alone.
4. If the source claims to be metal-centered, confirm the central metal is at the origin. Do not translate or rotate it automatically; report the discrepancy or ask before changing coordinates.
5. Count atoms by element and compare with any supplied formula.
6. Check for missing records, duplicated atoms, malformed coordinates, and unsupported elements.

### 2. Convert the central Y label to Dy when requested

For the established Y-to-Dy surrogate workflow:

- Change only the identified central atom symbol from `Y` to `Dy`.
- Keep its coordinates and every other atom's coordinates unchanged.
- Do not alter ligand coordinates, rotate the structure, optimize the geometry, or remove atoms.
- Reassess charge, spin, electron count, and active-space assumptions after the substitution.

Do not replace any other Y atom unless the user explicitly requests it.

### 3. Assign basis sets and group coordinate records

Use the reference basis mapping:

| Element | Basis set |
|---|---|
| Dy | `ANO-RCC-VTZP` |
| Si | `ANO-RCC-VDZP` |
| O | `ANO-RCC-VDZP` |
| N | `ANO-RCC-VDZP` |
| F | `ANO-RCC-VDZ` |
| C | `ANO-RCC-VDZ` |
| H | `ANO-RCC-VDZ` |

Rules:

- Emit one `Basis set` block for each element present; never emit an empty block.
- Use labels such as `Dy.ANO-RCC-VTZP` and close every block with `End of basis`.
- Give each atom a unique label based on its original source index, such as `Dy1`, `N2`, `C3`, `Si8`. The numeric suffix must retain the original atom index even when coordinate records are regrouped.
- MOLCAS truncates center labels to four characters. Ensure labels remain unique after truncation; for structures with more atoms than can be uniquely represented by the simple element-plus-index scheme, generate and validate short unique labels.
- Preserve the relative source order within each element group.
- Use the reference block order `Dy, Si, O, N, F, C, H`, omitting absent elements.
- Write `Angstrom` on coordinate records so coordinates are not interpreted as Bohr.
- If an element is not covered by the mapping, use a basis supplied by the user or ask; do not invent one.

### 4. Determine charge, spin, and active space

For the established Dy(III) CAS(9e,7o) model:

```text
spin = 6
Nactel = 9 0 0
ras2 = 7
ciroot = 21,21,1
```

Dy(III) has nominal `4f^9` configuration and the free-ion ground term `6H15/2`. For this standard high-spin model, use multiplicity 6. `Nactel = 9 0 0` specifies nine active electrons, a maximum of zero holes in RAS1 and zero electrons in RAS3; the absence of RAS1/RAS3 orbitals makes this a CAS setup; `ras2 = 7` selects seven active orbitals.

For the all-electron cation `DySi5C32NH71` with total charge `+1`:

- Nuclear-charge sum: `66 + 5*14 + 32*6 + 7 + 71 = 406`.
- Electron count: `406 - 1 = 405`.
- Inactive doubly occupied orbitals: `(405 - 9) / 2 = 198`.

Thus, for this exact all-electron composition and CAS(9e,7o) model:

```text
Inactive = 198
```

`Inactive` counts doubly occupied orbitals, not inactive electrons. Recalculate it for each new composition, charge, basis/Hamiltonian treatment, or active-space choice. The arithmetic above assumes an all-electron calculation, no frozen orbitals, and all electrons outside the active space paired. If a reference contains frozen orbitals, use N_e = 2*N_frozen + 2*N_inactive + N_active; adjust for any ECP treatment rather than using the no-frozen shortcut.

### 5. Build the input modules in order

The complete input must retain every module marker and run in this order:

1. `&GATEWAY` — native basis-set coordinate blocks and `ANGM` origin.
2. `&SEWARD` — integral generation, including `AMFI`, `DOUG`, and the reference Cholesky settings.
3. `&RASSCF` — CAS(9e,7o) roots.
4. `&RASSI` — spin-orbit state interaction and angular-momentum matrix elements.
5. `&SINGLE_ANISO` — magnetic anisotropy analysis.

The `ANGM` origin must coincide with the magnetic center. For a single Dy center placed at `(0,0,0)`, use `ANGM` coordinates `0.000 0.000 0.000`. `ANGM` can be specified in GATEWAY or SEWARD in this MOLCAS workflow; keep it in the reference location unless a version-specific reason requires a change.

Use the supplied [method template](../templates/Dy_SMM_CASSCF_RASSI_SINGLE_ANISO.input) as the source of module settings. Replace its coordinate-block, initial-orbital-file, and inactive-orbital placeholders for the actual job; it is not directly runnable while they remain unresolved.

The method uses `ciroot = 21,21,1`: average the 21 lowest sextet roots with equal weights. `LROOTS` specifies the starting CI-matrix dimension, rather than an additional state multiplicity. With 21 sextet roots, the spin-component space supplied to spin-orbit interaction has dimension 21*6=126. SINGLE_ANISO's `mltp` selects eight groups of dimension 2 (16 spin-orbit levels); it need not equal the count of spin-free roots. Do not add other spin multiplicities or change the scientific protocol without a requested change.

If the number of RASSCF roots or the spin-orbit state list changes, revisit the RASSI and SINGLE_ANISO sections instead of leaving inconsistent counts.

Use a distinct `Project` and work directory for each independent run. Do not reuse stale `RUNFILE`, `JobIph`, or `JOB001` data from another structure.

### 6. Validate before delivery

Before returning the input file, check all of the following:

1. The input starts with `&GATEWAY` and retains it.
2. The input uses native `Basis set` blocks consistently and does not contain `Group`, `Group = NoSym`, or `NoSym` directives in this native mode.
3. Atom count matches the source. After an explicitly requested central Y-to-Dy substitution, Dy increases by one and Y decreases by one; other element counts are unchanged.
4. Every source coordinate appears exactly once and is numerically unchanged; the only permitted symbol change in the Y-to-Dy workflow is the identified central atom.
5. Every element has the intended basis set; all blocks have `End of basis`.
6. Atom labels are unique after MOLCAS's four-character truncation.
7. The central Dy coordinates and `ANGM` origin agree.
8. Charge, spin, `Nactel`, `ras2`, and `Inactive` match the chemical/electron-count model.
9. RASSI root count, `JobIph` count, state index list, and SINGLE_ANISO state list are consistent.
10. All intended modules occur in order: GATEWAY, SEWARD, RASSCF, RASSI, SINGLE_ANISO.
11. Distinguish static input validation from an actual OpenMolcas run. Never claim that a module converged unless the output log confirms it.

## Troubleshooting from observed logs

### `COORD keyword is not found` in GATEWAY

Likely cause in this workflow: native `Basis set` blocks were combined with the XYZ-mode `Group`/`NoSym` directive. Remove `Group`/`NoSym`, retain `&GATEWAY`, and keep the native basis-block coordinates. Do not add an XYZ `COORD` block unless converting the entire input to XYZ mode.

### `Record not found in runfile: iArray labels` in SEWARD

First inspect the submitted input. If `&GATEWAY` is missing or GATEWAY did not complete, restore/fix that module and confirm it runs before SEWARD. This error can occur when SEWARD starts without the runfile records produced by GATEWAY. Use a fresh project/work directory after correcting the input to avoid stale intermediate files.

### GATEWAY succeeds but SEWARD still fails

Do not change the molecular coordinates blindly. Check basis labels, unique center labels, every `End of basis`, ANGM placement/origin, module boundaries, and compatibility with the installed MOLCAS version. Diagnose from the first failing module and its first error message.

## Deliverables

- Save a complete `.input` file with a structure label, e.g. `165_2558780_Dy_SingleAniso.input`.
- Provide a grouped coordinate-only file only if requested.
- Report formula/atom count, charge, spin, active space, inactive-orbital calculation, basis assignment, and assumptions.
- State explicitly that coordinates were preserved and whether OpenMolcas was actually run.

## Default concise response

“已生成 `<name>.input`。使用原生 MOLCAS `&GATEWAY` + `Basis set` 坐标块格式，坐标数值保持不变；已检查原子数量、元素计数、基组分配、电子数、活性空间及 RASSI/SINGLE_ANISO 状态数。当前只完成静态输入校验，未运行 OpenMolcas。”

## References

- MOLCAS 8.17 GATEWAY manual (native input vs XYZ mode): https://www.molcas.org/documentation/manual/node85.html
- MOLCAS 8 SEWARD manual: https://www.molcas.org/documentation/manual/node113.html
- SINGLE_ANISO tutorial (AMFI, DOUG, ANGM, RASSI MEES/SPIN): https://gitlab.com/Molcas/doc/-/blob/master/source/tutorials/tut_single_aniso.rst
