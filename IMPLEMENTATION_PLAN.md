# Restrict WhatsApp Bot to Owner

## Goal
Stop the bot from replying to everyone in group chats or other users. It should only reply to the Owner.

## Changes

### 1. `skills/wacli/server.js`
- **Load Environment**: Add `dotenv` to load `WHATSAPP_NUMBER`.
- **Filter Logic**:
  - Check `msg.from`.
  - If `msg.from` == `process.env.WHATSAPP_NUMBER` (plus suffix handling), Process.
  - If `msg.from` contains `@g.us` (Group), Ignore.
  - If `msg.from` != Owner, Ignore.

### 2. Deployment
- Use `deploy_clawbrain.sh` from the new `ClawBrain` workspace.
- Restart service on EC2.

## Verification
- User sends message -> Reply.
- Group chat message -> No Reply.
