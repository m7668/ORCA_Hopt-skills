---
name: molcas-smm
description: Prepare native-format MOLCAS/OpenMolcas inputs for metal-centered Dy(III) single-molecule magnets, including requested central Y-to-Dy substitution, ANO-RCC basis blocks, and the saved CASSCF-RASSI-SINGLE_ANISO protocol. Use for magnetic-anisotropy input preparation, not ORCA hydrogen optimization or general method design.
---

# MOLCAS: Dy(III) SMM Input Preparation

Prepare a `.input` file from the supplied metal-centered coordinates without changing their numeric strings. Respond in Simplified Chinese unless requested otherwise. The user-provided updated protocol is preserved; generating an input does not authorize executing its EMIL COPY/RM commands or running MOLCAS.

## Establish inputs and model

Read [references/native-workflow.md](references/native-workflow.md) when preparing or checking an input; it defines the native format, basis map, grouping, electronic model, and troubleshooting. Use [the method template](templates/Dy_SMM_CASSCF_RASSI_SINGLE_ANISO.input) for exact module settings. This is a fixed Dy(III) CAS(9e,7o) sextet protocol, not a general protocol for every metal or electronic state. A supplied working reference and explicit user choices take precedence; changes to the scientific method require a concrete reason and the user's instruction.

Establish:

- The actual coordinate source, units, central metal identity/index, and whether it has already been centered at the origin. Do not silently translate, rotate, re-optimize, or round coordinates. If it is not centered, resolve that before using the saved zero ANGM origin.
- Whether the identified central Y should be restored to Dy. Apply that substitution only when requested, including an explicit request to continue the established Y-surrogate-to-Dy workflow. Other Y atoms stay unchanged. Use electron counts for the final Dy model; do not transfer the Y Hopt multiplicity to it.
- Total charge and the intended model from user instructions or an identified reference. A matching formula alone does not establish the archived example's identity. The saved CAS(9e,7o), sextet, 21-root calculation applies to the established Dy(III) model; resolve a contradictory model before emitting those settings.
- A compatible **initial orbital file** for `lumorb`. It must match the emitted center order, basis set, modeled elements, and seven selected Dy 4f active orbitals. A Y Hopt XYZ is geometry only, not a Dy initial orbital file. The package neither supplies nor generates INPORB, nor guarantees the active orbitals by specifying `ras2=7`.

If the orbital file is available, replace `<INITIAL_ORBITAL_FILE>` with its actual filename relative to the submission directory, or use a verified reference's FILEORB/COPY configuration. If INPORB is already provided by a confirmed run setup, omit the template's COPY line and document that requirement. If its source or active-orbital selection is unknown, complete geometry/electron checks and deliver a clearly identified draft with the unresolved dependency. Do not invent an orbital filename, silently remove `lumorb`, or add SCF/guess-orbital steps as an unrequested new protocol.

## Generate native input

- Retain `&GATEWAY` and per-element `Basis set` coordinate blocks. For this saved native profile, omit XYZ-mode `Group`/`NoSym` directives. Do not remove GATEWAY to bypass parsing errors.
- Replace `<BASIS_SET_COORDINATE_BLOCKS>` with all actual atom blocks, using the reference's basis map and explicit Angstrom units. Include no absent elements or illustrative dummy atoms.
- Group by Dy, Si, O, N, F, C, H, omitting absent groups, and preserve source order within groups. A supplied reference's specific center order takes precedence, especially for orbital compatibility. The complete archived example uses Dy, N, Si, C, H; it is a case-specific order, not an alternative general default.
- Keep element-plus-source-index labels when unique after four-character truncation. Otherwise allocate short unique labels and provide a label-to-source-index map; do not claim the shortened suffix still encodes the original index.
- Recalculate `<INACTIVE_ORBITALS>` from the final composition and charge. With this all-electron, no-frozen CAS(9,7) profile, N_inactive = (sum(Z) - charge - 9)/2, which must be a nonnegative integer. For other frozen/ECP/active-space choices use the full electron accounting in the reference. Never carry `198` into a different molecule.
- Preserve module order: GATEWAY, SEWARD, RASSCF, RASSI, SINGLE_ANISO. Preserve the saved root and spin settings unless an explicitly requested method change requires coordinated updates.

## Check and deliver

Validate atom count, source-index permutation, coordinate-string multiset (including repeated records), expected symbol changes, finite coordinates, element/basis membership, unique truncated labels, closed basis blocks, center/ANGM agreement, electron accounting, and state lists. Treat repeated records as possible distinct source atoms; flag suspicious duplicates without deleting or merging them automatically. Check the orbital setup as a dependency, not a fact established by coordinate parsing.

The source-to-output element counts may differ only by the requested central Y-to-Dy replacement. Explain eight doublets as groups of spin-orbit levels, not eight RASSCF roots. All method placeholders must be resolved before describing an input as ready for submission.

Save to the requested destination or the environment's deliverable directory and link only an existing file. Briefly report formula/count, charge, spin, CAS, computed inactive orbitals, grouping/substitution, initial-orbital dependency status, and exact coordinate preservation. Report static checks separately from an actual run; claim convergence only from inspected output.

The [165 / CCDC 2558780 input](examples/165_2558780_Dy_SingleAniso.input) is preserved from the updated user archive. It has complete geometry and method sections, but requires a compatible INPORB supplied externally. It is not a self-contained initial-orbital preparation workflow or proof of convergence.
