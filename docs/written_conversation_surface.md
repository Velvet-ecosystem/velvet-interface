# Founder Written Conversation Surface

Status: trusted built-in local conversation scene

## Purpose

The Founder interface now has a protected written surface that talks to Runtime through the narrow local conversation Unix socket.

```text
QtWrittenConversationWidget
        |
        v
UnixConversationBridge
        |
        | AF_UNIX
        v
Velvet Runtime conversation service
        |
        +--> Core grounded meaning
        +--> Language expression
```

Interface owns only the narrow Unix client. It does not import Runtime, Core, inspect body-state records, authorize actions, or execute anything.

## Access

The scene is a trusted built-in scene rather than a manifest-loaded capability. It requires either:

```text
VELVET_OWNER_PRESENT=true
```

or:

```text
VELVET_MAINTENANCE_UNLOCKED=true
```

Presentation mode alone is not treated as proof of owner identity.

Open the scene from the Founder Home VELVET presence hotspot or with:

```text
Ctrl+Alt+C
```

## Runtime service

Runtime owns the server side of the conversation socket. Deployed/default endpoint:

```text
/run/velvet/conversation.sock
```

The launcher also accepts:

```bash
--conversation-socket /run/velvet/conversation.sock
```

Repo-local development Runtime uses its own writable `.velvet-dev/run/conversation.sock`. When Interface and Runtime are sibling checkouts, use:

```bash
bash scripts/run_founder_dev.sh
```

That helper binds Interface to Runtime's development boot snapshot and conversation socket without changing production defaults. Runtime must still be running and its optional conversation service must be active.

To omit the scene entirely:

```bash
--disable-written-conversation
```

## Interaction

The transcript uses plain text only. Human input is bounded to 4096 characters. A turn is submitted asynchronously so local Runtime or grounding latency does not block Qt navigation or repainting.

Every reply is validated again at the Interface boundary. The surface rejects any reply that claims:

- authority granted
- execution granted
- actuation granted

Action-like text may still display that Runtime authorization is required; the Interface does not perform that authorization.

## First useful questions

With current body records available, examples include:

```text
What is the cabin temperature?
Can you tell me the outside temperature?
Is the ignition on
What is the vehicle voltage?
How fast are we going?
Tell me the cabin humidity
```

If evidence is missing, stale, or insufficient, the shared conversation path retains its established truthful wording instead of fabricating a value.
