#!/usr/bin/env python3
"""iTerm2 companion script for the terminal plant banner (optional; iTerm2 only).

Escape codes can't reach everything in iTerm2: there is none for the cursor guide's colour, and
none to put the selection or cursor-text colours back afterwards. iTerm2's Python API can do both,
so this script listens for a message `plants` prints and recolours just that session:

    theme: cursor guide, selection, selected text, cursor and cursor text follow the plant
    reset: each of those goes back to exactly what the session had before

install.sh copies it to ~/Library/Application Support/iTerm2/Scripts/AutoLaunch/ when iTerm2 is
installed. It needs iTerm2's Python API switched on (Settings > General > Magic > Enable Python
API) and iTerm2's Python runtime (Scripts > Manage > Install Python Runtime); restart iTerm2
afterwards. Without it, plants still works: those few colours just stay as your profile has them.

Message, printed by plants.sh:  ESC ] 1337 ; Custom=id=pvz-banner:<session id> theme <5 hex colours> BEL
                                ESC ] 1337 ; Custom=id=pvz-banner:<session id> reset BEL
Colours, in order: background, text, cursor, selection background, selection text.
"""
import iterm2

IDENTITY = "pvz-banner"
# profile property -> which of the five colours it takes, and its alpha (0-255)
TARGETS = {
    "cursor_guide_color": (2, 70),      # the plant's vivid colour, mostly see-through
    "selection_color": (3, 255),
    "selected_text_color": (4, 255),
    "cursor_color": (2, 255),
    "cursor_text_color": (0, 255),
}
originals = {}   # session id -> {property: the Color it had before the first plant}


def colour(hexa, alpha):
    return iterm2.Color(int(hexa[0:2], 16), int(hexa[2:4], 16), int(hexa[4:6], 16), alpha)


async def apply(session, values):
    change = iterm2.LocalWriteOnlyProfile()
    for name, value in values.items():
        setter = getattr(change, "set_" + name, None)
        if setter and value is not None:
            setter(value)
    await session.async_set_profile_properties(change)


async def main(connection):
    app = await iterm2.async_get_app(connection)
    async with iterm2.CustomControlSequenceMonitor(
            connection, IDENTITY, r"^(\S+) (theme|reset) ?([0-9a-fA-F ]*)$") as monitor:
        while True:
            match = await monitor.async_get()
            try:
                session = app.get_session_by_id(match.group(1))
                if session is None:
                    continue
                sid = session.session_id
                if match.group(2) == "theme":
                    hexes = match.group(3).split()
                    if len(hexes) < 5:
                        continue
                    if sid not in originals:      # remember what to go back to
                        profile = await session.async_get_profile()
                        originals[sid] = {name: getattr(profile, name, None) for name in TARGETS}
                    await apply(session, {name: colour(hexes[i], alpha) for name, (i, alpha) in TARGETS.items()})
                elif sid in originals:
                    await apply(session, originals.pop(sid))
            except Exception as error:            # one bad message must not stop the listener
                print("pvz-banner:", error)


iterm2.run_forever(main)
