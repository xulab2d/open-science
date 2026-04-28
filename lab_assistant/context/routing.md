# Routing

Default routing model:
- Project-specific scientific or metadata questions: route to the project owners.
- Tooling, behavior, or workflow questions: route to the workspace maintainer.
- High-level summary expectations: align with PI-facing preferences already recorded in this workspace.
- If a scientific conclusion depends on project-owner context, ask a narrow clarification on Slack rather than leaving the question as passive follow-up.
- Use DMs for targeted owner questions and `#open-science` for questions whose answer should be shared with the lab.
- Default rule: if a question is tied to one project or one owner pair, DM the mapped owners first. Do not post project-specific clarification questions to `#open-science` unless the answer is expected to help the broader lab immediately, the owners are unclear, or a DM attempt already failed.
- When a Slack reply resolves a scientific uncertainty, update the relevant project note, synthesis, fact graph, or memory file so the answer is not lost in Slack history.
- OpenScience-specific interaction capabilities such as rendered LaTeX and file-backed image uploads should remain available in-context for browser-based turns; keep Slack output plain-text and channel-appropriate.

Known owner shortcuts:
- `CWB` usually indicates Christiano Wang Beach.
- `WJL` usually indicates Weijie Li.
- `ZDS` usually indicates Zengde She.

Current confirmed project roots:
- `/Volumes/Xu Lab/tMoTe2_Measuring/CWB_Yifan_D93_Run2_attodry522`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Shuai-MT43-DR911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/WJL_Zengde_B79_Attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_WJL_C7_Attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/Zengde_Weijie_A5_AAtA_dot_oldattodry`
- `/Volumes/Xu Lab/tMoTe2_Measuring/courtney_christiano_D88_1+1+1_AAA_4deg_attodry911`
- `/Volumes/Xu Lab/tMoTe2_Measuring/courtney_christiano_D88_run2_AAA_attodry522`

Current confirmed summary root:
- `/Volumes/Xu Lab/OpenScience/Summaries/PPT`

Slack clarification helper:
- `python3 lab_assistant/integrations/slack/post_clarification.py --person christiano_wang_beach --message "..."`
- `python3 lab_assistant/integrations/slack/post_clarification.py --person yi_fan_zhao --message "..."`
- `python3 lab_assistant/integrations/slack/post_clarification.py --person zengde_she --message "..."`
- `python3 lab_assistant/integrations/slack/post_clarification.py --person weijie_li --message "..."`
- `python3 lab_assistant/integrations/slack/post_clarification.py --channel open-science --message "..."`
