import importlib.util, tempfile, unittest
from pathlib import Path
import os, sys
sys.dont_write_bytecode = True
SCRIPT = Path(os.environ.get("SONARFIX_SCRIPT", str(Path(__file__).resolve().parents[2] / "scripts" / "sonar-fix.py")))
spec = importlib.util.spec_from_file_location("sonarfix", SCRIPT)
sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)
CATALOG = sf.load_rules()["rules"]["python"]

class Versions(unittest.TestCase):
    def test_python_bounds(self):
        for spec_text, expected in [("<3.13,>=3.10", "3.10"), ("^3.11", "3.11"), ("~=3.12", "3.12"),
                                    ("~2.7 || ^3.6", "3.6"), (">=3.8.1,<4.0", "3.8"), ("==3.12.*", "3.12"), ("", "unknown")]:
            self.assertEqual(sf.python_lower_bound(spec_text), expected, spec_text)
    def test_maven(self):
        self.assertEqual(sf.java_version_maven("<properties><java.version>21</java.version></properties>"), "21")
        self.assertEqual(sf.java_version_maven("<properties><java.version>1.8</java.version><maven.compiler.source>${java.version}</maven.compiler.source></properties>"), "8")
        self.assertEqual(sf.java_version_maven("<artifactId>maven-compiler-plugin</artifactId><configuration><release>17</release></configuration>"), "17")
    def test_gradle(self):
        for text, expected in [("languageVersion = JavaLanguageVersion.of(17)", "17"), ("sourceCompatibility = JavaVersion.VERSION_1_8", "8"),
                               ("kotlin { jvmToolchain(21) }", "21"), ("sourceCompatibility = '11'", "11")]:
            self.assertEqual(sf.java_version_gradle(text), expected, text)

class Globs(unittest.TestCase):
    def test_sonar_globs(self):
        rx = [sf.glob_to_regex(p) for p in sf.sonar_patterns("**/model/**, **/*Application.java,src/gen/*.java")]
        self.assertTrue(any(r.match("src/main/java/a/model/X.java") for r in rx))
        self.assertTrue(any(r.match("src/main/java/a/DemoApplication.java") for r in rx))
        self.assertTrue(any(r.match("src/gen/A.java") for r in rx))
        self.assertFalse(any(r.match("src/gen/sub/A.java") for r in rx))
        self.assertFalse(any(r.match("src/main/java/a/Service.java") for r in rx))

class Tests(unittest.TestCase):
    def test_classification(self):
        for path in ["tests/test_a.py", "a_test.py", "conftest.py", "src/test/java/a/ATest.java", "web/a.spec.ts", "pkg/a_test.go", "spec/a_spec.rb"]:
            self.assertTrue(sf.is_test_path(path), path)
        for path in ["app/service.py", "src/main/java/a/Tester.java", "web/contest.ts", "latest/a.py"]:
            self.assertFalse(sf.is_test_path(path), path)

class DuplicateLiterals(unittest.TestCase):
    def run_on(self, source, name="mod.py"):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / name).write_text(source)
            return sf.python_duplicate_literals(Path(d), name, CATALOG)
    def test_threshold_and_filters(self):
        found, _ = self.run_on('a="hello world"\nb="hello world"\nc="hello world"\n')
        self.assertEqual([f["rule"] for f in found], ["S1192"])
        for skipped in ['"abcd"', '"single_word"', '"%Y-%m-%d"', '"#a1b2c3"']:
            found, _ = self.run_on(f"a={skipped}\nb={skipped}\nc={skipped}\n")
            self.assertEqual(found, [], skipped)
        found, _ = self.run_on('"""doc string here"""\nx=f"hello world {1}"\ny=f"hello world {2}"\nz="hello world"\n')
        self.assertEqual(found, [])
        found, _ = self.run_on('a="hello world"\nb="hello world"\nc="hello world"\n', name="test_mod.py")
        self.assertEqual(found, [])
    def test_new_syntax_note(self):
        found, note = self.run_on("type Alias = list[int]\n")
        self.assertEqual(found, [])
        if note:
            self.assertIn("S1192 and S5754 checks skipped", note)

class Gaps(unittest.TestCase):
    def run_on(self, source, name="mod.py"):
        return DuplicateLiterals.run_on(self, source, name)
    def test_four_char_phrase_skipped(self):
        found, _ = self.run_on('a="a bc"\nb="a bc"\nc="a bc"\n')
        self.assertEqual(found, [])
        found, _ = self.run_on('a="a bcd"\nb="a bcd"\nc="a bcd"\n')
        self.assertEqual(len(found), 1)
    def test_lowest_or_group(self):
        self.assertEqual(sf.python_lower_bound("^3.10 || ^3.8"), "3.8")
    def test_globstar_matches_zero_dirs(self):
        self.assertTrue(sf.glob_to_regex("**/model/**").match("model/X.java"))
    def test_fstrings_skipped_even_when_parts_repeat(self):
        found, _ = self.run_on('x=1\na=f"hello world {x}"\nb=f"hello world {x}"\nc=f"hello world {x}"\n')
        self.assertEqual(found, [])
    def test_repeated_docstrings_skipped(self):
        src = "".join(f'def f{i}():\n    """Return the value here."""\n    return {i}\n' for i in range(3))
        found, _ = self.run_on(src)
        self.assertEqual(found, [])
    def test_singular_test_dir(self):
        self.assertTrue(sf.is_test_path("test/helpers.py"))

class Mapping(unittest.TestCase):
    def test_component_paths(self):
        self.assertEqual(sf.sonar_component_path("com.example:shop-service:src/A.java", {}), "src/A.java")
        self.assertEqual(sf.sonar_component_path("k:x", {"k:x": "mod/x.py"}), "mod/x.py")
    def test_scope_and_actions(self):
        cat = {"S1192": {"scope": "Main"}, "S1481": {"scope": "All"}, "S2699": {"scope": "Tests"}}
        self.assertFalse(sf.keep_for_scope("S1192", cat, True)); self.assertTrue(sf.keep_for_scope("S1481", cat, True))
        self.assertFalse(sf.keep_for_scope("S2699", cat, False))
        self.assertEqual(sf.action_for("S1135", "CODE_SMELL"), "report"); self.assertEqual(sf.action_for("S2068", "VULNERABILITY"), "ask")
        self.assertEqual(sf.action_for("S107", "CODE_SMELL"), "check-api"); self.assertEqual(sf.action_for("S1481", "CODE_SMELL"), "fix")
    def test_languages(self):
        self.assertIsNone(sf.language_of("types/a.d.ts")); self.assertEqual(sf.language_of("a.TSX"), "typescript")

class SonarKey(unittest.TestCase):
    def test_maven_default_project_key(self):
        pom = """<project><parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId></parent>
<groupId>com.example</groupId><artifactId>orders-service</artifactId><properties><sonar.host.url>http://sonar</sonar.host.url></properties>
<dependencies><dependency><groupId>x</groupId><artifactId>y</artifactId></dependency></dependencies></project>"""
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text(pom)
            settings, _, _ = sf.sonar_settings(Path(d))
        self.assertEqual(settings.get("sonar.projectKey"), "com.example:orders-service")
    def test_maven_group_from_parent(self):
        pom = "<project><parent><groupId>com.acme</groupId><artifactId>p</artifactId></parent><artifactId>svc</artifactId></project>"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text(pom)
            settings, _, _ = sf.sonar_settings(Path(d))
        self.assertEqual(settings.get("sonar.projectKey"), "com.acme:svc")

class ReviewFindings(unittest.TestCase):
    def test_multiline_pom_exclusions(self):
        pom = "<project><groupId>g</groupId><artifactId>a</artifactId><properties>\n<sonar.exclusions>\n  **/model/**,\n  **/dto/**\n</sonar.exclusions>\n<sonar.login>\n  abc\n</sonar.login>\n</properties></project>"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text(pom)
            settings, _, credentials = sf.sonar_settings(Path(d))
        self.assertEqual(sf.sonar_patterns(settings.get("sonar.exclusions", "")), ["**/model/**", "**/dto/**"])
        self.assertEqual(credentials, ["pom.xml:7"])
    def test_dot_folder_pattern_kept(self):
        self.assertEqual(sf.sonar_patterns("./src/gen/**,.gen/**"), ["src/gen/**", ".gen/**"])
    def test_huge_argument_list_is_an_error_not_a_crash(self):
        code, _, err = sf.run_command(["echo"] + ["x" * 1000] * 3000)
        self.assertNotEqual(code, 0)
        self.assertIn("too long", err)
    def test_batches(self):
        self.assertEqual([len(b) for b in sf.batches(list(range(1201)), 500)], [500, 500, 201])

