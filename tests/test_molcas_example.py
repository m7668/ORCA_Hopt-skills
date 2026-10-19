"""Independent static checks of the user-supplied native MOLCAS example."""

from collections import Counter
from decimal import Decimal
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'skills/molcas-smm/examples/165_2558780_Dy_SingleAniso.input'


class MolcasExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = EXAMPLE.read_text(encoding='utf-8')
        cls.records = []
        cls.bases = []
        basis = None
        expect_basis = False
        for raw in cls.text.splitlines():
            line = raw.strip()
            if line.lower() == 'basis set':
                if basis is not None:
                    raise ValueError('Nested basis blocks')
                expect_basis = True
            elif expect_basis:
                basis = line
                cls.bases.append(basis)
                expect_basis = False
            elif line.lower() == 'end of basis':
                if basis is None:
                    raise ValueError('Unmatched basis block terminator')
                basis = None
            elif basis:
                fields = line.split()
                if len(fields) != 5 or fields[4].lower() != 'angstrom':
                    raise ValueError('Expected native Angstrom atom record')
                label, x, y, z, _ = fields
                element, index = re.fullmatch(r'([A-Z][a-z]?)(\d+)', label).groups()
                if not all(Decimal(v).is_finite() for v in (x, y, z)):
                    raise ValueError('Nonfinite coordinate')
                cls.records.append((element, int(index), label, (x, y, z), basis))
        if basis is not None or expect_basis:
            raise ValueError('Unclosed basis block')

    def test_geometry_labels_and_basis_membership(self):
        self.assertEqual(len(self.records), 110)
        self.assertEqual(Counter(r[0] for r in self.records), dict(Dy=1, Si=5, C=32, N=1, H=71))
        self.assertEqual(sorted(r[1] for r in self.records), list(range(1, 111)))
        self.assertEqual(len({r[2][:4].upper() for r in self.records}), 110)
        expected = dict(Dy='VTZP', Si='VDZP', N='VDZP', C='VDZ', H='VDZ')
        for element, _, _, _, basis in self.records:
            self.assertEqual(basis, element+'.ANO-RCC-'+expected[element])
        center = [r for r in self.records if r[0] == 'Dy'][0]
        self.assertEqual(tuple(map(Decimal, center[3])), (0, 0, 0))
        self.assertRegex(self.text, r'(?i)angm\s+0\.000\s+0\.000\s+0\.000')

    def test_electron_accounting(self):
        nuclear_charges = dict(Dy=66, Si=14, C=6, N=7, H=1)
        zsum = sum(nuclear_charges[r[0]] for r in self.records)
        inactive = int(re.search(r'(?i)\bInactive\s+(\d+)', self.text)[1])
        active = int(re.search(r'(?i)\bNactel\s+(\d+)', self.text)[1])
        self.assertEqual(zsum, 406)
        self.assertEqual(zsum - (2*inactive + active), 1)
        self.assertEqual(active, 9)

    def test_module_and_state_lists(self):
        modules = re.findall(r'(?im)^\s*&([a-z_]+)', self.text)
        self.assertEqual([m.upper() for m in modules], ['GATEWAY','SEWARD','RASSCF','RASSI','SINGLE_ANISO'])
        self.assertNotRegex(self.text, r'(?im)^\s*(?:Group\b|NoSym\b|COORD\b)')
        self.assertRegex(self.text, r'(?i)ciroot\s+21,21,1')
        match = re.search(r'(?i)Nr of JobIph\s*\n\s*1\s+(\d+)\s*\n([^\n]+)', self.text)
        count, roots = int(match[1]), list(map(int, match[2].split()))
        self.assertEqual(roots, list(range(1, count+1)))
        self.assertEqual(count, 21)
        match = re.search(r'(?i)mltp\s*\n\s*(\d+)\s*\n([^\n]+)', self.text)
        groups = list(map(int, match[2].split()))
        self.assertEqual(len(groups), int(match[1]))
        self.assertEqual(groups, [2]*8)
        self.assertLessEqual(sum(groups), count*6)


if __name__ == '__main__':
    unittest.main()
