# Founder Written Conversation Surface

Status: trusted built-in local conversation scene

## Purpose

The Founder interface now has a protected written surface that talks to Runtime through the narrow local conversation Unix socket.

```text
QtWrittenConversationWidget
        |
        v
UnixConversationClient
        |
        | AF_UNIX
        v
Velvet Runtime conversation service
        |
        +--> Core grounded meaning
        +--> Language expression
```

Interface does not import Core, inspect body-state records, authorize actions, or execute anything.

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

Open the scene with:

```text
Ctrl+Alt+C
```

This avoids changing the current Founder room artwork, press points, or navigation maps. A visible room entrance can be added later as a normal navigation press point after the surface is proven on-device.

## Runtime service

Runtime's conversation socket must be enabled separately:

```bash
export VELVET_CONVERSATION_SOCKET_ENABLED=true
```

Default endpoint:

```text
/run/velvet/conversation.sock
```

The launcher also accepts:

```bash
--conversation-socket /run/velvet/conversation.sock
```

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
