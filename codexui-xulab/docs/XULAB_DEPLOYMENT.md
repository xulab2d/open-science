# Xu Lab Deployment Notes

This fork is intended to run behind external access control.

Default assumptions:
- authentication is handled by Cloudflare Access or another reverse proxy
- the app has no built-in password gate
- the app should be reachable only through the external access layer when exposed remotely

Current fork-specific changes:
- removed the GitHub trending-projects panel from the home screen
- removed the old password-gate path from the server and CLI
- updated package metadata and startup text for the Xu Lab variant
