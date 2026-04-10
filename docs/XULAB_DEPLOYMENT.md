# Xu Lab Deployment Notes

This fork is intended to run behind external access control.

Default assumptions:
- authentication is handled by Cloudflare Access or another reverse proxy
- the app's built-in password gate is disabled by default
- the app should be reachable only through the external access layer when exposed remotely

Current fork-specific changes:
- removed the GitHub trending-projects panel from the home screen
- changed CLI defaults so password auth is opt-in instead of auto-generated
- updated package metadata and startup text for the Xu Lab variant

Fallback:
- if external auth is temporarily unavailable, the built-in password gate can still be enabled with:

```bash
node dist-cli/index.js --password <secret>
```
