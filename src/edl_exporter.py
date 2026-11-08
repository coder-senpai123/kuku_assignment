"""Edit Decision List (EDL) and FFmpeg Cut Script Generator.

Exports promo segment cut commands for video editors (FFmpeg, Premiere CSV).
"""

from __future__ import annotations
import json
import os
from typing import List, Dict, Any


def generate_ffmpeg_commands(ranked_promos: List[Dict[str, Any]], video_dir: str = "videos") -> str:
    """Generate shell/PowerShell commands to cut and concatenate promos from episode video files."""
    lines = ["# Microdrama Promo FFmpeg Cut Scripts", "# Generated automatically\n"]

    for p in ranked_promos:
        rank = p["rank"]
        cid = p["candidate_id"]
        ptype = p["promo_type"]
        lines.append(f"# ========================================================")
        lines.append(f"# Promo #{rank}: {cid} ({ptype.upper()})")
        lines.append(f"# ========================================================")

        seg_files = []
        for idx, s in enumerate(p["segments"]):
            ep = s["episode"]
            start_sec = s["start_time_seconds"]
            dur_sec = s["duration_seconds"]
            out_seg = f"promo_{rank}_seg_{idx+1}.mp4"
            seg_files.append(out_seg)

            lines.append(
                f'ffmpeg -y -ss {start_sec:.2f} -i "{video_dir}/episode_{ep:03d}.mp4" -t {dur_sec:.2f} -c:v libx264 -c:a aac "{out_seg}"'
            )

        if len(seg_files) == 1:
            lines.append(f'mv "{seg_files[0]}" "final_promo_{rank}.mp4"\n')
        else:
            # Concat demuxer script
            concat_list = f"promo_{rank}_list.txt"
            file_entries = "\n".join(f"file '{f}'" for f in seg_files)
            lines.append(f'cat <<EOF > {concat_list}\n{file_entries}\nEOF')
            lines.append(f'ffmpeg -y -f concat -safe 0 -i {concat_list} -c copy "final_promo_{rank}.mp4"\n')

    return "\n".join(lines)


def export_edl(json_path: str, output_path: str, video_dir: str = "videos") -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    script = generate_ffmpeg_commands(data["ranked_promos"], video_dir=video_dir)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"Exported FFmpeg cut script to: {output_path}")


if __name__ == "__main__":
    export_edl("results/promos_ranked.json", "results/cut_promos.sh")
