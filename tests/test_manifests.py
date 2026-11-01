"""Keeps the plugin manifests, pyproject.toml and SKILL.md in step.

The same version is declared in six places; a release that bumps only some of
them installs a different version depending on the agent.
Run with: python -m unittest discover -s tests
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# top-level keys allowed by https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
PORTABLE_KEYS = {"$schema", "name", "version", "description", "author", "homepage",
                 "repository", "license", "keywords", "extensions"}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.portable = load("plugin.json")
        self.claude = load(".claude-plugin/plugin.json")
        self.marketplace = load(".claude-plugin/marketplace.json")
        self.codex = load(".codex-plugin/plugin.json")

    def test_versions_match(self):
        skill = (ROOT / "skills/truegreen/SKILL.md").read_text(encoding="utf-8")
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        versions = {
            "plugin.json": self.portable["version"],
            ".claude-plugin/plugin.json": self.claude["version"],
            ".claude-plugin/marketplace.json": self.marketplace["plugins"][0]["version"],
            ".codex-plugin/plugin.json": self.codex["version"],
            "pyproject.toml": re.search(r'^version = "([^"]+)"', pyproject, re.M).group(1),
            "SKILL.md": re.search(r'^  version: "([^"]+)"', skill, re.M).group(1),
        }
        self.assertEqual(len(set(versions.values())), 1, versions)

    def test_names_match(self):
        names = {self.portable["name"], self.claude["name"], self.codex["name"],
                 self.marketplace["plugins"][0]["name"]}
        self.assertEqual(names, {"truegreen"})

    def test_portable_manifest_fits_schema(self):
        self.assertEqual(self.portable["$schema"],
                         "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json")
        self.assertLessEqual(set(self.portable), PORTABLE_KEYS)

    def test_codex_interface(self):
        self.assertEqual(self.codex["skills"], "./skills/")
        ui = self.codex["interface"]
        for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
            self.assertTrue(ui.get(key), key)
        self.assertLessEqual(len(ui["defaultPrompt"]), 3)
        for prompt in ui["defaultPrompt"]:
            self.assertLessEqual(len(prompt), 128, prompt)


if __name__ == "__main__":
    unittest.main()
