# Targeted ORCA checks

Read when a basis/ECP question, indexed setting, or execution request makes these details relevant. The saved template remains the user's protocol; these checks do not authorize changing it.

## Basis and ECP

Inspect the global orbital basis, metal override, auxiliary basis, relativistic Hamiltonian (if any), and effective core potential together. ORCA's manual explicitly notes that `NewGTO` does not automatically assign the ECP in the same way as applicable global basis keywords. An inherited global ECP can also remain after a basis override. Therefore neither the presence nor absence of a `NewECP` line alone establishes correctness.

For the saved Y template, the generated structure contains Y in place of Dy, so inspect the Y basis/ECP assignment rather than retaining Dy-specific settings. Verify the actual installed ORCA version's assignment when execution or compatibility validation is requested. This package does not establish that the template has passed ORCA. For a custom ZORA/DKH or other relativistic model, check the matching orbital and auxiliary basis family as a whole.

Charge and multiplicity refer to the substituted Y model. Dy's electronic configuration and multiplicity cannot simply be transferred to Y. Use the user's explicit values; infer or discuss missing assignments from the actual modeled species. Example values in documentation are not standing defaults.

Source: [ORCA 6.1 basis sets and ECPs](https://www.faccts.de/docs/orca/6.1/manual/contents/essentialelements/basisset.html), especially assignment/adding basis functions and effective core potentials. Consult the installed version's documentation when different.

## Atom indices

Reordering geometry changes the atoms addressed by index-dependent settings. Establish reference-to-source correspondence first, then use the source-to-output mapping. Check each keyword's numbering convention in the corresponding manual; do not apply a universal offset to every ORCA keyword. A range may cease to be contiguous after reordering and need individual entries.

The helper emits both 1-based and 0-based columns. It does not rewrite indexed settings. Its token check is deliberately limited; inspect settings not covered by the supported subset.

## Hydrogen optimization and resources

`OptimizeHydrogens true` keeps the non-H skeleton fixed in an ordinary optimization. The manual notes a different interaction for fragment optimizations, so inspect fragment settings in a custom reference.

MaxCore is MB per process, rather than total job memory. Consult actual machine resources only when adapting or running the job; file preparation retains the saved values.

Sources: [ORCA 6.1 geometry optimization](https://www.faccts.de/docs/orca/6.1/manual/contents/structurereactivity/optimizations.html), [ORCA 6.1 manual, memory troubleshooting](https://www.faccts.de/docs/orca/6.1/manual/_static/pdf/orca.pdf).
