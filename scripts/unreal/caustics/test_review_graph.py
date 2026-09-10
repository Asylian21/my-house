"""CPU graph controls, plus read-only checks of retained native graph evidence."""
from pathlib import Path
import json, tempfile, unittest
import review_graph as R


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.E = Path(self.tmp.name).resolve() / 'UE'
        self.P = self.E / '.brezi-managed/new/Project/BreziTwin'
        self.wd = self.E / 'Engine/Source'
        self.plugin = self.P / 'Plugins/BreziCausticsProbe'
        self.wd.mkdir(parents=True)
        self.plugin.mkdir(parents=True)
        self.header = self.plugin / 'Intermediate/Definitions.BreziCausticsProbe.h'
        self.header.parent.mkdir()
        self.header.write_text('#define BREZI_HAS_FLOOR_CAUSTICS_API 1\n')
        self.cpp = self.plugin / 'Private.cpp'
        self.cpp.write_text('// provider source\n')
        self.obj = self.plugin / 'Intermediate/provider.cpp.o'
        self.bin = self.P / 'Binaries/Mac/BreziTwin'
        self.doc = {'Actions': [self.action(0, 'Compile', ['-c', '-include', str(self.header), str(self.cpp), '-o', str(self.obj)], [str(self.obj)], []),
                                self.action(1, 'Link', [str(self.obj), '-o', str(self.bin)], [str(self.bin)], [0])]}

    def action(self, i, kind, tokens, outputs, deps):
        import shlex
        rsp = self.plugin / ('action%d.rsp' % i)
        lines = [shlex.quote(t) for t in tokens]
        rsp.write_text('\n'.join(lines))
        return {'Id': i, 'Type': kind, 'WorkingDirectory': str(self.wd),
                'CommandPath': '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++',
                'CommandArguments': '@' + shlex.quote(str(rsp)), 'ResponseFileContents': lines,
                'ProducedItems': outputs, 'DeleteItems': [], 'PrerequisiteActions': deps}

    def result(self):
        return R.review(self.doc, self.E, self.P, R.sha(json.dumps(self.doc).encode()))

    def rejects(self, text):
        result = self.result()
        self.assertEqual(result['status'], 'failed')
        self.assertIn(text, json.dumps(result['issues']))

    def test_provider_object_and_link_pass(self):
        result = self.result()
        self.assertEqual(result['issues'], [])
        self.assertEqual(result['providerCompileActions'][0]['linkActions'], [1])
        self.assertEqual(result['sharedEngineProducedPaths'], [])

    def test_api_zero_duplicate_and_missing(self):
        for contents in ('#define BREZI_HAS_FLOOR_CAUSTICS_API 0', '', '#define BREZI_HAS_FLOOR_CAUSTICS_API 1\n#define BREZI_HAS_FLOOR_CAUSTICS_API 0'):
            self.header.write_text(contents)
            self.rejects('Provider API definition')
        self.header.unlink()
        self.rejects('Missing generated/source input')

    def test_rsp_drift(self):
        (self.plugin / 'action0.rsp').write_text('-c old.cpp')
        self.rejects('Response file differs')

    def test_foreign_output_and_symlink_escape(self):
        self.doc['Actions'][0]['ProducedItems'].append('/tmp/foreign.o')
        self.rejects('Foreign ProducedItems')
        alias = self.plugin / 'escape'
        alias.symlink_to(Path(self.tmp.name))
        self.doc['Actions'][0]['ProducedItems'][-1] = str(alias / 'foreign.o')
        self.rejects('Foreign ProducedItems')

    def test_old_project_not_allowed_as_shared_engine(self):
        old = self.E / '.brezi-managed/old/Project/BreziTwin'
        self.doc['Actions'][0]['WorkingDirectory'] = str(old)
        self.rejects('Foreign working directory')

    def test_duplicate_ids_and_products(self):
        self.doc['Actions'][1]['Id'] = 0
        with self.assertRaisesRegex(ValueError, 'Duplicate/invalid'):
            self.result()
        self.doc['Actions'][1]['Id'] = 1
        self.doc['Actions'][1]['ProducedItems'].append(str(self.obj))
        self.rejects('Duplicate produced path')

    def test_missing_edges_and_cycle(self):
        self.doc['Actions'][1]['PrerequisiteActions'] = [99]
        self.rejects('Missing/self/duplicate')
        self.doc['Actions'][1]['PrerequisiteActions'] = [0]
        self.doc['Actions'][0]['PrerequisiteActions'] = [1]
        self.rejects('Cyclic or unresolved')

    def test_link_response_and_edge_both_required(self):
        self.doc['Actions'][1]['PrerequisiteActions'] = []
        self.rejects('Provider object absent')
        self.doc['Actions'][1] = self.action(1, 'Link', ['-o', str(self.bin)], [str(self.bin)], [0])
        self.rejects('Provider object absent')

    def test_cache_only_is_not_claimed_as_provider_compile(self):
        self.doc['Actions'] = [self.action(1, 'Link', [str(self.obj), '-o', str(self.bin)], [str(self.bin)], [])]
        self.rejects('No provider compile action')

    def test_wrong_compiler_and_unlisted_output(self):
        self.doc['Actions'][0]['CommandPath'] = '/bin/sh'
        self.rejects('Unexpected native compiler')
        self.doc['Actions'][0]['ProducedItems'] = []
        self.rejects('Response output missing')

    def test_no_historical_output_overwrite(self):
        import sys
        from unittest.mock import patch
        (self.E / '.brezi-isolated-engine').write_text(str(self.E))
        (self.P / 'BreziTwin.uproject').write_text('{}')
        graph = self.P.parent / 'actions.json'
        graph.write_text(json.dumps(self.doc))
        output = graph.parent / 'graph-review.json'
        output.write_text('preserved')
        with patch.object(sys, 'argv', ['review_graph.py', '--engine', str(self.E), '--project', str(self.P), '--graph', str(graph)]):
            with self.assertRaisesRegex(ValueError, 'new review file'):
                R.main()
        self.assertEqual(output.read_text(), 'preserved')

    def make_copy(self, filename='libtbb.12.17.dylib'):
        import shlex
        source = self.E / 'Engine/Source/ThirdParty/Intel/TBB/Deploy/oneTBB-2022.3.0/Mac/lib' / filename
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(b'CPU fixture library bytes')
        target = self.P / 'Binaries/Mac' / filename
        return {'Id': 2, 'Type': 'BuildProject', 'WorkingDirectory': str(self.wd), 'CommandPath': '/bin/sh',
                'CommandArguments': '-c ' + shlex.quote(f'cp -f "{source}" "{target}"'), 'ResponseFileContents': [],
                'ProducedItems': [str(target)], 'DeleteItems': [str(target)], 'PrerequisiteActions': []}

    def test_exact_tbb_copies_and_hashes(self):
        for name in ('libtbb.12.17.dylib', 'libtbb.12.dylib', 'libtbb.dylib', 'libtbbmalloc.2.17.dylib', 'libtbbmalloc.2.dylib', 'libtbbmalloc.dylib'):
            self.doc['Actions'] = self.doc['Actions'][:2] + [self.make_copy(name)]
            result = self.result()
            self.assertEqual(result['issues'], [])
            row = result['copyActions'][0]
            self.assertEqual(row['sourceSha256'], row['expectedOutputSha256'])
            self.assertIsNone(row['currentOutputSha256'])
            self.assertFalse(row['copyExecutedByReviewer'])
            self.assertFalse(Path(row['target']).exists())

    def test_copy_rejects_extra_shell_and_wrong_destination(self):
        import shlex
        original = self.make_copy()
        body = shlex.split(original['CommandArguments'])[1]
        for changed in (body + '; true', body + ' && true', body.replace('cp -f', 'cp -rf'),
                        body.replace(str(self.P), str(self.E / '.brezi-managed/old/Project/BreziTwin')),
                        body.replace('libtbb.12.17.dylib', 'libOther.dylib')):
            action = dict(original, CommandArguments='-c ' + shlex.quote(changed))
            self.doc['Actions'] = self.doc['Actions'][:2] + [action]
            self.rejects('Unsupported copy action')

    def test_copy_rejects_output_mismatch_and_source_alias(self):
        action = self.make_copy()
        self.doc['Actions'].append(action)
        action['DeleteItems'] = []
        self.rejects('output/deletion must equal target')
        action['DeleteItems'] = action['ProducedItems'][:]
        row = R.tbb_copy(action, self.E, self.P)
        source = Path(row['source'])
        alias_target = source.with_suffix('.real')
        source.rename(alias_target)
        source.symlink_to(alias_target)
        self.rejects('TBB source missing or aliased')

    def test_actual_stored_graphs_read_only(self):
        E = Path(__file__).resolve().parents[3] / 'output/unreal/caustics-active-study/candidate/UE_5.8'
        P = E / '.brezi-managed/active/Project/BreziTwin'
        names = [('editor-graph-delivery02-8c9e209356604367b8fc11a38110d929', 46, 1),
                 ('game-graph-delivery03-664979644b88454baf22ee7b83e6fc16', 71, 3)]
        for name, count, providers in names:
            graph = E / '.brezi-managed/active/stages' / name / 'actions.json'
            if not graph.is_file():
                self.skipTest('Optional historical native fixtures absent')
            raw = graph.read_bytes()
            result = R.review(json.loads(raw), E, P, R.sha(raw))
            self.assertEqual(result['actionCount'], count)
            self.assertEqual(len(result['providerCompileActions']), providers)
            self.assertTrue(all(x['apiEnabled'] and x['linkActions'] for x in result['providerCompileActions']))
            # Later builds regenerate shared Engine RSPs. They are current files,
            # not immutable fixtures: retain any actual drift as rejection.
            self.assertTrue(all(row[1] == 'Response file differs from exported command' for row in result['issues']), result['issues'])
            self.assertEqual(result['status'], 'failed' if result['issues'] else 'pass')
            actions = {a['Id']: a for a in json.loads(raw)['Actions']}
            for row in result['issues']:
                self.assertIn(actions[row[0]]['Type'], ('Compile', 'Link'))
            self.assertEqual(graph.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
