# Microdrama Promo FFmpeg Cut Scripts
# Generated automatically

# ========================================================
# Promo #1: STITCH_EP01_014__EP01_119 (STITCHED)
# ========================================================
ffmpeg -y -ss 14.30 -i "videos/episode_001.mp4" -t 15.50 -c:v libx264 -c:a aac "promo_1_seg_1.mp4"
ffmpeg -y -ss 119.80 -i "videos/episode_001.mp4" -t 17.70 -c:v libx264 -c:a aac "promo_1_seg_2.mp4"
cat <<EOF > promo_1_list.txt
file 'promo_1_seg_1.mp4'
file 'promo_1_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_1_list.txt -c copy "final_promo_1.mp4"

# ========================================================
# Promo #2: STITCH_EP02_000__EP04_100 (STITCHED)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_002.mp4" -t 15.50 -c:v libx264 -c:a aac "promo_2_seg_1.mp4"
ffmpeg -y -ss 100.20 -i "videos/episode_004.mp4" -t 14.50 -c:v libx264 -c:a aac "promo_2_seg_2.mp4"
cat <<EOF > promo_2_list.txt
file 'promo_2_seg_1.mp4'
file 'promo_2_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_2_list.txt -c copy "final_promo_2.mp4"

# ========================================================
# Promo #3: STITCH_EP02_000__EP04_102 (STITCHED)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_002.mp4" -t 15.50 -c:v libx264 -c:a aac "promo_3_seg_1.mp4"
ffmpeg -y -ss 102.20 -i "videos/episode_004.mp4" -t 12.00 -c:v libx264 -c:a aac "promo_3_seg_2.mp4"
cat <<EOF > promo_3_list.txt
file 'promo_3_seg_1.mp4'
file 'promo_3_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_3_list.txt -c copy "final_promo_3.mp4"

# ========================================================
# Promo #4: STITCH_EP03_040__EP04_102 (STITCHED)
# ========================================================
ffmpeg -y -ss 40.40 -i "videos/episode_003.mp4" -t 12.60 -c:v libx264 -c:a aac "promo_4_seg_1.mp4"
ffmpeg -y -ss 102.20 -i "videos/episode_004.mp4" -t 13.50 -c:v libx264 -c:a aac "promo_4_seg_2.mp4"
cat <<EOF > promo_4_list.txt
file 'promo_4_seg_1.mp4'
file 'promo_4_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_4_list.txt -c copy "final_promo_4.mp4"

# ========================================================
# Promo #5: EP15_047_086 (CONTINUOUS)
# ========================================================
ffmpeg -y -ss 47.40 -i "videos/episode_015.mp4" -t 39.10 -c:v libx264 -c:a aac "promo_5_seg_1.mp4"
mv "promo_5_seg_1.mp4" "final_promo_5.mp4"

# ========================================================
# Promo #6: STITCH_EP01_014__EP01_122 (STITCHED)
# ========================================================
ffmpeg -y -ss 14.30 -i "videos/episode_001.mp4" -t 15.50 -c:v libx264 -c:a aac "promo_6_seg_1.mp4"
ffmpeg -y -ss 122.50 -i "videos/episode_001.mp4" -t 15.00 -c:v libx264 -c:a aac "promo_6_seg_2.mp4"
cat <<EOF > promo_6_list.txt
file 'promo_6_seg_1.mp4'
file 'promo_6_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_6_list.txt -c copy "final_promo_6.mp4"

# ========================================================
# Promo #7: STITCH_EP03_040__EP04_100 (STITCHED)
# ========================================================
ffmpeg -y -ss 40.40 -i "videos/episode_003.mp4" -t 12.60 -c:v libx264 -c:a aac "promo_7_seg_1.mp4"
ffmpeg -y -ss 100.20 -i "videos/episode_004.mp4" -t 15.50 -c:v libx264 -c:a aac "promo_7_seg_2.mp4"
cat <<EOF > promo_7_list.txt
file 'promo_7_seg_1.mp4'
file 'promo_7_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_7_list.txt -c copy "final_promo_7.mp4"

