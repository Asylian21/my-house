"""CPU graph/configuration checks; never execute UBT, Clang, Xcode or an Unreal app."""
import importlib.util
import json
from pathlib import Path
import shlex
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('model_refresh_build', Path(__file__).with_name('model-refresh-build.py'))
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) if not isinstance(data, str) else data)
    return path


class ConfigurationTests(unittest.TestCase):
    def test_legacy_default_and_explicit_shipping(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory).resolve()
            write(output / 'profile.json', {})
            self.assertEqual(BUILD.game_configuration(output), 'Development')
            write(output / 'profile.json', {'gameConfiguration': 'Shipping'})
            self.assertEqual(BUILD.game_configuration(output), 'Shipping')
            for invalid in ('Test', 'shipping', '', None, '../Development'):
                write(output / 'profile.json', {'gameConfiguration': invalid})
                with self.subTest(invalid=invalid), self.assertRaisesRegex(RuntimeError, 'gameConfiguration'):
                    BUILD.game_configuration(output)

    def test_receipt_remains_configuration_specific(self):
        project = Path('/isolated/Project/BreziTwin')
        self.assertEqual(BUILD.target_receipt_path(project, 'Development').name, 'BreziTwin.target')
        self.assertEqual(BUILD.target_receipt_path(project, 'Shipping').name, 'BreziTwin-Mac-Shipping.target')

    def test_shipping_xcode_handoff_uses_linked_name_without_changing_configuration(self):
        workspace, run = Path('/isolated project/workspace'), Path('/isolated project/run')
        development = BUILD.xcode_arguments(workspace, run, 'Development')
        shipping = BUILD.xcode_arguments(workspace, run, 'Shipping')
        for configuration, argv in [('Development', development), ('Shipping', shipping)]:
            self.assertEqual(argv[argv.index('-configuration') + 1], configuration)
            self.assertEqual(argv[argv.index('-workspace') + 1], str(workspace))
            self.assertEqual(argv[argv.index('-derivedDataPath') + 1], str(run / 'derived-data'))
            self.assertIn('UE_XCODE_BUILD_MODE=PostBuildSync', argv)
        names = ['UE_UBT_BINARY_SUBPATH=BreziTwin', 'UE_MAC_EXECUTABLE_NAME=BreziTwin',
                 'PRODUCT_NAME=BreziTwin', 'EXECUTABLE_NAME=BreziTwin']
        self.assertEqual([value for value in shipping if value in names], names)
        self.assertFalse(any(value in development for value in names))
        self.assertFalse(any('BreziTwin-Mac-Shipping' in value for value in shipping))
        with self.assertRaisesRegex(RuntimeError, 'Unsupported Xcode Game configuration'):
            BUILD.xcode_arguments(workspace, run, 'Test')

    def test_installed_engine_requires_arm64_game_configuration_and_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Path(directory).resolve()
            write(engine / 'Engine/Build/InstalledBuild.txt', 'installed')
            write(engine / 'Engine/Config/BaseEngine.ini', '[InstalledPlatforms]\n'
                  '+InstalledPlatformConfigurations=(PlatformName="Mac", Configuration="Shipping", '
                  'PlatformType="Game", Architecture="arm64", RequiredFile="Engine/Binaries/Mac/Shipping.target")\n')
            with self.assertRaisesRegex(RuntimeError, 'receipt is missing'):
                BUILD.check_installed_configuration(engine, 'Shipping')
            write(engine / 'Engine/Binaries/Mac/Shipping.target', '{}')
            BUILD.check_installed_configuration(engine, 'Shipping')
            with self.assertRaisesRegex(RuntimeError, 'does not advertise'):
                BUILD.check_installed_configuration(engine, 'Development')

    def test_shipping_products_pin_stable_finalized_app_and_reject_other_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory).resolve()
            raw = write(project / 'Binaries/Mac/BreziTwin', 'raw-link')
            app = write(project / 'Binaries/Mac/BreziTwin.app/Contents/MacOS/BreziTwin', 'signed-app')
            target = {'TargetName': 'BreziTwin', 'Platform': 'Mac', 'Configuration': 'Shipping', 'BuildProducts': [
                {'Path': str(raw), 'Type': 'RequiredResource'}, {'Path': str(app), 'Type': 'Executable'}]}
            hashes = BUILD.target_build_product_hashes(project, target, 'Shipping')
            self.assertEqual(hashes[str(app)], BUILD.sha(app))
            with self.assertRaisesRegex(RuntimeError, 'identity differs'):
                BUILD.target_build_product_hashes(project, target, 'Development')
            target['BuildProducts'][-1]['Path'] = str(write(project / 'Binaries/Mac/Other.app/Contents/MacOS/Other', 'other'))
            with self.assertRaisesRegex(RuntimeError, 'finalized Game app'):
                BUILD.target_build_product_hashes(project, target, 'Shipping')

    def test_exported_graph_configuration_is_checked_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            output = root / 'output/unreal/shipping'
            engine = root / 'EngineInstall'
            project = output / 'Project/BreziTwin'
            intermediate = project / 'Intermediate'
            configuration = 'Shipping'
            write(output / 'profile.json', {'gameConfiguration': configuration})
            write(project / 'BreziTwin.uproject', {'Plugins': []})
            write(project / 'Config/DefaultGame.ini', '[Packaging]\n')
            source = write(project / 'Source/Module.cpp', 'int fixture;')
            ubt = write(engine / 'Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll', 'ubt')
            script = write(engine / 'Engine/Build/BatchFiles/Mac/UpdateVersionAfterBuild.sh', 'script')
            strip = write(root / 'Toolchain/usr/bin/strip', 'fixture-strip-tool')
            dotnet = engine / 'Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet'
            cwd = engine / 'Engine/Source'
            cwd.mkdir(parents=True)
            obj = intermediate / 'Module.o'
            raw = project / 'Binaries/Mac/BreziTwin'
            receipt = BUILD.target_receipt_path(project, configuration)
            post_data = {'ProjectFile': str(project / 'BreziTwin.uproject'), 'Platform': 'Mac',
                         'TargetName': 'BreziTwin', 'Configuration': configuration, 'StubOutputPath': str(raw)}
            post = write(intermediate / 'PostBuildSync.json', post_data)
            metadata_data = {'ProjectFile': str(project / 'BreziTwin.uproject'), 'ReceiptFile': str(receipt),
                             'Receipt': {'TargetName': 'BreziTwin', 'Platform': 'Mac', 'Configuration': configuration}}
            metadata = write(intermediate / 'TargetMetadata.json', metadata_data)
            write(intermediate / 'ProjectFiles/BreziTwin_Mac_BreziTwin.xcworkspace/contents.xcworkspacedata', 'workspace')
            actions = []

            def action(kind, command, args, produced, response=None):
                index = len(actions) + 1
                data = {'Id': index, 'Type': kind, 'CommandPath': str(command), 'CommandArguments': shlex.join(args),
                        'WorkingDirectory': str(cwd), 'ProducedItems': [str(produced)], 'DeleteItems': [],
                        'PrerequisiteActions': [index - 1] if index > 1 else []}
                if response is not None:
                    data['ResponseFileContents'] = [response]
                actions.append(data)

            compile_text = shlex.join(['-c', str(source), '-o', str(obj)])
            compile_rsp = write(intermediate / 'compile.rsp', compile_text)
            action('Compile', BUILD.CLANG, ['@' + str(compile_rsp)], obj, compile_text)
            link_text = shlex.join([str(obj), '-o', str(raw)])
            link_rsp = write(intermediate / 'link.rsp', link_text)
            action('Link', BUILD.CLANG, ['@' + str(link_rsp)], raw, link_text)
            action('CreateAppBundle', dotnet, [str(ubt), '-Mode=ApplePostBuildSync', '-Input=' + str(post)],
                   project / 'Binaries/Mac/BreziTwin.app/Contents/Info.plist')
            action('BuildProject', '/bin/sh', [str(script), str(project), 'Mac', '1'],
                   project / 'Build/Mac/BreziTwin.PackageVersionCounter')
            marker = project / 'Intermediate/Build/Mac/arm64/BreziTwin/Shipping/BreziTwin.stripped'
            strip_command = shlex.join([str(strip), str(raw), '-S']) + ' && touch ' + shlex.quote(str(marker))
            action('CreateAppBundle', '/bin/sh', ['-c', strip_command], marker)
            action('WriteMetadata', dotnet, [str(ubt), '-Mode=WriteMetadata', '-Input=' + str(metadata)], receipt)
            graph = write(output / 'game-actions.json', {'Environment': {}, 'Actions': actions})
            with patch.object(BUILD, 'ROOT', root), patch.object(BUILD, 'STRIP', strip):
                plan = BUILD.prepare_plan(output, engine, graph)
                self.assertEqual(plan[-1], configuration)
                self.assertIn(str(output / 'profile.json'), plan[-2])
                self.assertEqual([phase for phase, _ in plan[4]], ['compile', 'link', 'xcode', 'version', 'strip', 'metadata'])
                self.assertIn(str(strip), plan[-2])
                original_strip_arguments = actions[-2]['CommandArguments']
                actions[-2]['CommandArguments'] = shlex.join(['-c', strip_command.replace(' -S ', ' -x ')])
                write(graph, {'Environment': {}, 'Actions': actions})
                with self.assertRaisesRegex(RuntimeError, 'Unreviewed Shipping strip'):
                    BUILD.prepare_plan(output, engine, graph)
                actions[-2]['CommandArguments'] = original_strip_arguments
                write(graph, {'Environment': {}, 'Actions': actions})
                post_data['Configuration'] = 'Development'
                write(post, post_data)
                with self.assertRaisesRegex(RuntimeError, 'Xcode postbuild configuration'):
                    BUILD.prepare_plan(output, engine, graph)
                post_data['Configuration'] = configuration
                write(post, post_data)
                metadata_data['Receipt']['Configuration'] = 'Development'
                write(metadata, metadata_data)
                with self.assertRaisesRegex(RuntimeError, 'Metadata configuration'):
                    BUILD.prepare_plan(output, engine, graph)


if __name__ == '__main__':
    unittest.main()
