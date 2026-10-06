#!/bin/bash
# Render every clip of one champion and join them with titles into OUT/<id>_v2.mp4.
# Usage: make_video.sh CHAMPION_ID OUT_DIR "Clip:Title:loops" ...
# VIDEO=E,Q re-renders only those clips (others reuse their frames); VIDEO=none only joins.
set -e
ID=$1; OUT=$2; shift 2
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
VIDEO=${VIDEO:-all}
[ "$VIDEO" = none ] || /tmp/bpyenv/bin/python "$HERE/build.py" "$ID" "$OUT" --clips all --video "$VIDEO" --root_motion --samples 8 --width 400 --height 532 --threads ${THREADS:-3} --fast > "$OUT/render.log" 2>&1
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
rm -f "$OUT/parts.txt"
i=0
for spec in "$@"; do
  name="${spec%%:*}"; rest="${spec#*:}"; title="${rest%:*}"; loops="${rest##*:}"
  title="${title//\'/}"  # drawtext quotes the title
  i=$((i+1))
  ffmpeg -y -loglevel error -stream_loop $((loops-1)) -framerate 24 -i "$OUT/frames/$name/%04d.png" \
    -vf "drawtext=fontfile=$FONT:text='$title':x=20:y=20:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.45:boxborderw=8,format=yuv420p" \
    -c:v libx264 -crf 20 "$OUT/part_$i.mp4"
  echo "file 'part_$i.mp4'" >> "$OUT/parts.txt"
done
ffmpeg -y -loglevel error -f concat -safe 0 -i "$OUT/parts.txt" -c copy "$OUT/${ID}_v2.mp4"
echo VIDEO-DONE
