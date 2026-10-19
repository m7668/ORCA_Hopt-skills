#!/usr/bin/env python3
"""Prepare plain Cartesian ORCA inputs without changing coordinate text."""

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import re
import sys


ELEMENTS = set("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split())
METALS = set("Li Be Na Mg Al K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv".split())
OPEN_BLOCK = re.compile(r"^\s*\*\s+xyz\s+([+-]?\d+)\s+([1-9]\d*)\s*(?:#.*)?$", re.I)
INDEXED = re.compile(r"\b(?:constraints|scan|modify_internal|fragment\w*|invertconstraints|connect|potential|pointcharges|moinp|moread|inhess|hessfile|nuclei)\b|\b(?:newgto|addgto|newecp|delecp)\s+\d+", re.I)
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "references" / "orca-template.inp"


@dataclass(frozen=True)
class Atom:
    element: str
    xyz: tuple
    line: str


def read_text(path):
    # Preserve line endings in all reference text outside the replaced block.
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def parse_atom(line):
    fields = line.split()
    if len(fields) != 4 or fields[0] not in ELEMENTS:
        raise ValueError("Expected a plain element and three coordinates; annotations are unsupported")
    try:
        values = [Decimal(x.replace("D", "E").replace("d", "e")) for x in fields[1:]]
    except InvalidOperation as exc:
        raise ValueError("Invalid coordinate number") from exc
    if not all(value.is_finite() for value in values):
        raise ValueError("Coordinates must be finite")
    return Atom(fields[0], tuple(fields[1:]), line)


def coordinate_block(text):
    if re.search(r"\$new_job|\*\s*(?:xyzfile|int)\b|%coords\b", text, re.I):
        raise ValueError("Multiple jobs and non-inline Cartesian blocks are unsupported")
    lines = text.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if OPEN_BLOCK.fullmatch(line.rstrip("\r\n"))]
    if len(starts) != 1:
        raise ValueError("Expected exactly one plain * xyz charge multiplicity block")
    start = starts[0]
    ends = [i for i in range(start + 1, len(lines)) if lines[i].strip() == "*"]
    if len(ends) != 1 or any(re.match(r"\s*\*", line) for line in lines[start + 1:ends[0]]):
        raise ValueError("Malformed or multiple coordinate blocks")
    return lines, start, ends[0]


def parse_structure(text):
    lines = text.splitlines()
    if lines and re.fullmatch(r"\s*\d+\s*", lines[0]):
        count = int(lines[0])
        if len(lines) < 2:
            raise ValueError("XYZ comment line is missing")
        records = lines[2:]
        while records and not records[-1].strip():
            records.pop()
        if len(records) != count:
            raise ValueError("XYZ atom count does not match records; multiple frames are unsupported")
    else:
        block, start, end = coordinate_block(text)
        # A source ORCA file's settings are not implicitly used as the template.
        records = [line.rstrip("\r\n") for line in block[start + 1:end]]
    if not records:
        raise ValueError("Structure must contain at least one atom")
    return [parse_atom(line) for line in records]


def parse_indices(value, count):
    if value.lower() == "none":
        return []
    try:
        indices = [int(token) - 1 for token in value.split(",")]
    except ValueError as exc:
        raise ValueError("Atom indices must be comma-separated integers, or 'none'") from exc
    if len(indices) != len(set(indices)) or any(i < 0 or i >= count for i in indices):
        raise ValueError("Atom indices must be unique and within the source structure (1-based)")
    return indices


def replace_dy_with_y(atoms):
    """Replace element tokens only; preserve spacing and coordinate strings."""
    converted = [Atom('Y', a.xyz, re.sub(r'^(\s*)Dy(?=\s)', r'\1Y', a.line))
                 if a.element == 'Dy' else a for a in atoms]
    if len(converted) != len(atoms) or any(a.xyz != b.xyz for a, b in zip(atoms, converted)):
        raise ValueError('Metal substitution changed coordinate values')
    if any(b.element != ('Y' if a.element == 'Dy' else a.element)
           for a, b in zip(atoms, converted)):
        raise ValueError('Unexpected element substitution')
    return converted


def atom_order(atoms, metal, sphere, element_order=None):
    if not metal or set(metal) & set(sphere):
        raise ValueError("Supply metal atoms and a disjoint first-sphere assignment")
    if any(atoms[i].element not in METALS for i in metal):
        raise ValueError("A selected central atom is not a metal")
    chosen = set(metal) | set(sphere)
    remaining = [i for i in range(len(atoms)) if i not in chosen]
    heavy = list(dict.fromkeys(atoms[i].element for i in remaining if atoms[i].element not in {"C", "H"}))
    if element_order:
        requested = element_order.split(",")
        if len(set(requested)) != len(requested) or any(e not in ELEMENTS or e in {"C", "H"} for e in requested):
            raise ValueError("Element order must contain unique non-C/H element symbols")
        heavy = [e for e in requested if e in heavy] + [e for e in heavy if e not in requested]
    return (sorted(metal) + sorted(sphere)
            + [i for e in heavy for i in remaining if atoms[i].element == e]
            + [i for i in remaining if atoms[i].element == "C"]
            + [i for i in remaining if atoms[i].element == "H"])


def validate_permutation(atoms, order):
    if sorted(order) != list(range(len(atoms))):
        raise ValueError("Output indices are not a permutation of the source")
    before = Counter((a.element, *a.xyz) for a in atoms)
    after = Counter((atoms[i].element, *atoms[i].xyz) for i in order)
    if before != after:
        raise ValueError("Coordinate records changed")


