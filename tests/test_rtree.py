import unittest
import os
import shutil
import tempfile
import sys

# Ensure import of tree from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tree import RepoTreeVisualizer

class TestRepoTree(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content=""):
        full_path = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_flat_list_structure(self):
        """Test that flat list mode finds the correct files."""
        self.create_file("src/main.py")
        self.create_file("src/utils.py")
        self.create_file("README.md")

        viz = RepoTreeVisualizer(self.test_dir, use_color=False)
        lines = viz.get_flat_list()
        
        # expect paths relative to root
        self.assertIn("src/main.py", lines)
        self.assertIn("src/utils.py", lines)
        self.assertIn("README.md", lines)

    def test_gitignore_fallback(self):
        """
        Test that .gitignore works even WITHOUT a real .git folder.
        This verifies the 'manual parser' fallback logic.
        """
        # 1. Create a .gitignore
        self.create_file(".gitignore", "*.log\nsecret/")
        
        # 2. Create ignored content
        self.create_file("error.log")
        self.create_file("secret/key.txt")
        
        # 3. Create valid content
        self.create_file("app.py")

        viz = RepoTreeVisualizer(self.test_dir, use_color=False)
        lines = viz.get_flat_list()

        self.assertIn("app.py", lines)
        self.assertNotIn("error.log", lines)
        self.assertNotIn("secret/key.txt", lines)
        # .gitignore itself is usually visible
        self.assertIn(".gitignore", lines)

    def test_max_depth(self):
        """Test that --depth limits recursion."""
        self.create_file("level1/level2/level3/deep.txt")
        
        # Limit to depth 1
        viz = RepoTreeVisualizer(self.test_dir, max_depth=1, use_color=False)
        lines = viz.get_flat_list()

        # Should see level1/
        self.assertTrue(any("level1/" in x for x in lines))
        # Should NOT see level3
        self.assertFalse(any("level3" in x for x in lines))

    def test_ascii_tree_generation(self):
        """Basic check that the ASCII tree returns lines."""
        self.create_file("test.py")
        viz = RepoTreeVisualizer(self.test_dir, use_color=False)
        tree = viz.get_ascii_tree()
        
        # First line is usually the root folder name
        self.assertTrue(len(tree) > 0)
        # Check for tree characters
        self.assertTrue(any("test.py" in line for line in tree))

if __name__ == '__main__':
    unittest.main()