# LSU v3.2 environment snapshot

captured_at_utc: 2026-11-06T01:58:30Z
worktree: /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2
git_branch: lsu-platform-v3.2
git_commit: 6f98088a7144d7f6fb22d985be3023ac5658e71b
git_status_porcelain:
  ?? docs/gem5-fi/lsu/implementation_v3_2/
  ?? docs/superpowers/plans/2026-11-06-lsu-platform-v3.2.md
uname: Linux localhost0101 6.6.0-145.3.16.148.oe2403sp3.aarch64 #1 SMP Mon Jun 22 19:55:09 CST 2026 aarch64 aarch64 aarch64 GNU/Linux
gcc: gcc (GCC) 12.3.1 (openEuler 12.3.1-111.oe2403sp3)
python: Python 3.11.6
scons: 	SCons: v4.5.2, Sun, 21 Dec 2025 11:53:56 +0800, by lkp on dc-64g
gem5_source_commit_file: # Base upstream gem5 version for this vendored source tree (CHAOS/gem5/). # Record of the official gem5 release this repo's gem5/ source is based on. # # To refresh from upstream: #   git clone https://github.com/gem5/gem5 CHAOS/gem5 #   git -C CHAOS/gem5 checkout stable #   git -C CHAOS/gem5 checkout 62c7bf284864b83f7308f5e14ca9c80812621c29  Upstream:       https://github.com/gem5/gem5 Branch:         stable Tag (nearest):  v25.1.0.1 git describe:   v25.1.0.1-6-g62c7bf2848   # 6 commits past tag v25.1.0.1 Commit:         62c7bf284864b83f7308f5e14ca9c80812621c29 Commit subject: misc: add GitHub Agentic Workflow to summarize weekly activity to stable (#3391) Recorded on:    2026-08-24  # CHAOS integration layered on top of this base (NOT part of upstream): #   src/CHAOSReg/, src/mem/CHAOSMem/, src/mem/cache/CHAOSCache/   (in this commit) #   src/cpu/o3/CHAOSPhysReg/ + o3 hooks in cpu.hh/free_list.hh/regfile.hh #       (deferred to a follow-up patch) 
worktree_gem5_opt: ABSENT
main_repo_gem5_opt_sha256: 6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4  /home/sdc/gem5-fi-ding/build/ARM/gem5.opt
disk: /dev/mapper/openeuler-home  354G  300G   36G   90% /home