class BroadCatchDecision(unittest.TestCase):
    def test_broad_catch_is_a_decision(self):
        self.assertEqual(sf.action_for("BROAD-EXCEPT", "CODE_SMELL"), "ask")
        self.assertEqual(sf.action_for("S2221", "CODE_SMELL"), "ask")
        self.assertEqual(sf.action_for("S1128", "CODE_SMELL"), "check-api")

class DeferredMinors(unittest.TestCase):
    def test_venv_runner_resolved_in_module_dir(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d) / "svc"
            (module / ".venv/bin").mkdir(parents=True)
            (module / ".venv/bin/python").write_text("")
            (module / "pyproject.toml").write_text("[project]\nname='x'\n[tool.pytest.ini_options]\n")
            (module / "tests").mkdir(exist_ok=True); (module / "tests/test_x.py").write_text("")
            info = sf.python_module(module)
        self.assertTrue(info["test"].startswith(".venv/bin/python -m pytest"))
        self.assertNotIn("missing: .venv", info["test"])
    def test_broken_eslint_cache_is_not_ready(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "node_modules/.bin").mkdir(parents=True)
            (Path(d) / "node_modules/.bin/eslint").write_text("")
            self.assertFalse(sf.eslint_ready(Path(d)))
    def test_csharp_test_project_dir(self):
        self.assertTrue(sf.is_test_path("src/Shop.Tests/Helpers.cs"))
        self.assertTrue(sf.is_test_path("Shop.UnitTests/Fakes/Clock.cs"))
        self.assertFalse(sf.is_test_path("src/Shop.Api/Program.cs"))
    def test_properties_credential_line_after_continuation(self):
        text = "sonar.exclusions=a/**,\\\n  b/**\nsonar.token=abc\n"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "sonar-project.properties").write_text(text)
            settings, _, credentials = sf.sonar_settings(Path(d))
        self.assertEqual(credentials, ["sonar-project.properties:3"])
        self.assertEqual(sf.sonar_patterns(settings["sonar.exclusions"]), ["a/**", "b/**"])
    def test_file_sha256_in_chunks(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "x.bin"; f.write_bytes(b"abc" * 100000)
            self.assertEqual(sf.file_sha256(f), hashlib.sha256(b"abc" * 100000).hexdigest())

class PmdInstallAtomic(unittest.TestCase):
    def install_with(self, members, prepare=None):
        import io, os, zipfile, hashlib
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle:
            for name, data in members:
                bundle.writestr(name, data)
        payload = buffer.getvalue()
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False
        d = tempfile.mkdtemp()
        old = (os.environ.get("XDG_CACHE_HOME"), sf.urllib.request.urlopen, sf.PMD_SHA256)
        os.environ["XDG_CACHE_HOME"] = d
        if prepare:
            prepare()
        sf.urllib.request.urlopen = lambda *a, **k: Response(payload)
        sf.PMD_SHA256 = hashlib.sha256(payload).hexdigest()
        try:
            return sf.command_install_pmd(None), Path(d)
        finally:
            sf.urllib.request.urlopen, sf.PMD_SHA256 = old[1], old[2]
            if old[0] is None: os.environ.pop("XDG_CACHE_HOME")
            else: os.environ["XDG_CACHE_HOME"] = old[0]
    def test_good_archive_installs(self):
        code, d = self.install_with([(f"pmd-bin-{sf.PMD_VERSION}/bin/pmd", "#!/bin/sh\n")])
        self.assertEqual(code, 0)
        self.assertTrue((d / f"sonarqube-issue-fixer/pmd-bin-{sf.PMD_VERSION}/bin/pmd").exists())
    def test_archive_without_pmd_leaves_nothing(self):
        code, d = self.install_with([("other/readme.txt", "x")])
        self.assertEqual(code, 1)
        self.assertFalse((d / f"sonarqube-issue-fixer/pmd-bin-{sf.PMD_VERSION}").exists())
        self.assertEqual(list((d / "sonarqube-issue-fixer").glob("*")), [])

class ReviewRound1(unittest.TestCase):
    def test_generated_markers_need_a_real_header(self):
        hand_written = ['"""Order model. The id is auto-generated by the database."""\n', "# DO NOT EDIT without updating the API\nX = 1\n"]
        generated = ["// Code generated by protoc-gen-go. DO NOT EDIT.\npackage x\n", "# @generated by tool\nx = 1\n", "// <auto-generated>\nclass A {}\n"]
        for text in hand_written:
            self.assertFalse(sf.looks_generated(text), text)
        for text in generated:
            self.assertTrue(sf.looks_generated(text), text)
    def test_kotlin_scripts_are_source_but_gradle_scripts_are_not(self):
        self.assertEqual(sf.language_of("scripts/release.main.kts"), "kotlin")
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "build.gradle.kts").write_text("plugins {}\n")
            self.assertEqual(sf.exclusion_reason(Path(d), "build.gradle.kts", sf.ScopeRules(), False), "build-script")
    def test_incomplete_read_is_reported(self):
        import io, os, http.client
        class Broken(io.BytesIO):
            def read(self, *a): raise http.client.IncompleteRead(b"")
            def __enter__(self): return self
            def __exit__(self, *a): return False
        with tempfile.TemporaryDirectory() as d:
            old = (os.environ.get("XDG_CACHE_HOME"), sf.urllib.request.urlopen)
            os.environ["XDG_CACHE_HOME"] = d
            sf.urllib.request.urlopen = lambda *a, **k: Broken()
            try:
                code = sf.command_install_pmd(None)
            finally:
                sf.urllib.request.urlopen = old[1]
                if old[0] is None: os.environ.pop("XDG_CACHE_HOME")
                else: os.environ["XDG_CACHE_HOME"] = old[0]
            self.assertEqual(code, 1)
            self.assertEqual(list(Path(d).rglob("*.zip")), [])
    def test_write_findings_without_out_keeps_no_open_fd(self):
        import os
        before = len(os.listdir("/dev/fd"))
        path = sf.write_findings([], None)
        after = len(os.listdir("/dev/fd"))
        path.unlink()
        self.assertEqual(after, before)
    def test_pmd_ruleset_has_no_deprecated_refs(self):
        ruleset = sf.pmd_ruleset(sf.load_rules())
        self.assertNotIn("design.xml/UseUtilityClass", ruleset)
        self.assertNotIn("design.xml/AvoidCatchingGenericException", ruleset)
    def test_stderr_summary_skips_warnings(self):
        err = "[WARN] Warning at ruleset.xml:16:1\n  deprecated rule\n[ERROR] Cannot load ruleset\n"
        self.assertEqual(sf.error_summary(err), "[ERROR] Cannot load ruleset")

