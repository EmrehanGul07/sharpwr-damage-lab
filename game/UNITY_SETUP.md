# Opening the game in Unity (personal build)

All gameplay code already exists as three local packages in `game/packages/`; the Unity
project only needs to be created once and pointed at them. The arena builds itself from code
when you press Play, so no scene has to be authored.

## 1. Install (once)

- Unity Hub, then **Unity 6.3 LTS (6000.3.x)** with the **Android Build Support** module
  (includes OpenJDK, Android SDK & NDK). Personal licence is fine.

## 2. Create the project

1. `git fetch origin && git checkout moba/foundation`
2. Unity Hub → **New project** → template **Universal 3D** →
   *Project name* `unity`, *Location* `<repo>/game` → **Create project**.
   (`game/unity` must not exist yet; it does not in the repository.)
3. Close Unity once it has opened, then add these three lines to
   `game/unity/Packages/manifest.json` inside `"dependencies": {`:
   ```json
   "com.sharpwr.sim": "file:../../packages/com.sharpwr.sim",
   "com.sharpwr.client": "file:../../packages/com.sharpwr.client",
   "com.sharpwr.unity": "file:../../packages/com.sharpwr.unity",
   ```
4. Reopen the project. The Console must show **no compile errors**. If it does, copy them to
   Claude: they are Unity API differences that CI's stub check cannot catch.

## 3. Play

Press **Play** in the sample scene. You control Samira (blue); the grey cylinder is the
practice dummy (2000 HP, 50 armor, 30 MR); the red capsule is the bot.

| Desktop | Phone / touch (mouse left button also works) |
|---|---|
| Right-click ground: move · right-click enemy: attack | Left half: virtual joystick |
| Q W E R: cast toward the cursor (E picks the enemy nearest the cursor) | ATTACK: attack nearest enemy |
| A: attack the enemy nearest the cursor · S: stop | Q/W/E/R: tap = quick cast, drag = aim, release on the top red area = cancel |
| F1: debug panel (tick, state hash, events, unsupported list) | Top bar: bot difficulty, reset, debug |

R needs S Style (6 stacks: alternate AA/Q/W/E hits). Unsupported or provisional Samira
mechanics are listed in the debug panel.

## 4. Phone build (personal use only — do not upload or share)

File → **Build Profiles** → Android → **Switch Platform** → Player Settings: Default
Orientation *Landscape Left* → connect the phone with USB debugging → **Build And Run**.

## 5. Commit

Commit `game/unity/Assets`, `game/unity/Packages`, `game/unity/ProjectSettings`
(`game/.gitignore` already excludes Library/Temp/Logs/UserSettings). Turn on Git LFS before
adding any binary art. Riot-derived art may only go in `Assets/SharpWR/Reference/`.

## Optional: Unity builds in CI

Add repository secrets `UNITY_EMAIL`, `UNITY_PASSWORD` (and `UNITY_LICENSE` for Personal) so
GameCI can compile the real Unity project and run PlayMode tests (docs/moba/06-testing.md).
