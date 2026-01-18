#!/usr/bin/env python3
"""
Timelapse Video Assembler

Assembles captured timelapse images into a video file.
Works with the 5-digit frame numbering convention: basename_00001.jpg

Features:
- Frame number overlay (top-left)
- Timestamp overlay (bottom-right) from metadata
- H.264 compression with configurable quality
- Brightness report generation from metadata

Usage:
    python assemble_timelapse.py ./timelapse -o microgreens_timelapse.mp4
    python assemble_timelapse.py ./timelapses --fps 25 --basename microgreens -o output.mp4
    
    # High compression for smaller files:
    python assemble_timelapse.py ./timelapse --small -o small_video.mp4
    python assemble_timelapse.py ./timelapse --tiny -o tiny_video.mp4
    
    # Custom compression:
    python assemble_timelapse.py ./timelapses --fps 25 --crf 28 --preset slow --basename microgreens -o compressed.mp4

    # No overlays:
    python assemble_timelapse.py ./timelapse --no-frame --no-timestamp -o clean.mp4

Requirements:
    pip install pillow numpy opencv-python
    # ffmpeg required for compression (optional but recommended)

Author: Claude (Anthropic) for mgua
Date: 2025-01-17
"""

import argparse
import json
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Required: pip install pillow numpy")
    sys.exit(1)

# Optional: opencv for video creation
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def find_images(capture_dir: Path, basename: str) -> list[dict]:
    """Find all images matching the naming pattern and sort by frame number."""
    pattern = re.compile(rf"^{re.escape(basename)}_(\d{{5}})\.jpg$")
    
    captures = []
    for img_path in capture_dir.glob(f"{basename}_*.jpg"):
        match = pattern.match(img_path.name)
        if match:
            frame_num = int(match.group(1))
            
            # Try to load metadata if available
            meta_path = img_path.with_suffix('.json')
            metadata = {}
            if meta_path.exists():
                try:
                    with open(meta_path) as f:
                        metadata = json.load(f)
                except:
                    pass
            
            captures.append({
                'frame': frame_num,
                'image_path': str(img_path),
                'metadata': metadata,
                'timestamp': metadata.get('timestamp', ''),
            })
    
    return sorted(captures, key=lambda x: x['frame'])


def generate_brightness_report(captures: list[dict], output_path: Path):
    """Generate a CSV report of brightness and LED values over time."""
    with open(output_path, 'w') as f:
        f.write("frame,timestamp,brightness,led_intensity,running_avg\n")
        for cap in captures:
            meta = cap.get('metadata', {})
            f.write(f"{cap['frame']},{meta.get('timestamp', '')},"
                    f"{meta.get('brightness', '')},{meta.get('led_intensity', '')},"
                    f"{meta.get('running_avg', '')}\n")
    print(f"Brightness report saved: {output_path}")


