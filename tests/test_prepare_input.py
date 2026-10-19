import contextlib
import csv
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_input.py"
SPEC = importlib.util.spec_from_file_location("prepare_input", SCRIPT)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.xyz = "8\nDy ligand example\nH +0.000 1e-03 -0.0\nC 1.000 2 3\nDy 0 0 0\nSi 2 0 0\nN 1 0 0\nC 3 2 1\nH +0.000 1e-03 -0.0\nO 4D-1 0 0\n"
        self.atoms = mod.parse_structure(self.xyz)
        self.template = mod.read_text(mod.DEFAULT_TEMPLATE)

    def test_reordering_preserves_original_records_including_duplicates(self):
        order = mod.atom_order(self.atoms, [2], [4, 1])
        self.assertEqual(order, [2, 1, 4, 3, 7, 5, 0, 6])
        result = mod.render(self.template, self.atoms, order, 1, 6)
        actual = mod.parse_structure(result)
        self.assertEqual([a.line for a in actual], [self.atoms[i].line for i in order])
        self.assertEqual(sum(a.line == self.atoms[0].line for a in actual), 2)

    def test_same_element_order_is_stable_and_customizable(self):
        order = mod.atom_order(self.atoms, [2], [4], "O,Si")
        self.assertEqual(order, [2, 4, 7, 3, 1, 5, 0, 6])

    def test_duplicated_or_missing_indices_rejected(self):
        for order in ([0] * 8, list(range(7))):
            with self.assertRaises(ValueError):
                mod.validate_permutation(self.atoms, order)

    def test_invalid_assignments_rejected(self):
        for indices in ("0", "9", "2,2", "bad"):
            with self.assertRaises(ValueError):
                mod.parse_indices(indices, 8)
        with self.assertRaises(ValueError):
            mod.atom_order(self.atoms, [2], [2])
        with self.assertRaises(ValueError):
            mod.atom_order(self.atoms, [1], [])

    def test_bad_count_multiple_frames_and_annotations_rejected(self):
        for text in (self.xyz.replace("8\n", "9\n", 1), self.xyz + self.xyz,
                     "1\ncomment\nDy 0 0 0 extra\n", "1\ncomment\nDy NaN 0 0\n"):
            with self.assertRaises(ValueError):
                mod.parse_structure(text)

    def test_reference_noncoordinate_text_and_crlf_preserved(self):
        prefix = '! BP\r\n%geom\r\n OptimizeHydrogens true\r\nend\r\n'
        suffix = '\r\n# keep this footer\r\n'
        reference = prefix + '* xyz 0 1\r\nDy 0 0 1\r\n*' + suffix
        result = mod.render(reference, self.atoms, list(range(8)), 1, 6)
        self.assertTrue(result.startswith(prefix))
        self.assertTrue(result.endswith('*' + suffix))
        self.assertEqual([a.line for a in mod.parse_structure(result)], [a.line for a in self.atoms])

    def test_index_sensitive_settings_block_actual_reordering(self):
        order = mod.atom_order(self.atoms, [2], [4])
        for setting in ('%geom Constraints { C 0 C } end end', '%geom Scan B 0 1 = 1,2,3 end end',
                        '%basis NewGTO 0 "def2-TZVP" end end'):
            reference = setting + '\n' + self.template
            with self.assertRaisesRegex(ValueError, 'index-sensitive'):
                mod.render(reference, self.atoms, order, 1, 6)
            mod.render(reference, self.atoms, list(range(8)), 1, 6)

    def test_multiple_jobs_and_blocks_rejected(self):
        block = '* xyz 1 6\nDy 0 0 0\n*\n'
        for text in (block + block, block + '$new_job\n* xyzfile 1 6 other.xyz\n',
                     '* xyz 1 6\nDy 0 0 0\n'):
            with self.assertRaises(ValueError):
                mod.parse_structure(text)

    def test_mapping_has_both_index_conventions(self):
        order = mod.atom_order(self.atoms, [2], [4])
        rows = list(csv.DictReader(io.StringIO(mod.mapping_csv(self.atoms, self.atoms, order))))
        self.assertEqual(rows[0], dict(source_1based='3', output_1based='1',
                                      source_0based='2', output_0based='0', source_element='Dy', output_element='Dy'))
        self.assertEqual(sorted(int(row['source_1based']) for row in rows), list(range(1, 9)))

    def test_cli_unicode_paths_and_no_silent_overwrite(self):
        # Use a managed temporary directory; all artifacts are removed by the context.
        with tempfile.TemporaryDirectory(prefix='orca-test-') as directory:
            root = Path(directory)
            source, output, mapping = root / '结构.xyz', root / '结果.inp', root / '编号.csv'
            source.write_text(self.xyz, encoding='utf-8')
            args = [str(source), '--output', str(output), '--charge', '1', '--multiplicity', '6',
                    '--metal-atoms', '3', '--sphere-atoms', '2,5', '--map', str(mapping)]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(mod.main(args), 0)
                before = output.read_bytes()
                self.assertEqual(mod.main(args), 2)
            self.assertEqual(output.read_bytes(), before)
            self.assertTrue(mapping.exists())

    def test_other_metals_require_reviewed_template(self):
        with tempfile.TemporaryDirectory(prefix='orca-test-') as directory:
            root = Path(directory)
            source, output = root / 'source.xyz', root / 'output.inp'
            source.write_text('1\nexample\nTb 0 0 0\n', encoding='utf-8')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(mod.main([str(source), '--keep-order', '--output', str(output), '--charge', '3',
                                           '--multiplicity', '7']), 2)
            self.assertFalse(output.exists())

    def test_dy_to_y_preserves_all_coordinate_strings_and_other_elements(self):
        converted = mod.replace_dy_with_y(self.atoms)
        self.assertEqual(converted[2].element, 'Y')
        self.assertEqual(converted[2].line, 'Y 0 0 0')
        for old, new in zip(self.atoms, converted):
            self.assertEqual(old.xyz, new.xyz)
            if old.element != 'Dy':
                self.assertEqual(old, new)
        padded = mod.parse_atom('  Dy   +0.000  1D-3 -0.0  ')
        self.assertEqual(mod.replace_dy_with_y([padded])[0].line, '  Y   +0.000  1D-3 -0.0  ')

    def test_default_cli_converts_multiple_dy_and_orders_atoms(self):
        with tempfile.TemporaryDirectory(prefix='orca-test-') as directory:
            root = Path(directory)
            source, output, mapping = root/'source.xyz', root/'output.inp', root/'map.csv'
            source.write_text(self.xyz, encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(mod.main([str(source), '--charge', '1', '--multiplicity', '1',
                                          '--metal-atoms', '3', '--sphere-atoms', '5,8',
                                          '--output', str(output), '--map', str(mapping)]), 0)
            result = mod.read_text(output)
            atoms = mod.parse_structure(result)
            self.assertEqual([a.element for a in atoms], ['Y','N','O','Si','C','C','H','H'])
            self.assertIn('newgto Y "def2-tzvp" end', result)
            self.assertIn('* xyz 1 1', result)
            self.assertNotIn('Dy', result)
            with mapping.open(encoding='utf-8', newline='') as handle:
                first = next(csv.DictReader(handle))
            self.assertEqual((first['source_element'],first['output_element']), ('Dy','Y'))
        doubled = self.atoms + [self.atoms[2]]
        converted = mod.replace_dy_with_y(doubled)
        self.assertEqual(sum(a.element=='Y' for a in converted), 2)

    def test_custom_reference_converts_only_when_requested(self):
        with tempfile.TemporaryDirectory(prefix='orca-test-') as directory:
            root=Path(directory)
            source, template = root/'source.xyz', root/'template.inp'
            source.write_text(self.xyz, encoding='utf-8')
            template.write_text(self.template.replace('newgto Y', 'newgto Dy'), encoding='utf-8')
            for convert in (False, True):
                output=root/('y.inp' if convert else 'dy.inp')
                args=[str(source),'--template',str(template),'--keep-order','--charge','1',
                      '--multiplicity','1','--output',str(output)]
                if convert: args.append('--dy-to-y')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(mod.main(args),0)
                result=mod.read_text(output)
                element='Y' if convert else 'Dy'
                self.assertEqual(mod.parse_structure(result)[2].element, element)
                self.assertIn('newgto '+element+' "def2-tzvp" end',result)

    def test_missing_parameters_and_zero_multiplicity_rejected(self):
        with self.assertRaises(ValueError):
            mod.render(self.template, self.atoms, list(range(8)), 1, 0)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            mod.main(['source.xyz', '--output', 'output.inp'])


if __name__ == '__main__':
    unittest.main()