class ReviewRound2(unittest.TestCase):
    def test_sarif_uri_is_percent_decoded(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "my dir").mkdir()
            (root / "my dir/c.py").write_text("x = 1\n")
            uri = "file://" + str(root).replace(" ", "%20") + "/my%20dir/c.py"
            self.assertEqual(sf.relative_to_root(root, uri), "my dir/c.py")
    def test_build_like_folder_inside_sources_is_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for rel in ("src/build/c.py", "build/x.py", "app/build/gen/y.kt", "pkg/out/z.go"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x\n")
            (root / "app/build.gradle.kts").write_text("plugins {}\n")
            self.assertIsNone(sf.exclusion_reason(root, "src/build/c.py", sf.ScopeRules(), False))
            self.assertIsNone(sf.exclusion_reason(root, "pkg/out/z.go", sf.ScopeRules(), False))
            self.assertEqual(sf.exclusion_reason(root, "build/x.py", sf.ScopeRules(), False), "dependency-or-build-dir")
            self.assertEqual(sf.exclusion_reason(root, "app/build/gen/y.kt", sf.ScopeRules(), False), "dependency-or-build-dir")
    def test_python_target_per_module(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.9"\n')
            (root / "backend").mkdir()
            (root / "backend/pyproject.toml").write_text('[project]\nrequires-python = ">=3.12"\n')
            self.assertEqual(sf.python_target_for(root, "backend/m.py"), "py312")
            self.assertEqual(sf.python_target_for(root, "tools/x.py"), "py39")

class ReviewRound3(unittest.TestCase):
    def test_conda_env_and_site_packages_are_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for rel in ("env/conda-meta/history", "env/lib/python3.11/site-packages/requests/api.py", "vendored/site-packages/x.py", "app/main.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            self.assertEqual(sf.exclusion_reason(root, "env/lib/python3.11/site-packages/requests/api.py", sf.ScopeRules(), False), "dependency-or-build-dir")
            self.assertEqual(sf.exclusion_reason(root, "vendored/site-packages/x.py", sf.ScopeRules(), False), "dependency-or-build-dir")
            self.assertIsNone(sf.exclusion_reason(root, "app/main.py", sf.ScopeRules(), False))
    def test_bare_except_is_fixed_to_except_exception(self):
        self.assertEqual(sf.action_for("S5754", "CODE_SMELL"), "fix")
    def test_module_under_build_like_folder_is_discovered(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "tools/out/sub").mkdir(parents=True)
            (root / "tools/out/sub/package.json").write_text('{"scripts":{"test":"jest"}}')
            self.assertIn("tools/out/sub", [relative for relative, _ in sf.discover_modules(root)])
    def test_workspace_children_follow_root_manager(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "package.json").write_text('{"name":"r"}')
            (root / "pnpm-workspace.yaml").write_text("packages: ['packages/*']\n")
            (root / "pnpm-lock.yaml").write_text("")
            (root / "packages/a").mkdir(parents=True)
            (root / "packages/a/package.json").write_text('{"scripts":{"test":"jest"}}')
            self.assertEqual([relative for relative, _ in sf.discover_modules(root)], ["."])
    def test_project_level_issue_has_no_fake_file(self):
        self.assertEqual(sf.sonar_component_path("com.acme:service", {}, "com.acme:service"), "")
        self.assertEqual(sf.sonar_component_path("com.acme:service:src/A.java", {}, "com.acme:service"), "src/A.java")
    def test_missing_pytest_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            import subprocess, sys
            subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(module / ".venv")], check=True)
            (module / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
            (module / "tests").mkdir(exist_ok=True); (module / "tests/test_x.py").write_text("")
            info = sf.python_module(module)
        self.assertIn("(missing: pytest)", info["test"])

class ReviewRound4(unittest.TestCase):
    def test_generated_after_licence_header(self):
        licence = "".join(f"// Licensed under the Apache License line {i}\n" for i in range(15))
        self.assertTrue(sf.looks_generated(licence + "\n// Code generated by deepcopy-gen. DO NOT EDIT.\npackage v1\n"))
        self.assertTrue(sf.GENERATED_NAME_PATTERN.search("zz_generated.deepcopy.go"))
    def test_maven_layout_beats_names(self):
        self.assertFalse(sf.is_test_path("src/main/java/com/x/spec/UserSpec.java"))
        self.assertFalse(sf.is_test_path("svc/src/main/java/x/AuditIT.java"))
        self.assertTrue(sf.is_test_path("src/test/java/com/x/Helpers.java"))
        self.assertFalse(sf.is_test_path("mylib/testing/helpers.py"))
    def test_module_relative_exclusions(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pom.xml").write_text("<project><modules><module>svc</module></modules><properties><sonar.exclusions>src/main/java/gen/**</sonar.exclusions></properties></project>")
            for rel in ("svc/pom.xml", "svc/src/main/java/gen/A.java", "svc/src/main/java/app/B.java"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("<project/>" if rel.endswith(".xml") else "class A {}\n")
            settings, _, _ = sf.sonar_settings(root)
            selected, excluded, _ = sf.filter_scope(root, ["svc/src/main/java/gen/A.java", "svc/src/main/java/app/B.java"], settings)
        self.assertEqual(selected, ["svc/src/main/java/app/B.java"])
        self.assertEqual(excluded.get("sonar.exclusions"), 1)
    def test_non_git_walk_skips_hidden_folders(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for rel in (".eggs/requests.egg/requests/api.py", "app/main.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            self.assertEqual(sf.all_files(root, False), ["app/main.py"])
    def test_node_family_and_build_files_use_constants(self):
        self.assertTrue(all(name in sf.BUILD_FILE_NAMES for name in (sf.POM_FILE, sf.GRADLE_FILE, sf.PYPROJECT_FILE)))
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "package.json").write_text('{"workspaces": ["p/*"]}')
            self.assertTrue(all(sf.aggregates_children(Path(d), eco) for eco in sf.NODE_ECOSYSTEMS))

class ReviewRound5(unittest.TestCase):
    def test_relative_to_root_tolerates_case_and_outside(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve() / "proj"
            (root / "pkg").mkdir(parents=True); (root / "pkg/m.py").write_text("x = 1\n")
            upper = root.parent / "PROJ"
            self.assertEqual(sf.relative_to_root(upper, str(root / "pkg/m.py")), "pkg/m.py")
            self.assertEqual(sf.relative_to_root(root, "/elsewhere/x.py"), "/elsewhere/x.py")
    def test_php_test_command_checked_in_module_dir(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve() / "backend"
            (module / "vendor/bin").mkdir(parents=True)
            (module / "vendor/bin/phpunit").write_text("")
            (module / "phpunit.xml").write_text("<phpunit/>")
            (module / "composer.json").write_text('{"require": {"php": ">=8.2"}}')
            info = sf.php_module(module)
        self.assertEqual(info["test"], "vendor/bin/phpunit")
    def test_multiline_generator_headers(self):
        openapi = "/*\n * Pet Store API\n * NOTE: This class is auto generated by OpenAPI Generator.\n * https://openapi-generator.tech\n * Do not edit the class manually.\n */\npackage x;\n"
        jooq = "/*\n * This file is generated by jOOQ.\n */\npackage y;\n"
        annotated = "package z;\n\nimport javax.annotation.processing.Generated;\n\n@Generated(\"dagger\")\npublic final class A {}\n"
        for text in (openapi, jooq, annotated):
            self.assertTrue(sf.looks_generated(text), text[:40])
        self.assertFalse(sf.looks_generated("/** Builds the order.\n * The id is generated by the database. */\nclass Order {}\n"))
    def test_pom_comments_are_ignored(self):
        pom = "<project><groupId>g</groupId><artifactId>a</artifactId>\n<!-- <sonar.exclusions>src/main/java/**</sonar.exclusions>\n<sonar.login>abc</sonar.login> -->\n<properties><sonar.host.url>https://sonar.example</sonar.host.url></properties></project>"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text(pom)
            settings, _, credentials = sf.sonar_settings(Path(d))
        self.assertNotIn("sonar.exclusions", settings)
        self.assertEqual(credentials, [])
        self.assertEqual(settings.get("sonar.host.url"), "https://sonar.example")
    def test_python_target_is_cached(self):
        self.assertTrue(hasattr(sf.python_target, "cache_info"))

class ReviewRound6(unittest.TestCase):
    def test_test_inclusions_when_tests_share_sources(self):
        self.assertFalse(sf.is_test_path("src/app.py", ["src"], ["**/*_test.py"], ["src"]))
        self.assertTrue(sf.is_test_path("src/app_test.py", ["src"], ["**/*_test.py"], ["src"]))
        self.assertTrue(sf.is_test_path("tests/x.py", ["tests"], [], ["src"]))
    def test_absolute_path_through_symlinked_parent(self):
        import argparse, os
        with tempfile.TemporaryDirectory() as d:
            real = Path(d).resolve()
            (real / "src").mkdir(); (real / "src/ok.py").write_text("x = 1\n")
            alias = Path(d)
            if str(alias) == str(real):
                self.skipTest("temp dir has no symlinked parent here")
            args = argparse.Namespace(files_from=None, files=[str(alias / "src/ok.py")])
            self.assertEqual(sf.read_scope(args, real), ["src/ok.py"])
    def test_sonar_sources_and_inclusions_limit_main_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for rel in ("src/a.py", "scripts/b.py", "tests/test_c.py", "src/gen/d.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            settings = {"sonar.sources": "src", "sonar.tests": "tests", "sonar.inclusions": "src/a.py,src/gen/**"}
            selected, excluded, _ = sf.filter_scope(root, ["src/a.py", "scripts/b.py", "tests/test_c.py", "src/gen/d.py"], settings, [])
        self.assertEqual(sorted(selected), ["src/a.py", "src/gen/d.py", "tests/test_c.py"])
        self.assertEqual(excluded.get("outside-sonar.sources"), 1)
    def test_properties_comment_does_not_continue(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "sonar-project.properties").write_text("# note \\\nsonar.exclusions=src/gen/**\n")
            settings, _, _ = sf.sonar_settings(Path(d))
        self.assertEqual(settings.get("sonar.exclusions"), "src/gen/**")
    def test_marker_inside_string_is_not_generated(self):
        self.assertFalse(sf.looks_generated('HEADER = "// Code generated by tool. DO NOT EDIT."\n'))
        self.assertFalse(sf.looks_generated('def f():\n    """Mentions @generated in a docstring."""\n'))
        self.assertTrue(sf.looks_generated("# Generated by the protocol buffer compiler.  DO NOT EDIT!\n"))
    def test_pmd_skips_annotations(self):
        self.assertIn('name="skipAnnotations" value="true"', sf.pmd_ruleset(sf.load_rules()))

class ReviewRound7(unittest.TestCase):
    def test_sonar_tests_set_means_names_do_not_count_outside(self):
        self.assertFalse(sf.is_test_path("src/app/test_helpers.py", ("tests",), (), ("src",)))
        self.assertTrue(sf.is_test_path("tests/test_a.py", ("tests",), (), ("src",)))
    def test_unresolved_maven_properties(self):
        self.assertEqual(sf.sonar_patterns("${project.basedir}"), ["."])
        self.assertEqual(sf.sonar_patterns("${sonar.srcDir},src/main"), ["src/main"])
    def test_spec_folder_is_test_only_for_ruby(self):
        self.assertFalse(sf.is_test_path("api/spec/models.py"))
        self.assertFalse(sf.is_test_path("pkg/spec/validator.ts"))
        self.assertTrue(sf.is_test_path("spec/models/user_spec.rb"))
        self.assertTrue(sf.is_test_path("spec/helpers/date.rb"))
    def test_case_fallback_with_length_changing_letters(self):
        with tempfile.TemporaryDirectory() as d:
            real = Path(d).resolve() / "İsmail" / "app"
            (real / "pkg").mkdir(parents=True); (real / "pkg/a.py").write_text("x = 1\n")
            other_case = real.parent.parent / "i̇smail" / "app"
            if not other_case.exists():
                self.skipTest("file system is case-sensitive or does not fold İ")
            self.assertEqual(sf.relative_to_root(other_case, str(real / "pkg/a.py")), "pkg/a.py")
    def test_hidden_folders_excluded_in_git_scope_too(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / ".github/scripts").mkdir(parents=True); (root / ".github/scripts/release.py").write_text("x = 1\n")
            self.assertEqual(sf.exclusion_reason(root, ".github/scripts/release.py", sf.ScopeRules(), False), "hidden-dir")
    def test_skipped_dir_is_cached(self):
        self.assertTrue(hasattr(sf.skipped_dir, "cache_info"))

class ReviewRound8(unittest.TestCase):
    def test_s1192_message_keeps_turkish_text(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.py").write_text('a = "Kay\u0131t bulunamad\u0131"\nb = "Kay\u0131t bulunamad\u0131"\nc = "Kay\u0131t bulunamad\u0131"\n')
            found, _ = sf.python_duplicate_literals(Path(d), "m.py", sf.load_rules()["rules"]["python"])
        self.assertIn("Kay\u0131t bulunamad\u0131", found[0]["message"])
    def test_missing_scope_files_are_noted(self):
        import argparse, io, contextlib
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); (root / "a.py").write_text("x = 1\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                files = sf.read_scope(argparse.Namespace(files_from=None, files=["a.py", "missing.py"]), root)
        self.assertEqual(files, ["a.py"])
        self.assertIn("note=file not found: missing.py", out.getvalue())
    def test_deleted_non_source_not_counted(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sf.exclusion_reason(Path(d).resolve(), "docs/gone.md", sf.ScopeRules(), False), "not-source")
    def test_deep_module_discovered(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "services/team/app/backend/api").mkdir(parents=True)
            (root / "services/team/app/backend/api/pyproject.toml").write_text("[project]\nname='x'\n")
            self.assertIn("services/team/app/backend/api", [r for r, _ in sf.discover_modules(root)])
    def test_partial_pmd_folder_is_replaced(self):
        code, cache = PmdInstallAtomic.install_with(self, [(f"pmd-bin-{sf.PMD_VERSION}/bin/pmd", "#!/bin/sh\n")],
                                                    prepare=lambda: (sf.pmd_home() / "lib").mkdir(parents=True))
        self.assertEqual(code, 0)
        self.assertTrue((cache / f"sonarqube-issue-fixer/pmd-bin-{sf.PMD_VERSION}/bin/pmd").exists())
    def test_analyzers_run_concurrently(self):
        self.assertTrue(hasattr(sf, "ANALYZER_WORKERS"))

class ReviewRound9(unittest.TestCase):
    def test_spaces_after_operators(self):
        self.assertEqual(sf.python_lower_bound(">= 3.9, < 3.13"), "3.9")
        self.assertEqual(sf.python_lower_bound("< 4, >= 3.8"), "3.8")
    def test_root_bin_kept_in_git_mode(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "package.json").write_text('{"bin": "bin/cli.js"}')
            (root / "bin").mkdir(); (root / "bin/cli.js").write_text("console.log(1)\n")
            self.assertIsNone(sf.exclusion_reason(root, "bin/cli.js", sf.ScopeRules(), False, (), True))
            self.assertEqual(sf.exclusion_reason(root, "bin/cli.js", sf.ScopeRules(), False, (), False), "dependency-or-build-dir")
    def test_sonar_sources_file_entry(self):
        self.assertIsNone(sf.sonar_rule_reason("main.py", sf.ScopeRules((), (), ("lib", "main.py")), ()))
    def test_failing_analyzer_becomes_error_line(self):
        groups = {"python": ["a.py"]}
        errors, notes = [], []
        old = sf.analyze_python
        sf.analyze_python = lambda *a: (_ for _ in ()).throw(ValueError("bad JSON"))
        try:
            results = sf.run_analyzers(Path("."), groups, sf.load_rules(), errors, notes)
        finally:
            sf.analyze_python = old
        self.assertEqual(results, [])
        self.assertTrue(any("python" in e and "bad JSON" in e for e in errors), errors)
    def test_spec_names_by_language_and_source_sets(self):
        self.assertFalse(sf.is_test_path("src/commonMain/kotlin/ApiSpec.kt"))
        self.assertTrue(sf.is_test_path("src/commonTest/kotlin/ApiSpec.kt"))
        self.assertFalse(sf.is_test_path("Domain/OrderSpec.cs"))
        self.assertFalse(sf.is_test_path("app/UserSpec.java"))
        self.assertTrue(sf.is_test_path("tests/UserSpec.kt") and sf.is_test_path("lib/UserSpec.kt"))
    def test_hand_written_grpc_module_is_source(self):
        self.assertIsNone(sf.GENERATED_NAME_PATTERN.search("user_grpc.py"))
        self.assertTrue(sf.GENERATED_NAME_PATTERN.search("user_pb2_grpc.py"))
    def test_paths_symlink_outside_does_not_abort(self):
        import io, contextlib
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve(); root = base / "proj"; root.mkdir(); (base / "shared.py").write_text("x = 1\n")
            (root / "a.py").write_text("x = 1\n"); (root / "linked.py").symlink_to(base / "shared.py")
            self.assertEqual(sf.expand_paths(root, ["a.py", "linked.py"], False), ["a.py", "linked.py"])
    def test_pytest_check_does_not_run_from_the_project(self):
        import inspect
        self.assertIn("gettempdir", inspect.getsource(sf.python_can_import))

class ReviewRound10(unittest.TestCase):
    def test_exclusions_not_relative_to_non_maven_folders(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "sonar-project.properties").write_text("sonar.exclusions=scripts/**\n")
            for rel in ("tools/Makefile", "tools/scripts/b.py", "scripts/a.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            settings, _, _ = sf.sonar_settings(root)
            selected, _, _ = sf.filter_scope(root, ["tools/scripts/b.py", "scripts/a.py"], settings)
        self.assertEqual(selected, ["tools/scripts/b.py"])
    def test_uv_commands_do_not_relock(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "uv.lock").write_text("pytest\n"); (module / "pyproject.toml").write_text("[dependency-groups]\ndev=['pytest','pyright']\n")
            (module / "tests").mkdir(exist_ok=True); (module / "tests/test_x.py").write_text("")
            info = sf.python_module(module)
        self.assertTrue(info["test"].startswith("uv run --frozen pytest"), info["test"])
        self.assertTrue(info["typecheck"].startswith("uv run --frozen pyright"), info["typecheck"])
    def test_missing_pytest_with_uv(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "uv.lock").write_text("version = 1\n"); (module / "pyproject.toml").write_text("[project]\nname='x'\n"); (module / "conftest.py").write_text("")
            info = sf.python_module(module)
        self.assertIn("(missing: pytest)", info["test"])
    def test_java_without_jdk_needs_review(self):
        import io, contextlib, shutil as sh
        old_which, old_exists = sf.shutil.which, sf.pmd_executable
        sf.shutil.which = lambda name: None if name == "java" else sh.which(name)
        sf.pmd_executable = lambda: Path(__file__)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                sf.print_analysis_notes({"java": ["A.java"]}, [], [])
        finally:
            sf.shutil.which, sf.pmd_executable = old_which, old_exists
        self.assertIn("review=java", out.getvalue())

class UserDecisions(unittest.TestCase):
    def test_sonar_config_without_tests_makes_tests_main(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "sonar-project.properties").write_text("sonar.sources=.\n")
            settings, _, _ = sf.sonar_settings(root)
            layout = sf.test_layout(settings, root)
        self.assertFalse((sf.classify("tests/test_auth.py", layout) == sf.TEST))
    def test_no_sonar_config_keeps_name_rules(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            layout = sf.test_layout({}, root)
        self.assertTrue((sf.classify("tests/test_auth.py", layout) == sf.TEST))
    def test_maven_without_sonar_tests_keeps_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pom.xml").write_text("<project><groupId>g</groupId><artifactId>a</artifactId><properties><sonar.host.url>h</sonar.host.url></properties></project>")
            settings, _, _ = sf.sonar_settings(root)
            layout = sf.test_layout(settings, root)
        self.assertTrue((sf.classify("src/test/java/a/ATest.java", layout) == sf.TEST))

class ReviewRound11(unittest.TestCase):
    def test_sonarjs_default_exclusions_under_git(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "package.json").write_text('{"bin": "bin/cli.js"}')
            for rel in ("dist/index.js", "bin/cli.js", "dist/tool.py", "src/vendor/lib.ts"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x\n")
            reason = lambda rel: sf.exclusion_reason(root, rel, sf.ScopeRules(), False, (), True)
            self.assertEqual(reason("dist/index.js"), "sonarjs-default-exclusion")
            self.assertEqual(reason("src/vendor/lib.ts"), "dependency-or-build-dir")
            self.assertIsNone(reason("bin/cli.js"))
            self.assertIsNone(reason("dist/tool.py"))
    def test_non_git_walk_keeps_build_like_folders_for_counting(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "package.json").write_text("{}")
            (root / "bin").mkdir(); (root / "bin/cli.js").write_text("x\n")
            self.assertIn("bin/cli.js", sf.all_files(root, False))
            self.assertEqual(sf.exclusion_reason(root, "bin/cli.js", sf.ScopeRules(), False, (), False), "dependency-or-build-dir")
    def test_import_catalog_follows_rule_language(self):
        data = sf.load_rules()
        self.assertIs(sf.catalog_for_rule_key(data, "java:S3776"), data["rules"]["java"])
        self.assertIs(sf.catalog_for_rule_key(data, "python:S3776"), data["rules"]["python"])
        self.assertIs(sf.catalog_for_rule_key(data, "typescript:S3776"), data["rules"]["javascript"])
    def test_scope_settings_parsed_once(self):
        rules, layout = sf.scope_settings({"sonar.sources": "src", "sonar.tests": "tests"}, Path("."))
        self.assertEqual(rules.sources, layout.sources)
    def test_project_relative_helper(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); (root / "a.py").write_text("x\n")
            self.assertEqual(sf.project_relative(root, "a.py"), "a.py")
            with self.assertRaises(sf.UsageError):
                sf.project_relative(root, "../outside.py")

class ReviewRound12(unittest.TestCase):
    def test_untracked_build_output_guessed_under_git(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "setup.py").write_text("")
            for rel in ("build/lib/pkg/mod.py", "bin/tool.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            selected, excluded, _ = sf.filter_scope(root, ["build/lib/pkg/mod.py", "bin/tool.py"], {}, [], True, {"build/lib/pkg/mod.py"})
        self.assertEqual(selected, ["bin/tool.py"])
        self.assertEqual(excluded.get("dependency-or-build-dir"), 1)
    def test_security_impact_rules_are_ask(self):
        data = sf.load_rules()
        item = sf.finding("a.ts", 1, "S1313", "eslint", "ip", data["rules"]["javascript"])
        self.assertEqual(item["action"], "ask")
    def test_python_module_without_tests(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "pyproject.toml").write_text("[project]\nname='x'\n"); (module / "app.py").write_text("x = 1\n")
            info = sf.python_module(module)
        self.assertTrue(info["test"].startswith("none"), info["test"])
    def test_unsupported_language_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); (root / "src").mkdir(); (root / "src/App.vue").write_text("<template/>")
            self.assertEqual(sf.exclusion_reason(root, "src/App.vue", sf.ScopeRules(), False), "unsupported-language")
    def test_security_engine_keys_and_impacts_are_ask(self):
        data = sf.load_rules()
        a = sf.sonar_issue_finding({"rule": "pythonsecurity:S3649", "component": "p:a.py", "project": "p"}, "", {}, data)
        b = sf.sonar_issue_finding({"rule": "java:S9999", "component": "p:A.java", "project": "p",
                                     "impacts": [{"softwareQuality": "SECURITY", "severity": "HIGH"}]}, "", {}, data)
        self.assertEqual((a["action"], b["action"]), ("ask", "ask"))
    def test_missing_typecheck_and_tsc_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "package.json").write_text('{"devDependencies": {"typescript": "^5"}}'); (module / "tsconfig.json").write_text("{}")
            info = sf.node_module(module)
        self.assertIn("(missing: tsc", info["build"])
    def test_outside_absolute_path_is_skipped(self):
        import argparse, io, contextlib
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve(); root = base / "proj"; root.mkdir(); (root / "a.py").write_text("x\n"); (base / "o.py").write_text("x\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                files = sf.read_scope(argparse.Namespace(files_from=None, files=["a.py", str(base / "o.py")]), root)
        self.assertEqual(files, ["a.py"])
        self.assertIn("outside the project", out.getvalue())
    def test_solution_aggregates_projects(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "App.sln").write_text(""); (root / "src/App").mkdir(parents=True); (root / "src/App/App.csproj").write_text("<Project/>")
            self.assertEqual([r for r, _ in sf.discover_modules(root)], ["."])

class ReviewRound13(unittest.TestCase):
    def test_pytest_style_tests_without_declared_pytest(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "pyproject.toml").write_text("[project]\nname='x'\n")
            (module / "tests").mkdir(); (module / "tests/test_a.py").write_text("def test_x():\n    assert True\n")
            info = sf.python_module(module)
        self.assertIn("pytest", info["test"])
    def test_unittest_style_tests_keep_unittest(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "pyproject.toml").write_text("[project]\nname='x'\n")
            (module / "tests").mkdir(); (module / "tests/test_a.py").write_text("import unittest\nclass T(unittest.TestCase):\n    pass\n")
            info = sf.python_module(module)
        self.assertIn("unittest", info["test"])
    def test_test_inclusions_without_tests_skip_main_source_set(self):
        self.assertFalse(sf.is_test_path("src/main/java/p/TestDataFactory.java", (), ("**/*Test*.java",)))
        self.assertTrue(sf.is_test_path("src/test/java/p/FooTest.java", (), ("**/*Test*.java",)))
    def test_java_missing_skips_pmd_question(self):
        import shutil as sh
        old, old_pmd = sf.shutil.which, sf.pmd_executable
        sf.shutil.which = lambda name: None if name == "java" else sh.which(name)
        sf.pmd_executable = lambda: Path("/nonexistent/pmd")
        errors, notes = [], []
        try:
            sf.analyze_java(Path("."), ["A.java"], sf.load_rules(), errors, notes)
        finally:
            sf.shutil.which, sf.pmd_executable = old, old_pmd
        self.assertFalse(any("install-pmd" in n for n in notes), notes)
        self.assertTrue(any("java not found" in e for e in errors), errors)
    def test_single_test_source_set_definition(self):
        self.assertNotIn("/src/androidTest/", sf.TEST_SOURCE_SETS)

class ReviewRound14(unittest.TestCase):
    def test_gradle_settings_only_root_keeps_test_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "settings.gradle.kts").write_text("include(\"app\")\n")
            (root / "sonar-project.properties").write_text("sonar.projectKey=x\n")
            (root / "app").mkdir(); (root / "app/build.gradle.kts").write_text("plugins {}\n")
            settings, _, _ = sf.sonar_settings(root)
            layout = sf.test_layout(settings, root)
        self.assertTrue((sf.classify("app/src/test/java/a/ATest.java", layout) == sf.TEST))
    def test_recursion_error_is_a_note(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "deep.py").write_text("x = " + "+".join(["1"] * 200000) + "\n")
            found, note = sf.python_duplicate_literals(Path(d), "deep.py", sf.load_rules()["rules"]["python"])
        self.assertEqual(found, [])
        self.assertTrue(note is None or "S1192 and S5754 checks skipped" in note, note)
    def test_django_tests_module(self):
        self.assertTrue(sf.is_test_path("polls/tests.py"))
    def test_unittest_mock_import_is_not_unittest_style(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "pyproject.toml").write_text("[project]\nname='x'\n")
            (module / "tests").mkdir(); (module / "tests/test_api.py").write_text("from unittest.mock import patch\n\ndef test_x():\n    assert True\n")
            info = sf.python_module(module)
        self.assertIn("pytest", info["test"])
    def test_test_dir_file_outside_test_inclusions_is_out_of_scope(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pom.xml").write_text("<project/>")
            for rel in ("src/test/java/a/TestHelper.java", "src/test/java/a/FooTest.java"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("class A {}\n")
            settings = {"sonar.test.inclusions": "**/*Test.java"}
            selected, excluded, _ = sf.filter_scope(root, ["src/test/java/a/TestHelper.java", "src/test/java/a/FooTest.java"], settings, [])
        self.assertEqual(selected, ["src/test/java/a/FooTest.java"])
        self.assertEqual(excluded.get("outside-sonar.test.inclusions"), 1)

class ReviewRound15(unittest.TestCase):
    def test_new_file_in_tracked_bin_folder_is_kept(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pyproject.toml").write_text("")
            for rel in ("bin/old.py", "bin/new.py", "build/lib/m.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            selected, _, _ = sf.filter_scope(root, ["bin/old.py", "bin/new.py", "build/lib/m.py"], {}, [], True,
                                             {"bin/new.py", "build/lib/m.py"})
        self.assertEqual(sorted(selected), ["bin/new.py", "bin/old.py"])
    def test_unrelated_comment_lines_are_not_a_generator_header(self):
        self.assertFalse(sf.looks_generated("# Config loader: values generated by the CI job are read from env.\n# Do not edit DEFAULTS without updating docs.\nimport os\n"))
    def test_failed_git_is_an_error(self):
        old = sf.git
        sf.git = lambda root, *args: (124, "")
        try:
            with self.assertRaises(sf.GitFailure):
                sf.uncommitted_files(Path("."), True)
        finally:
            sf.git = old
    def test_ruff_target_capped(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ".python-version").write_text("3.16\n")
            self.assertEqual(sf.python_target(Path(d).resolve()), "py315")
    def test_oserror_hint_only_for_e2big(self):
        code, _, err = sf.run_command(["/etc/hosts"])
        self.assertNotIn("argument list too long", err)

class ReviewRound16(unittest.TestCase):
    def test_shared_tests_folder_with_inclusions_keeps_main_code(self):
        layout = sf.TestLayout(("src",), ("**/test_*.py",), ("src",))
        self.assertEqual(sf.classify("src/app.py", layout), "main")
        self.assertEqual(sf.classify("src/test_app.py", layout), "test")
        dedicated = sf.TestLayout(("tests",), ("**/test_*.py",), ("src",))
        self.assertEqual(sf.classify("tests/helpers.py", dedicated), "ignored")
        self.assertEqual(sf.classify("src/app.py", dedicated), "main")
    def test_scope_not_emptied_by_shared_tests_folder(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            for rel in ("src/app.py", "src/test_app.py"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("x = 1\n")
            settings = {"sonar.sources": "src", "sonar.tests": "src", "sonar.test.inclusions": "**/test_*.py"}
            selected, _, _ = sf.filter_scope(root, ["src/app.py", "src/test_app.py"], settings, [])
        self.assertEqual(sorted(selected), ["src/app.py", "src/test_app.py"])
    def test_method_level_generated_and_loose_phrases(self):
        java = "package a;\n\npublic class Repo {\n    @Generated(\"excluded from jacoco\")\n    public int hash() { return 1; }\n}\n"
        self.assertFalse(sf.looks_generated(java))
        self.assertFalse(sf.looks_generated("# Auto-generated IDs are validated below\nimport os\n"))
        self.assertTrue(sf.looks_generated("package z;\n\n@Generated(\"dagger\")\npublic final class A {}\n"))
    def test_venv_folder_names(self):
        with tempfile.TemporaryDirectory() as d:
            module = Path(d).resolve()
            (module / "venv/bin").mkdir(parents=True); (module / "venv/pyvenv.cfg").write_text(""); (module / "venv/bin/python").write_text("")
            self.assertEqual(sf.python_runner(module), "venv/bin/python -m")
    def test_import_check_is_cached(self):
        self.assertTrue(hasattr(sf.python_can_import, "cache_info"))

class ReviewRound17(unittest.TestCase):
    def test_js_max_params_is_s107(self):
        data = sf.load_rules()
        self.assertEqual(data["sonarjs"].get("max-params"), "S107")
        self.assertIn("S107", data["rules"]["javascript"])
        self.assertIn('"max-params": ["error", 7]', sf.ESLINT_CONFIG)
    def test_loose_generated_by_phrases(self):
        for text in ("# Generated by Django 4.2 on 2024-01-01 10:00\nfrom django.db import migrations\n",
                     "# Generated from the pricing table below; keep in sync by hand\nX = 1\n",
                     "# auto-generated file names are skipped by the uploader\nimport os\n"):
            self.assertFalse(sf.looks_generated(text), text)
        self.assertTrue(sf.looks_generated("# Generated by the protocol buffer compiler.  DO NOT EDIT!\n"))
    def test_awaited_bare_except_is_a_decision(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "w.py").write_text("async def g(x):\n    try:\n        await x\n    except:\n        pass\n\ndef h():\n    try:\n        pass\n    except:\n        pass\n")
            data = sf.load_rules()
            items = [sf.finding("w.py", 4, "S5754", "ruff:E722", "bare", data["rules"]["python"]),
                     sf.finding("w.py", 10, "S5754", "ruff:E722", "bare", data["rules"]["python"])]
            sf.mark_s5754_decisions(Path(d), items)
        self.assertEqual([i["action"] for i in items], ["ask", "fix"])
    def test_pom_profiles_ignored(self):
        pom = "<project><groupId>g</groupId><artifactId>a</artifactId><profiles><profile><id>ci</id><properties><sonar.exclusions>src/**</sonar.exclusions></properties></profile></profiles></project>"
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "pom.xml").write_text(pom)
            settings, _, _ = sf.sonar_settings(Path(d))
        self.assertNotIn("sonar.exclusions", settings)

class ReviewRound18(unittest.TestCase):
    def test_bare_except_in_async_with_and_for_is_a_decision(self):
        code = ("async def g(s):\n    try:\n        async with s:\n            pass\n    except:\n        pass\n\n"
                "async def h(it):\n    try:\n        async for x in it:\n            pass\n    except:\n        pass\n")
        self.assertEqual(sf.awaited_bare_except_lines(sf.ast.parse(code)), {5, 12})
    def test_renaming_and_unused_import_rules_check_callers(self):
        self.assertEqual(sf.action_for("S5806", "CODE_SMELL"), "check-api")
        self.assertEqual(sf.action_for("S1128", "CODE_SMELL"), "check-api")

class ReviewRound19(unittest.TestCase):
    def test_findings_on_nosonar_lines_are_dropped_like_sonarqube_does(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "a.py").write_text("def f():\n    x = 1  # NOSONAR\n    y = 2\n    s = '# NOSONAR'\n")
            (root / "b.ts").write_text("const a = 1; // NOSONAR(S1481) kept on purpose\nconst b = 2;\n")
            results = [{"file": "a.py", "line": line, "rule": "S1481"} for line in (2, 3, 4)]
            results += [{"file": "b.ts", "line": line, "rule": "S1481"} for line in (1, 2)]
            kept = sf.without_suppressed(root, results)
            self.assertEqual([(item["file"], item["line"]) for item in kept], [("a.py", 3), ("a.py", 4), ("b.ts", 2)])

    def test_fixture_files_in_test_folder_are_not_counted_as_excluded_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pom.xml").write_text("<project/>")
            for rel in ("src/test/resources/a.json", "src/test/java/a/FooTest.java"):
                (root / rel).parent.mkdir(parents=True, exist_ok=True); (root / rel).write_text("{}\n")
            settings = {"sonar.test.inclusions": "**/*Test.java"}
            selected, excluded, _ = sf.filter_scope(root, ["src/test/resources/a.json", "src/test/java/a/FooTest.java"], settings, [])
        self.assertEqual(selected, ["src/test/java/a/FooTest.java"])
        self.assertEqual(excluded, {"not-source": 1})

class ReviewRound20(unittest.TestCase):
    def test_nosonar_comment_with_apostrophe_or_quote_still_suppresses(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "a.py").write_text("x = \"a b c d\"  # NOSONAR it's ok\ny = \"don't\"  # NOSONAR\ns = '# NOSONAR'\n")
            (root / "b.ts").write_text("const a = 1; // NOSONAR: don't touch\nconst t = `// NOSONAR`;\n")
            results = [{"file": "a.py", "line": line, "rule": "S1192"} for line in (1, 2, 3)]
            results += [{"file": "b.ts", "line": line, "rule": "S1481"} for line in (1, 2)]
            kept = sf.without_suppressed(root, results)
        self.assertEqual([(item["file"], item["line"]) for item in kept], [("a.py", 3), ("b.ts", 2)])
    def test_java_suppress_warnings_with_sonar_key_hides_findings_in_that_element(self):
        source = ("package a;\n"                                   # 1
                  "class A {\n"                                     # 2
                  "    @SuppressWarnings({\"java:S1192\", \"unchecked\"})\n"  # 3
                  "    void f() {\n"                                # 4
                  "        String s = \"}\";\n"                    # 5
                  "        g(\"x y\");\n"                          # 6
                  "    }\n"                                         # 7
                  "    void h() { g(\"x y\"); }\n"                # 8
                  "    @SuppressWarnings(\"squid:S1481\") int v = 1;\n"  # 9
                  "    int w = 2;\n"                                # 10
                  "}\n")
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "A.java").write_text(source)
            results = [{"file": "A.java", "line": line, "rule": rule} for line, rule in
                       [(6, "S1192"), (6, "S1481"), (8, "S1192"), (9, "S1481"), (10, "S1481")]]
            kept = sf.without_suppressed(root, results)
        self.assertEqual([(item["line"], item["rule"]) for item in kept], [(6, "S1481"), (8, "S1192"), (10, "S1481")])
    def test_imported_bare_except_around_await_is_a_decision(self):
        import json, subprocess
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "m.py").write_text("async def f(c):\n    try:\n        await c.get()\n    except:\n        pass\n")
            report = root / "issues.json"
            report.write_text(json.dumps({"issues": [{"key": "1", "rule": "python:S5754", "component": "p:m.py", "line": 4,
                                                     "message": "Specify an exception class to catch or reraise the exception",
                                                     "type": "CODE_SMELL"}],
                                          "components": [{"key": "p:m.py", "path": "m.py"}]}))
            out = subprocess.run([sys.executable, str(SCRIPT), "import", str(root), str(report), "--out", str(root / "f.json")],
                                 capture_output=True, text=True).stdout
        self.assertIn("m.py:4 S5754 ask", out)

class ReviewRound21(unittest.TestCase):
    def test_s5754_follows_sonar_ignored_system_exit_check(self):
        code = ("import sys\n"
                "try:\n    a()\nexcept:\n    raise\n"                          # 4: re-raised
                "try:\n    a()\nexcept:\n    pass\n"                           # 8: bare
                "try:\n    a()\nexcept BaseException:\n    log()\n"            # 12: BaseException
                "try:\n    a()\nexcept (ValueError, SystemExit):\n    pass\n"  # 16: SystemExit
                "try:\n    a()\nexcept SystemExit as e:\n    raise e\n"        # 20: re-raised
                "try:\n    a()\nexcept BaseException:\n    sys.exit(1)\n")     # 24: exits
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text(code)
            found = sf.python_ignored_system_exit(root, "m.py", CATALOG)
            sf.mark_s5754_decisions(root, found)
        self.assertEqual([(item["line"], item["rule"], item["action"]) for item in found],
                         [(8, "S5754", "fix"), (12, "S5754", "fix"), (16, "S5754", "ask")])
    def test_comment_suppression_follows_sonar_python_rules(self):
        cases = [("x = 1  # noqa", "S1481", True), ("x = 1  # noqa: E722", "S5754", False),
                 ("x = 1  # noqa: S1481", "S1481", True), ("x = 1  # noqa: S1481", "S1192", False),
                 ("x = 1  # NOSONAR(S1192)", "S1192", True), ("x = 1  # NOSONAR(S1192)", "S1481", False),
                 ("x = 1  # type: ignore  # noqa", "S1481", True), ("s = '# noqa'", "S1481", False)]
        for line, rule, hidden in cases:
            self.assertEqual(sf.comment_suppresses(line, rule, "python"), hidden, line + " " + rule)
        self.assertTrue(sf.comment_suppresses("int a = 1; // NOSONAR", "S1481", "java"))
        self.assertFalse(sf.comment_suppresses("int a = 1; // noqa", "S1481", "java"))
    def test_nested_coroutine_definition_does_not_make_try_suspend(self):
        code = "try:\n    async def cb():\n        await x()\n    register(cb)\nexcept:\n    pass\n"
        self.assertEqual(sf.awaited_bare_except_lines(sf.ast.parse(code)), set())
    def test_module_extras_quote_values_with_spaces(self):
        self.assertEqual(sf.module_extras({"node": ">=18 <20", "typecheck": "npx tsc"}), 'node=">=18 <20" typecheck="npx tsc"')
        self.assertEqual(sf.module_extras({"node": "20"}), "node=20")

class ReviewRound22(unittest.TestCase):
    def run_import(self, source, line):
        import json, subprocess
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text(source)
            report = root / "issues.json"
            report.write_text(json.dumps({"issues": [{"key": "1", "rule": "python:S5754", "component": "p:m.py", "line": line,
                                                     "message": "Reraise this exception", "type": "CODE_SMELL"}],
                                          "components": [{"key": "p:m.py", "path": "m.py"}]}))
            return subprocess.run([sys.executable, str(SCRIPT), "import", str(root), str(report), "--out", str(root / "f.json")],
                                  capture_output=True, text=True).stdout
    def test_imported_system_exit_handler_is_a_decision(self):
        self.assertIn("m.py:4 S5754 ask", self.run_import("try:\n    a()\n\nexcept SystemExit:\n    pass\n", 4))
    def hidden(self, name, source, findings):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / name).write_text(source)
            kept = sf.without_suppressed(root, [{"file": name, "line": line, "rule": rule} for line, rule in findings])
        return [(item["line"], item["rule"]) for item in kept]
    def test_java_suppression_skips_following_annotations_with_arrays(self):
        source = ("class A {\n    @SuppressWarnings(\"java:S1481\")\n    @Anno(value = {\"a\"})\n"
                  "    public void m() {\n        int x = 1;\n    }\n    void n() { int y = 1; }\n}\n")
        self.assertEqual(self.hidden("A.java", source, [(5, "S1481"), (7, "S1481")]), [(7, "S1481")])
    def test_java_all_javac_keys_and_old_squid_keys_follow_sonarjava(self):
        source = ("class A {\n    @SuppressWarnings(\"all\")\n    void a() { x(); }\n"           # 2-3
                  "    @SuppressWarnings({\"unused\", \"parameternumber\"})\n    void b(int p) { int y = 1; }\n"  # 4-5
                  "    @SuppressWarnings(\"squid:S00107\")\n    void c(int q) { }\n"          # 6-7
                  "    void d(int r) { int z = 1; }\n}\n")                                     # 8
        findings = [(3, "S3776"), (5, "S1481"), (5, "S107"), (5, "S3776"), (7, "S107"), (8, "S107"), (8, "S1481")]
        self.assertEqual(self.hidden("A.java", source, findings), [(5, "S3776"), (8, "S107"), (8, "S1481")])
    def test_kotlin_suppress_with_sonar_key_hides_function_findings(self):
        source = ("class K {\n    @Suppress(\"kotlin:S3776\")\n    fun big(a: Int): Int {\n        return a\n    }\n"
                  "    fun other(a: Int): Int = a\n}\n")
        self.assertEqual(self.hidden("K.kt", source, [(3, "S3776"), (3, "S107"), (6, "S3776")]), [(3, "S107"), (6, "S3776")])
    def test_s1192_message_lists_each_line_once(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text('def f():\n    return "hello world", "hello world", "hello world"\n')
            found, _ = sf.python_duplicate_literals(root, "m.py", CATALOG)
        self.assertIn("3 times (lines 2)", found[0]["message"])

    def test_root_sonar_properties_wins_over_nested_maven_example(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "sonar-project.properties").write_text("sonar.projectKey=x\nsonar.sources=.\n")
            (root / "examples/java-client").mkdir(parents=True); (root / "examples/java-client/pom.xml").write_text("<project/>")
            layout = sf.test_layout({"sonar.projectKey": "x", "sonar.sources": "."}, root)
        self.assertTrue(layout.everything_main)

class ReviewRound23(unittest.TestCase):
    def test_multiline_except_tuple_is_one_s5754_not_also_broad_except(self):
        results = [{"file": "m.py", "line": 7, "rule": "BROAD-EXCEPT"}, {"file": "m.py", "line": 12, "rule": "BROAD-EXCEPT"}]
        code = ("def f():\n    try:\n        a()\n    except (\n        ValueError,\n"
                "        OSError,\n        BaseException,\n    ):\n        log()\n    try:\n        a()\n    except Exception:\n        log()\n")
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text(code)
            found = sf.python_ignored_system_exit(root, "m.py", CATALOG)
            kept = sf.without_covered_broad_excepts(root, results + found)
        self.assertEqual(sorted((item["line"], item["rule"]) for item in kept), [(4, "S5754"), (12, "BROAD-EXCEPT")])
    def test_except_star_base_exception_around_await_is_a_decision(self):
        if sys.version_info < (3, 11):
            self.skipTest("except* needs Python 3.11")
        code = "async def f(c):\n    try:\n        await c.get()\n    except* BaseException:\n        log()\n"
        self.assertIn(4, sf.awaited_bare_except_lines(sf.ast.parse(code)))

class ReviewRound24(unittest.TestCase):
    def test_unparsable_file_keeps_s5754_as_a_decision(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text("def (:\n")
            results = [{"file": "m.py", "line": 1, "rule": "S5754", "action": "fix"}]
            sf.mark_s5754_decisions(root, results)
        self.assertEqual(results[0]["action"], "ask")
    def test_parse_skip_note_names_every_builtin_python_check(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text("def (:\n")
            _, note = sf.python_duplicate_literals(root, "m.py", CATALOG)
        self.assertIn("S1192 and S5754 checks skipped", note)
    def test_module_relative_test_inclusions_in_multi_module_build(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "pom.xml").write_text("<project/>")
            (root / "mod").mkdir(); (root / "mod/pom.xml").write_text("<project/>")
            rel = "mod/src/test/java/a/ATest.java"
            (root / rel).parent.mkdir(parents=True); (root / rel).write_text("class ATest {}\n")
            settings = {"sonar.test.inclusions": "src/test/**/*Test.java"}
            selected, excluded, layout = sf.filter_scope(root, [rel], settings)
            self.assertEqual(selected, [rel])
            self.assertEqual(sf.classify(rel, layout), sf.TEST)
    def test_src_main_folder_outside_jvm_does_not_hide_test_names(self):
        self.assertTrue(sf.is_test_path("src/main/__tests__/a.test.ts"))
        self.assertFalse(sf.is_test_path("src/main/java/a/TestUtils.java"))

class ReviewRound25(unittest.TestCase):
    def test_bun_runs_the_package_test_script(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "package.json").write_text('{"scripts": {"test": "vitest run"}}')
            (root / "bun.lock").write_text("")
            self.assertTrue(sf.node_module(root)["test"].startswith("bun run test"))

class ReviewRound26(unittest.TestCase):
    def test_plain_script_python_project_gets_a_module_with_tests(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "app.py").write_text("def f():\n    return 1\n")
            (root / "tests").mkdir(); (root / "tests/test_app.py").write_text("def test_f():\n    assert True\n")
            modules = sf.discover_modules(root)
        self.assertEqual([(relative, module["ecosystem"]) for relative, module in modules], [(".", "python")])
        self.assertNotIn("none", modules[0][1]["test"])
    def test_unborn_branch_is_named_not_head(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            subprocess.run(["git", "init", "-q", "-b", "feature", str(root)], check=True)
            _, branch, _, _ = sf.git_root_state(root)
        self.assertEqual(branch, "feature")
    def test_generated_exclusions_are_listed_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "a.py").write_text("# Code generated by protoc. DO NOT EDIT.\nx = 1\n")
            (root / "b.py").write_text("x = 1\n")
            generated: list = []
            selected, excluded, _ = sf.filter_scope(root, ["a.py", "b.py"], {}, [], generated=generated)
        self.assertEqual((selected, generated), (["b.py"], ["a.py"]))

class ReviewRound27(unittest.TestCase):
    def test_parameter_annotation_does_not_hide_the_method_body(self):
        source = "class A {\n    void f(@SuppressWarnings(\"unused\") int a) {\n        int x = 1;\n    }\n}\n"
        hidden = sf.annotation_suppressed_lines(source, False)
        self.assertNotIn(3, hidden.get("S1481", set()))
    def test_escaped_trailing_backslash_does_not_join_lines(self):
        self.assertEqual([line for _, line in sf.logical_lines("a=x\\\\\nb=y\nc=1\\\n  2\n")],
                         ["a=x\\\\", "b=y", "c=12"])
    def test_imported_s5754_on_a_later_tuple_line_is_a_decision(self):
        code = "async def f(x):\n    try:\n        await x()\n    except (\n        ValueError,\n        BaseException,\n    ):\n        pass\n"
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text(code)
            results = [{"file": "m.py", "line": 6, "rule": "S5754", "action": "fix"}]
            sf.mark_s5754_decisions(root, results)
        self.assertEqual(results[0]["action"], "ask")

class ReviewRound28(unittest.TestCase):
    def test_suppression_line_lookup_counts_only_newlines(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text("import os\n\x0c\n\ndef f():\n    x = 1  # NOSONAR\n")
            kept = sf.without_suppressed(root, [{"file": "m.py", "line": 5, "rule": "S1481"}])
        self.assertEqual(kept, [])
    def test_brace_inside_parameter_annotation_does_not_end_method_range(self):
        source = ("class A {\n    @SuppressWarnings(\"java:S1192\")\n    void f(@Ann({\"a\"}) int x) {\n"
                  "        String s = \"hello\";\n    }\n}\n")
        self.assertIn(4, sf.annotation_suppressed_lines(source, False)["S1192"])
    def test_bare_except_around_explicit_exit_is_a_decision(self):
        code = "import sys\ndef g():\n    try:\n        sys.exit(1)\n    except:\n        pass\n"
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); (root / "m.py").write_text(code)
            results = [{"file": "m.py", "line": 5, "rule": "S5754", "action": "fix"}]
            sf.mark_s5754_decisions(root, results)
        self.assertEqual(results[0]["action"], "ask")

class ReviewRound29(unittest.TestCase):
    def mark(self, files, line):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            for name, code in files.items():
                (root / name).write_text(code)
            results = [{"file": "m.py", "line": line, "rule": "S5754", "action": "fix"}]
            sf.mark_s5754_decisions(root, results)
        return results[0]["action"]
    def test_exit_imported_from_sys_or_builtin_quit_is_a_decision(self):
        self.assertEqual(self.mark({"m.py": "from sys import exit\ntry:\n    exit(2)\nexcept:\n    pass\n"}, 4), "ask")
        self.assertEqual(self.mark({"m.py": "try:\n    quit()\nexcept:\n    pass\n"}, 3), "ask")
    def test_missing_file_keeps_s5754_as_a_decision(self):
        self.assertEqual(self.mark({}, 4), "ask")
    def test_deep_python_sources_without_packaging_get_a_module(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            (root / "tools/scripts").mkdir(parents=True); (root / "tools/scripts/build.py").write_text("x = 1\n")
            modules = sf.discover_modules(root)
        self.assertEqual([(relative, module["ecosystem"]) for relative, module in modules], [(".", "python")])

class InstallPmd(unittest.TestCase):
    def test_interrupted_download_leaves_no_partial_zip(self):
        import os, io
        class Broken(io.BytesIO):
            def read(self, *args):
                raise OSError("connection reset")
            def __enter__(self): return self
            def __exit__(self, *args): return False
        with tempfile.TemporaryDirectory() as d:
            old_env, old_open = os.environ.get("XDG_CACHE_HOME"), sf.urllib.request.urlopen
            os.environ["XDG_CACHE_HOME"] = d
            sf.urllib.request.urlopen = lambda *a, **k: Broken()
            try:
                code = sf.command_install_pmd(None)
            finally:
                sf.urllib.request.urlopen = old_open
                if old_env is None: os.environ.pop("XDG_CACHE_HOME")
                else: os.environ["XDG_CACHE_HOME"] = old_env
            self.assertEqual(code, 1)
            self.assertEqual(list(Path(d).rglob("*.zip")), [])

if __name__ == "__main__":
    unittest.main()
