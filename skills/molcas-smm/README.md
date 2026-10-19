# MOLCAS Skill

This package defines a repeatable workflow for preparing OpenMolcas inputs for Dy(III) single-molecule magnets from metal-centered coordinates.

Codex invocation: `$molcas-smm`; display name: `MOLCAS`. Install this directory as `~/.codex/skills/molcas-smm`, independently of the ORCA Hopt skill in this repository.

## Contents

- `SKILL.md` — entry point, required inputs, and validation/delivery boundaries.
- `references/native-workflow.md` — updated user protocol, basis mapping, electron-count rules, and troubleshooting.
- `templates/Dy_SMM_CASSCF_RASSI_SINGLE_ANISO.input` — reusable CASSCF/RASSI/SINGLE_ANISO method template.
- `examples/165_2558780_Dy_SingleAniso.input` — full native-format example for the 165 / CCDC 2558780 coordinate set.

## Important format rule

The package uses **native MOLCAS input**: `&GATEWAY` followed by per-element `Basis set` coordinate blocks. Do not add `Group`/`NoSym` to this native format, and never remove `&GATEWAY` when troubleshooting. Mixing `Group` with native basis blocks can produce `COORD keyword is not found`; omitting `&GATEWAY` can leave SEWARD without the runfile records it needs and lead to `iArray labels` errors.

## Use

Provide the metal-centered coordinate file and request the `MOLCAS` workflow. The skill groups coordinates into per-element basis blocks while preserving original coordinate values and source atom indices, then builds and validates the input.

`lumorb` requires a compatible initial orbital file, normally `INPORB`, with the seven intended Dy 4f active orbitals established. Neither the method template nor the complete-coordinate example supplies that file. Provide the actual orbital source or a confirmed external setup that supplies INPORB; without it, generated input remains a draft with an unresolved runtime dependency. No SCF or alternative orbital-preparation method is added automatically.

The method template contains `<BASIS_SET_COORDINATE_BLOCKS>`, `<INITIAL_ORBITAL_FILE>`, and `<INACTIVE_ORBITALS>` placeholders. Resolve all three for the current job. If the run setup already supplies INPORB, remove the template COPY line and record that setup instead of inventing a file. The archived example is preserved as supplied; its example-specific `Inactive=198` is not a default for new structures.

The saved Dy(III) method uses CAS(9e,7o), spin 6, and 21 equally weighted sextet roots. Charge +1 and `Inactive = 198` belong to the established all-electron example `DySi5C32NH71`, not every Dy(III) complex. Recalculate inactive orbitals for each modeled composition and charge. The eight SINGLE_ANISO doublets are groups of spin-orbit levels and need not equal 21 spin-free roots.

## References

- [MOLCAS 8.17 GATEWAY manual](https://www.molcas.org/documentation/manual/node85.html)
- [MOLCAS 8 SEWARD manual](https://www.molcas.org/documentation/manual/node113.html)
- [SINGLE_ANISO tutorial](https://gitlab.com/Molcas/doc/-/blob/master/source/tutorials/tut_single_aniso.rst)