# ========================================================
# Promo #8: STITCH_EP04_001__EP04_102 (STITCHED)
# ========================================================
ffmpeg -y -ss 1.50 -i "videos/episode_004.mp4" -t 12.70 -c:v libx264 -c:a aac "promo_8_seg_1.mp4"
ffmpeg -y -ss 102.50 -i "videos/episode_004.mp4" -t 12.80 -c:v libx264 -c:a aac "promo_8_seg_2.mp4"
cat <<EOF > promo_8_list.txt
file 'promo_8_seg_1.mp4'
file 'promo_8_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_8_list.txt -c copy "final_promo_8.mp4"

# ========================================================
# Promo #9: STITCH_EP04_001__EP04_102 (STITCHED)
# ========================================================
ffmpeg -y -ss 1.50 -i "videos/episode_004.mp4" -t 13.50 -c:v libx264 -c:a aac "promo_9_seg_1.mp4"
ffmpeg -y -ss 102.50 -i "videos/episode_004.mp4" -t 12.80 -c:v libx264 -c:a aac "promo_9_seg_2.mp4"
cat <<EOF > promo_9_list.txt
file 'promo_9_seg_1.mp4'
file 'promo_9_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_9_list.txt -c copy "final_promo_9.mp4"

# ========================================================
# Promo #10: EP07_061_096 (CONTINUOUS)
# ========================================================
ffmpeg -y -ss 61.80 -i "videos/episode_007.mp4" -t 32.70 -c:v libx264 -c:a aac "promo_10_seg_1.mp4"
mv "promo_10_seg_1.mp4" "final_promo_10.mp4"

# ========================================================
# Promo #11: EP38_047_087 (CONTINUOUS)
# ========================================================
ffmpeg -y -ss 47.80 -i "videos/episode_038.mp4" -t 39.11 -c:v libx264 -c:a aac "promo_11_seg_1.mp4"
mv "promo_11_seg_1.mp4" "final_promo_11.mp4"

# ========================================================
# Promo #12: STITCH_EP05_000__EP06_027 (STITCHED)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_005.mp4" -t 15.80 -c:v libx264 -c:a aac "promo_12_seg_1.mp4"
ffmpeg -y -ss 27.90 -i "videos/episode_006.mp4" -t 12.60 -c:v libx264 -c:a aac "promo_12_seg_2.mp4"
cat <<EOF > promo_12_list.txt
file 'promo_12_seg_1.mp4'
file 'promo_12_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_12_list.txt -c copy "final_promo_12.mp4"

# ========================================================
# Promo #13: STITCH_EP05_000__EP06_026 (STITCHED)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_005.mp4" -t 15.80 -c:v libx264 -c:a aac "promo_13_seg_1.mp4"
ffmpeg -y -ss 26.50 -i "videos/episode_006.mp4" -t 14.00 -c:v libx264 -c:a aac "promo_13_seg_2.mp4"
cat <<EOF > promo_13_list.txt
file 'promo_13_seg_1.mp4'
file 'promo_13_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_13_list.txt -c copy "final_promo_13.mp4"

# ========================================================
# Promo #14: STITCH_EP06_000__EP06_026 (STITCHED)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_006.mp4" -t 14.90 -c:v libx264 -c:a aac "promo_14_seg_1.mp4"
ffmpeg -y -ss 26.50 -i "videos/episode_006.mp4" -t 13.00 -c:v libx264 -c:a aac "promo_14_seg_2.mp4"
cat <<EOF > promo_14_list.txt
file 'promo_14_seg_1.mp4'
file 'promo_14_seg_2.mp4'
EOF
ffmpeg -y -f concat -safe 0 -i promo_14_list.txt -c copy "final_promo_14.mp4"

# ========================================================
# Promo #15: EP06_000_040 (CONTINUOUS)
# ========================================================
ffmpeg -y -ss 0.00 -i "videos/episode_006.mp4" -t 41.00 -c:v libx264 -c:a aac "promo_15_seg_1.mp4"
mv "promo_15_seg_1.mp4" "final_promo_15.mp4"
