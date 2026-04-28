# Slack Routing Setup

Status:
- Workspace is now organized so Slack can be added as a thin interface layer.

What should exist before wiring it up:
1. A small Slack config file with:
- bot/app identifiers
- default channel or DM behavior
- user-id mapping for recurring lab members
2. A message adapter that:
- receives Slack events
- resolves thread/user context
- invokes the core assistant workflow
- formats the final reply for Slack
3. A routing file derived from canonical workspace context, not a second source of truth

Recommended config shape:
```json
{
  "summary_root": "/Volumes/Xu Lab/OpenScience/Summaries/PPT",
  "project_data_root": "/Volumes/Xu Lab/tMoTe2_Measuring",
  "people": {
    "isaac_van_orman": {"slack_user_id": ""},
    "christiano_wang_beach": {"slack_user_id": ""},
    "courtney": {"slack_user_id": ""},
    "yi_fan_zhao": {"slack_user_id": ""},
    "shuai_yuan": {"slack_user_id": ""},
    "weijie_li": {"slack_user_id": ""},
    "zengde_she": {"slack_user_id": ""}
  }
}
```

Routing rules to preserve:
- project questions go to project owners
- tooling questions go to the maintainer
- message formatting is Slack-specific, but reasoning and memory updates are not

Next step after this workspace pass:
- create a dedicated Slack config file and adapter directory under `lab_assistant/integrations/slack/`

Status after current pass:
- directory created: `lab_assistant/integrations/slack/`
- template created: `lab_assistant/integrations/slack/routing.template.json`
- Slack IDs recovered from the legacy workspace
- minimal Socket Mode bridge added
- remaining task: run the bridge outside this sandbox and verify event subscriptions/scopes
