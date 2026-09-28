# SharpWR Damage Lab — Web v4

Deploy-ready Streamlit Community Cloud package.

## Files
- streamlit_app.py — app entrypoint
- requirements.txt — Python dependencies
- .streamlit/config.toml — dark theme/config
- assets/ — reserved for champion/item PNGs

## Deploy
1. Create a GitHub repository.
2. Upload the CONTENTS of this folder to the repository root.
3. Connect GitHub to Streamlit Community Cloud.
4. Create app.
5. Select the repository and main branch.
6. Entrypoint: streamlit_app.py
7. Deploy.

## Current research model
- 23 ADC Lv1–15 automatic AD/AS scaling
- Yunara 58 Base AD / 3.0 AD per level
- Xayah AS/Lvl 0.034
- Senna Mist input
- 9 first-item TTK comparison
- HP / Armor / MR
- Attack-by-attack log
- C44 maximum 10% Magnification
- Yun Tal starts at 0 item crit
- Jhin 7.3 Whisper conversion saved:
  Bonus AS × 30% + Crit Rate × 40% + Level × 3%

## Caveats
Jhin item-specific combat, Zeri special attacks, champion abilities/passives, and Yun Tal full reactivation cycle still need dedicated modeling before treating those outputs as publication-grade.
