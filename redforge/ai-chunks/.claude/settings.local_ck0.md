<!-- source: .claude/settings.local.json idx:0 lines:53 -->

```json
{
  "permissions": {
    "allow": [
      "Bash(ls:*)",
      "Bash(find:*)",
      "Bash(python:*)",
      "Bash(make:*)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli --help)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike make -f /Users/siwenwang/PromptStrike/makefile install)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"import sys; sys.path.insert(0, ''/Users/siwenwang/PromptStrike''); from promptstrike.cli import app; app()\")",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli version)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli doctor)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli list-attacks)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli scan test-target --dry-run)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli config --show)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli config --create)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"import typer, click; print(f''typer: {typer.__version__}, click: {click.__version__}'')\")",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"import typer; print(''Typer version:'', typer.__version__); from typer.rich_utils import _print_options_panel; print(''Rich utils available'')\")",
      "Bash(pip install:*)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"import typer; print(''Typer version:'', typer.__version__)\")",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike grep -n \"typer.Option.*Path\" /Users/siwenwang/PromptStrike/promptstrike/cli.py)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike rg -n \"Path.*=\" /Users/siwenwang/PromptStrike/promptstrike/cli.py)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli scan --help)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"from typer import models; print(dir(models))\")",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -c \"import typer; print(dir(typer)); from typer.core import TyperArgument; print(''TyperArgument found'')\")",
      "Bash(/dev/null)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py -v)",
      "Bash(grep:*)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::test_version_command -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_cli_help -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_version_command -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_doctor_command -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_list_attacks_command -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_scan_dry_run -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py -k \"not (slow or integration)\" --maxfail=5 -x -q)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py -k \"not (slow or integration or scan_help)\" --maxfail=5 -q)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli config --help)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli doctor --help)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli version --help)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m pytest /Users/siwenwang/PromptStrike/tests/test_cli.py::TestCLICommands::test_scan_help -v)",
      "Bash(PYTHONPATH=/Users/siwenwang/PromptStrike python -m promptstrike.cli list-attacks --help)",
      "Bash(git add:*)",
      "Bash(git push:*)",
      "Bash(ssh-add:*)",
      "Bash(git commit:*)",
      "Bash(git checkout:*)",
      "Bash(promptstrike doctor:*)",
      "Bash(promptstrike list-attacks:*)",
      "Bash(pip show:*)"
    ],
    "deny": []
  }
}
```