def render(template, atoms, order, charge, multiplicity):
    if multiplicity < 1:
        raise ValueError("Multiplicity must be positive")
    validate_permutation(atoms, order)
    if re.search(r"\$new_job|\*\s*(?:xyzfile|int)\b|%coords\b", template, re.I):
        raise ValueError("Multiple jobs and non-inline Cartesian templates are unsupported")
    has_placeholders = any(token in template for token in ("<charge>", "<multiplicity>", "<REORDERED_COORDINATE_RECORDS>"))
    if has_placeholders:
        expected = "* xyz <charge> <multiplicity>\n<REORDERED_COORDINATE_RECORDS>\n*"
        normalized = template.replace("\r\n", "\n")
        if normalized.count(expected) != 1:
            raise ValueError("Template must contain one complete placeholder coordinate block")
        start = normalized.index(expected)
        prefix, suffix = normalized[:start], normalized[start + len(expected):]
        newline = "\r\n" if "\r\n" in template else "\n"
        prefix, suffix = prefix.replace("\n", newline), suffix.replace("\n", newline)
    else:
        lines, start, end = coordinate_block(template)
        # Validate existing plain coordinates before replacing them.
        for line in lines[start + 1:end]:
            parse_atom(line.rstrip("\r\n"))
        prefix, suffix = "".join(lines[:start]), "".join(lines[end + 1:])
        # Preserve the original closing delimiter's newline in the suffix.
        suffix = ("\r\n" if lines[end].endswith("\r\n") else "\n" if lines[end].endswith("\n") else "") + suffix
        newline = "\r\n" if "\r\n" in template else "\n"
    if order != list(range(len(atoms))) and INDEXED.search(prefix + suffix):
        raise ValueError("Reference contains index-sensitive settings; resolve atom mapping before reordering")
    body = newline.join(atoms[i].line for i in order)
    result = prefix + f"* xyz {charge} {multiplicity}" + newline + body + newline + "*" + suffix
    if re.search(r"<[A-Za-z_][^>\r\n]*>", result):
        raise ValueError("Unresolved template placeholder")
    actual = parse_structure(result)
    if [a.line for a in actual] != [atoms[i].line for i in order]:
        raise ValueError("Rendered coordinate block failed verification")
    return result


def mapping_csv(source_atoms, atoms, order):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["source_1based", "output_1based", "source_0based", "output_0based", "source_element", "output_element"])
    for new, old in enumerate(order):
        writer.writerow([old + 1, new + 1, old, new, source_atoms[old].element, atoms[old].element])
    return buffer.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--charge", required=True, type=int)
    parser.add_argument("--multiplicity", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--keep-order", action="store_true", help="Retain source order instead of coordination-sphere ordering")
    parser.add_argument("--dy-to-y", action="store_true", help="Also apply Dy-to-Y substitution with a custom template")
    parser.add_argument("--metal-atoms", help="1-based source indices, comma-separated")
    parser.add_argument("--sphere-atoms", help="1-based source indices, or none")
    parser.add_argument("--element-order", help="Remaining heavy elements, e.g. Si,N,O")
    parser.add_argument("--map", type=Path, dest="mapping", help="Optional atom index mapping CSV")
    args = parser.parse_args(argv)
    try:
        source_atoms = parse_structure(read_text(args.structure))
        saved_protocol = args.template.resolve() == DEFAULT_TEMPLATE.resolve()
        atoms = replace_dy_with_y(source_atoms) if saved_protocol or args.dy_to_y else source_atoms
        if not args.keep_order:
            if args.metal_atoms is None or args.sphere_atoms is None:
                raise ValueError("Reordering requires --metal-atoms and --sphere-atoms")
            metal = parse_indices(args.metal_atoms, len(atoms))
            sphere = parse_indices(args.sphere_atoms, len(atoms))
            order = atom_order(atoms, metal, sphere, args.element_order)
        else:
            if args.metal_atoms is not None or args.sphere_atoms is not None or args.element_order:
                raise ValueError("Ordering flags cannot be combined with --keep-order")
            metal = []
            order = list(range(len(atoms)))
        if saved_protocol:
            central = metal or [i for i, a in enumerate(atoms) if a.element in METALS]
            if not central or any(atoms[i].element != "Y" for i in central):
                raise ValueError("Saved template is for Y (Dy is converted to Y); supply a reviewed --template for other metals")
        template = read_text(args.template)
        if args.dy_to_y and not saved_protocol:
            # Element-scoped basis/ECP assignments must follow the substitution.
            template = re.sub(r'(?i)(\b(?:newgto|addgto|newecp|delecp)\s+)Dy\b', r'\1Y', template)
        result = render(template, atoms, order, args.charge, args.multiplicity)
        destinations = [args.output] + ([args.mapping] if args.mapping else [])
        if len({p.resolve() for p in destinations}) != len(destinations):
            raise ValueError("Output and mapping paths must differ")
        for path in destinations:
            if path.exists():
                raise ValueError(f"Output already exists: {path}")
            if not path.parent.is_dir():
                raise ValueError(f"Output directory does not exist: {path.parent}")
        with args.output.open("x", encoding="utf-8", newline="") as handle:
            handle.write(result)
        if args.mapping:
            with args.mapping.open("x", encoding="utf-8", newline="") as handle:
                handle.write(mapping_csv(source_atoms, atoms, order))
        print(json.dumps({"output": str(args.output.resolve()), "atom_count": len(atoms),
                          "source_elements": dict(Counter(a.element for a in source_atoms)),
                          "elements": dict(Counter(a.element for a in atoms)),
                          "dy_to_y_count": sum(a.element != b.element for a, b in zip(source_atoms, atoms)),
                          "charge": args.charge, "multiplicity": args.multiplicity,
                          "reordered": order != list(range(len(atoms))),
                          "coordinates_preserved": True, "orca_executed": False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
