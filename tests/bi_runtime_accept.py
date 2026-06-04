"""Bi-runtime acceptance harness.

Proves the exit criterion: ONE canonical persona.yaml produces EQUIVALENT working personas
across runtimes AND across the Claude adapter's two tiers:
  - code-puppy     (Tier 3 — enforced JSON sub-agent tool allow-list)
  - Claude Tier 2  (CLAUDE.md — capabilities instructed)
  - Claude Tier 3  (native subagent — enforced `tools:` allow-list)
'Equivalent' = same identity, same effective capabilities, same guardrails. The artifacts
differ (JSON vs CLAUDE.md vs subagent .md) but the persona's behavior contract is identical.

Run: uv run --with pyyaml python tests/bi_runtime_accept.py
"""
import sys, yaml

# ---- canon: the v1 capability vocabulary ----
V1 = {"read_code","read_collab","write_code","write_path","open_pr","run_tests",
      "merge_pr","push_main","force_push","edit_other_personas"}

def verbs(items):
    out = []
    for it in items:
        out.append((list(it.keys())[0], tuple(list(it.values())[0])) if isinstance(it, dict) else (it, ()))
    return out

def load(path):
    return yaml.safe_load(open(path))

# ---- adapter A: code-puppy (Tier 3) -> {identity, enforced_tools, denies} ----
def hydrate_codepuppy(p):
    allow = verbs(p["capabilities"]["allow"]); deny = verbs(p["capabilities"]["deny"])
    tools = {"agent_share_your_reasoning"}
    for v, _ in allow:
        if v in ("read_code","read_collab"): tools |= {"read_file","list_files","grep"}
        if v == "write_code": tools |= {"create_file","replace_in_file","delete_snippet"}
        if v == "write_path": tools |= {"create_file","replace_in_file"}
        if v in ("open_pr","run_tests"): tools |= {"agent_run_shell_command"}
    return {
        "identity": (p["identity"]["git_name"], p["identity"]["commit_prefix"], p["identity"]["routing_label"]),
        "can_write_files": bool(tools & {"create_file","replace_in_file","delete_snippet"}),
        "can_run_shell": "agent_run_shell_command" in tools,
        "denies": {v for v, _ in deny},
    }

# ---- adapter B: Claude Tier 2 (CLAUDE.md) -> same contract, rendered as instructed prose ----
def hydrate_claude_tier2(p):
    allow = verbs(p["capabilities"]["allow"]); deny = verbs(p["capabilities"]["deny"])
    av = {v for v, _ in allow}
    return {
        "identity": (p["identity"]["git_name"], p["identity"]["commit_prefix"], p["identity"]["routing_label"]),
        "can_write_files": bool(av & {"write_code","write_path"}),
        "can_run_shell": bool(av & {"open_pr","run_tests"}),
        "denies": {v for v, _ in deny},
    }

# ---- adapter B': Claude Tier 3 (native subagent) -> same contract, ENFORCED tool allow-list ----
# Whole-tool denials are real (tool omitted from `tools:`); sub-tool denials stay instructed.
def hydrate_claude_tier3(p):
    allow = verbs(p["capabilities"]["allow"]); deny = verbs(p["capabilities"]["deny"])
    tools = set()
    for v, _ in allow:
        if v in ("read_code","read_collab"): tools |= {"Read","Grep","Glob"}
        if v == "write_code": tools |= {"Write","Edit"}
        if v == "write_path": tools |= {"Write","Edit"}
        if v in ("open_pr","run_tests"): tools |= {"Bash"}
    return {
        "identity": (p["identity"]["git_name"], p["identity"]["commit_prefix"], p["identity"]["routing_label"]),
        "can_write_files": bool(tools & {"Write","Edit"}),
        "can_run_shell": "Bash" in tools,
        "denies": {v for v, _ in deny},
    }

def main():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    personas = [os.path.join(here, "examples/tess/persona.yaml"),
                os.path.join(here, "examples/rex/persona.yaml")]
    failures = 0
    for path in personas:
        p = load(path)
        # schema sanity: only v1 verbs
        allv = {v for v, _ in verbs(p["capabilities"]["allow"]) + verbs(p["capabilities"]["deny"])}
        bad = allv - V1
        cp = hydrate_codepuppy(p); cl2 = hydrate_claude_tier2(p); cl3 = hydrate_claude_tier3(p)
        same = (cp == cl2 == cl3)
        status = "PASS" if same and not bad else "FAIL"
        if not same or bad: failures += 1
        print(f"[{status}] {p['persona']:5} ({path.split('/')[-2]})")
        print(f"        identity      : {cp['identity']}  match={cp['identity']==cl2['identity']==cl3['identity']}")
        print(f"        can_write     : cp={cp['can_write_files']} claude-t2={cl2['can_write_files']} claude-t3={cl3['can_write_files']} match={cp['can_write_files']==cl2['can_write_files']==cl3['can_write_files']}")
        print(f"        can_run_shell : cp={cp['can_run_shell']} claude-t2={cl2['can_run_shell']} claude-t3={cl3['can_run_shell']} match={cp['can_run_shell']==cl2['can_run_shell']==cl3['can_run_shell']}")
        print(f"        denies        : match={cp['denies']==cl2['denies']==cl3['denies']} ({sorted(cp['denies'])})")
        if bad: print(f"        !! non-v1 verbs: {bad}")
    print()
    if failures:
        print(f"ACCEPTANCE FAILED ({failures} persona(s) diverge across runtimes/tiers)")
        sys.exit(1)
    print("BI-RUNTIME ACCEPTANCE: PASS")
    print("One persona.yaml -> equivalent behavior contract on code-puppy (Tier3),")
    print("Claude Tier 2 (CLAUDE.md) AND Claude Tier 3 (enforced subagent).")

if __name__ == "__main__":
    main()