def create_video_cv2(captures: list[dict], output_path: str, fps: int = 30, 
                     show_timestamp: bool = True, show_frame: bool = True,
                     crf: int = 23, preset: str = 'medium'):
    """Create video using OpenCV, then re-encode with ffmpeg for compression."""
    if not captures:
        print("No captures to process")
        return False
    
    # Get dimensions from first image
    first_img = cv2.imread(captures[0]['image_path'])
    if first_img is None:
        print(f"Cannot read first image: {captures[0]['image_path']}")
        return False
        
    height, width = first_img.shape[:2]
    
    # Create temporary uncompressed video first
    temp_path = output_path + ".temp.avi"
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))
    
    print(f"Creating video: {width}x{height} @ {fps}fps")
    print(f"Processing {len(captures)} frames...")
    
    for i, cap in enumerate(captures):
        img = cv2.imread(cap['image_path'])
        if img is not None:
            # Add overlays - top left
            y_pos = 30
            
            if show_frame:
                frame_text = f"Frame: {cap['frame']:05d}"
                cv2.putText(img, frame_text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, frame_text, (10, y_pos), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
            
            # Add timestamp - bottom right
            if show_timestamp and cap.get('metadata', {}).get('timestamp'):
                try:
                    ts = datetime.fromisoformat(cap['metadata']['timestamp'])
                    timestamp_str = ts.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Calculate text size to position in bottom-right
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    # font_scale = 0.7
                    font_scale = 2
                    thickness = 2
                    (text_width, text_height), baseline = cv2.getTextSize(
                        timestamp_str, font, font_scale, thickness
                    )
                    
                    # Position: 10px from right edge, 10px from bottom
                    x_pos = width - text_width - 15
                    y_pos_ts = height - 15
                    
                    # Draw with outline (white text, black outline)
                    cv2.putText(img, timestamp_str, (x_pos, y_pos_ts), 
                               font, font_scale, (0, 0, 0), thickness + 2)
                    cv2.putText(img, timestamp_str, (x_pos, y_pos_ts), 
                               font, font_scale, (255, 255, 255), thickness)
                except:
                    pass
            
            out.write(img)
        
        if (i + 1) % 50 == 0 or (i + 1) == len(captures):
            print(f"  Processed {i + 1}/{len(captures)} frames")
    
    out.release()
    
    # Re-encode with ffmpeg for better compression
    print(f"\nCompressing video (CRF={crf}, preset={preset})...")
    try:
        cmd = [
            'ffmpeg', '-y', '-i', temp_path,
            '-c:v', 'libx264',
            '-preset', preset,
            '-crf', str(crf),
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Remove temp file
            Path(temp_path).unlink()
            
            # Show file size
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"Video saved: {output_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"FFmpeg compression failed: {result.stderr}")
            print(f"Keeping uncompressed video at: {temp_path}")
            # Rename temp to output
            Path(temp_path).rename(output_path)
            return True
            
    except FileNotFoundError:
        print("FFmpeg not found. Keeping uncompressed video.")
        Path(temp_path).rename(output_path)
        size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"Video saved: {output_path} ({size_mb:.1f} MB)")
        print("Install ffmpeg for better compression.")
        return True


def create_ffmpeg_script(captures: list[dict], output_dir: Path, basename: str, fps: int,
                         crf: int = 23, preset: str = 'medium'):
    """Create a shell script to assemble video with ffmpeg."""
    script_path = output_dir / "create_video.sh"
    
    with open(script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Timelapse video assembly script\n")
        f.write("# Requires: ffmpeg\n\n")
        f.write(f"cd \"{output_dir}\"\n\n")
        f.write(f"# Using glob pattern for {basename}_*.jpg files\n")
        f.write(f"ffmpeg -framerate {fps} -pattern_type glob -i '{basename}_*.jpg' \\\n")
        f.write(f"  -c:v libx264 -preset {preset} -crf {crf} \\\n")
        f.write("  -pix_fmt yuv420p -movflags +faststart \\\n")
        f.write("  -vf \"pad=ceil(iw/2)*2:ceil(ih/2)*2\" \\\n")
        f.write("  timelapse.mp4\n\n")
        f.write("echo 'Video created: timelapse.mp4'\n")
    
    script_path.chmod(0o755)
    print(f"FFmpeg script saved: {script_path}")
    return script_path


def main():
    parser = argparse.ArgumentParser(
        description="Assemble timelapse video from captured frames",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("capture_dir", 
                        help="Directory containing captured images")
    parser.add_argument("-o", "--output", default="timelapse.mp4", 
                        help="Output video filename")
    parser.add_argument("-b", "--basename", default="frame",
                        help="Base filename pattern (e.g., 'frame' for frame_00001.jpg)")
    parser.add_argument("--fps", type=int, default=30, 
                        help="Output video framerate")
    
    # Overlay options
    overlay = parser.add_argument_group('Overlay Options')
    overlay.add_argument("--no-timestamp", action="store_true",
                         help="Don't show timestamp overlay (bottom-right)")
    overlay.add_argument("--no-frame", action="store_true",
                         help="Don't show frame number overlay (top-left)")
    
    # Compression options
    compress = parser.add_argument_group('Compression Options')
    compress.add_argument("--crf", type=int, default=23,
                          help="H.264 CRF value (0-51, lower=better quality, larger file). "
                               "Recommended: 18-28. Default 23 is good balance.")
    compress.add_argument("--preset", default="medium",
                          choices=['ultrafast', 'superfast', 'veryfast', 'faster', 
                                   'fast', 'medium', 'slow', 'slower', 'veryslow'],
                          help="H.264 encoding preset (slower=better compression)")
    compress.add_argument("--small", action="store_true",
                          help="Shortcut for high compression (CRF=28, preset=slow)")
    compress.add_argument("--tiny", action="store_true",
                          help="Shortcut for maximum compression (CRF=32, preset=veryslow)")
    
    # Other options
    parser.add_argument("--report-only", action="store_true", 
                        help="Only generate brightness report, no video")
    parser.add_argument("--ffmpeg-script", action="store_true",
                        help="Generate ffmpeg script instead of using OpenCV")
    
    args = parser.parse_args()
    
    capture_dir = Path(args.capture_dir)
    if not capture_dir.exists():
        print(f"Directory not found: {capture_dir}")
        sys.exit(1)
    
    # Find images
    captures = find_images(capture_dir, args.basename)
    print(f"Found {len(captures)} frames matching '{args.basename}_XXXXX.jpg'")
    
    if not captures:
        print("No valid captures found")
        print(f"Looking for pattern: {args.basename}_00000.jpg to {args.basename}_99999.jpg")
        sys.exit(1)
    
    # Show frame range
    first_frame = captures[0]['frame']
    last_frame = captures[-1]['frame']
    print(f"Frame range: {first_frame:05d} to {last_frame:05d}")
    
    # Check for gaps
    expected_count = last_frame - first_frame + 1
    if len(captures) < expected_count:
        missing = expected_count - len(captures)
        print(f"Warning: {missing} frames missing in sequence")
    
    # Generate brightness report if metadata exists
    has_metadata = any(cap.get('metadata') for cap in captures)
    if has_metadata:
        report_path = capture_dir / "brightness_report.csv"
        generate_brightness_report(captures, report_path)
    
    if args.report_only:
        return
    
    # Apply compression shortcuts
    crf = args.crf
    preset = args.preset
    if args.tiny:
        crf = 32
        preset = 'veryslow'
    elif args.small:
        crf = 28
        preset = 'slow'
    
    # Create video
    if args.ffmpeg_script or not HAS_CV2:
        if not HAS_CV2:
            print("\nOpenCV not available. Creating ffmpeg script...")
        script_path = create_ffmpeg_script(captures, capture_dir, args.basename, args.fps,
                                           crf=crf, preset=preset)
        print(f"\nTo create video, run:")
        print(f"  bash {script_path}")
        print(f"\nOr install opencv-python:")
        print(f"  pip install opencv-python")
    else:
        create_video_cv2(
            captures, 
            args.output, 
            args.fps,
            show_timestamp=not args.no_timestamp,
            show_frame=not args.no_frame,
            crf=crf,
            preset=preset
        )


if __name__ == "__main__":
    main()
