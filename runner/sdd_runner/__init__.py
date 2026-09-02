"""sdd_runner — phase-2 executor for the SDD autonomous loop.

The protocol this package implements is NOT defined here. It is defined by
spec 031 (`autonomous-orchestration-loop`) and corrected by spec 032
(`autonomous-loop-residual-calibration`). Every module that encodes a rule from
031 names the FR it implements in its module docstring, so a future change to
031 has a findable set of call sites.

Where this runner and `skills/sdd-orchestrate/SKILL.md` disagree, THIS RUNNER IS
WRONG (spec 040, D007). Semantic changes go through /spec-update against 031.
"""

__version__ = "0.1.0"
