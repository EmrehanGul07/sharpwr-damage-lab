# Unity client (not created yet)

The Unity project is created by a person with Unity Hub (a project cannot be generated
correctly without the editor):

1. Unity Hub → New project → **Universal 3D** template, Unity **6000.3.x LTS**, location
   `game/unity` (this folder; move this README aside first, then back).
2. `Packages/manifest.json` → add `"com.sharpwr.sim": "file:../../packages/com.sharpwr.sim"`.
3. Package Manager → install **Input System** and **Addressables**; Test Framework is included.
4. Create `Assets/SharpWR/{Bootstrap,Presentation,Input,Camera,UI,Scenes,Art,Tests}` and the
   `SharpWR.Presentation` asmdef referencing `SharpWR.Sim` (see `docs/moba/01-architecture.md` §5).
5. Commit `Assets/`, `Packages/`, `ProjectSettings/` (incl. `ProjectVersion.txt`). `game/.gitignore`
   already excludes Library/Temp/Logs/UserSettings. Enable Git LFS for binary art before adding any.
6. Verify: the Console shows no compile errors for `SharpWR.Sim`; Test Runner lists no tests yet.
