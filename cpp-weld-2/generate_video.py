#!/usr/bin/env python3
"""
Video generation script for welding simulation
Reads CSV frame data and generates MP4 video
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path

# Check for required packages
try:
    import imageio.v2 as imageio
except ImportError:
    print("Error: imageio package not found.")
    print("Install with: pip install imageio imageio-ffmpeg")
    sys.exit(1)

def load_frame(frame_file):
    """Load a single frame from CSV file"""
    # Read CSV, skip the metadata line
    df = pd.read_csv(frame_file, comment='#')

    # Extract metadata from first line
    with open(frame_file, 'r') as f:
        first_line = f.readline().strip()
        # Parse: # Frame: N, Time: T s
        parts = first_line.split(',')
        frame_num = int(parts[0].split(':')[1].strip())
        time_val = float(parts[1].split(':')[1].strip().replace('s', ''))

    return df, frame_num, time_val

def generate_video_from_frames(frames_dir='output/video_frames',
                                output_file='output/welding_simulation.mp4',
                                fps=10,
                                weld_process='TIG',
                                use_gas=True):
    """
    Generate MP4 video from saved CSV frame files

    Parameters:
    -----------
    frames_dir : str
        Directory containing frame CSV files
    output_file : str
        Output video file path
    fps : int
        Frames per second for video
    weld_process : str
        Welding process name (for title)
    use_gas : bool
        Whether gas shielding is used (for title)
    """

    frames_path = Path(frames_dir)
    if not frames_path.exists():
        print(f"Error: Frames directory '{frames_dir}' not found.")
        print("Run simulation with --save_video flag first.")
        return False

    # Find all frame files
    frame_files = sorted(frames_path.glob('frame_*.csv'))

    if not frame_files:
        print(f"Error: No frame files found in '{frames_dir}'")
        print("Run simulation with --save_video flag first.")
        return False

    print(f"Found {len(frame_files)} frames")
    print(f"Generating video at {fps} FPS...")

    # Create figure for video frames
    fig = plt.figure(figsize=(12, 6.08))

    # List to store rendered frames
    video_frames = []

    # Process gas status for title
    gas_status = "with Gas" if use_gas else "without Gas"
    title_base = f"{weld_process} Welding {gas_status}"

    # Process each frame
    for idx, frame_file in enumerate(frame_files):
        try:
            df, frame_num, time_val = load_frame(frame_file)

            # Reshape data
            i_vals = df['i'].values
            j_vals = df['j'].values
            x_vals = df['x'].values
            y_vals = df['y'].values
            T_vals = df['T'].values

            # Determine grid size
            nx = len(np.unique(i_vals))
            ny = len(np.unique(j_vals))

            # Reshape to 2D grid (row-major order: j varies faster in outer loop)
            T_grid = T_vals.reshape((ny, nx))
            x_1d = x_vals.reshape((ny, nx))[0, :]
            y_1d = y_vals.reshape((ny, nx))[:, 0]

            # Create plot
            plt.figure(fig.number)
            plt.clf()

            # Convert to mm for better visualization
            x_mm = x_1d * 1000
            y_mm = y_1d * 1000

            # Plot temperature field with better contrast
            # Use dynamic color scale based on actual temperatures
            T_min = max(293, T_grid.min())
            T_max = min(2500, T_grid.max() * 1.1)  # 10% above max for headroom

            im = plt.imshow(T_grid, origin='lower',
                          extent=[x_mm[0], x_mm[-1], y_mm[0], y_mm[-1]],
                          aspect='auto', cmap='hot',
                          vmin=T_min, vmax=T_max)  # Dynamic color scale

            # Calculate arc position (assuming start at x=20mm, speed=6mm/s)
            x_start_mm = 20.0
            v_weld_mm_s = 6.0  # 0.006 m/s = 6 mm/s
            x_arc_mm = x_start_mm + v_weld_mm_s * time_val

            # Only show arc if it's within the domain
            if x_mm[0] <= x_arc_mm <= x_mm[-1]:
                # Draw arc position as a vertical line
                plt.axvline(x=x_arc_mm, color='cyan', linewidth=3,
                           linestyle='--', label='Arc Position', alpha=0.8)

                # Draw arc marker (circle)
                plt.plot(x_arc_mm, 0, 'c*', markersize=20,
                        markeredgecolor='white', markeredgewidth=2)

                # Draw weld path (line showing where arc has been)
                if x_arc_mm > x_start_mm:
                    plt.plot([x_start_mm, x_arc_mm], [0, 0],
                            'c-', linewidth=2, alpha=0.6, label='Weld Path')

                plt.legend(loc='upper right', fontsize=10)

            plt.colorbar(im, label='Temperature (K)')
            plt.xlabel('x (mm)', fontsize=12)
            plt.ylabel('y (mm)', fontsize=12)
            plt.title(f'{title_base} - t = {time_val:.2f} s - Arc at x={x_arc_mm:.1f} mm',
                     fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)

            # Render to image
            fig.canvas.draw()
            # Use buffer_rgba() for newer matplotlib versions
            buf = fig.canvas.buffer_rgba()
            frame_img = np.asarray(buf)
            # Convert RGBA to RGB
            frame_img = frame_img[:, :, :3]
            video_frames.append(frame_img)

            # Progress indicator
            if (idx + 1) % max(1, len(frame_files) // 10) == 0:
                print(f"  Processed {idx + 1}/{len(frame_files)} frames ({100*(idx+1)//len(frame_files)}%)")

        except Exception as e:
            print(f"Warning: Error processing frame {frame_file.name}: {e}")
            continue

    plt.close(fig)

    if not video_frames:
        print("Error: No frames were successfully processed.")
        return False

    # Ensure all frames have same size (use first frame as reference)
    print(f"Saving video to '{output_file}'...")
    target_size = (video_frames[0].shape[1], video_frames[0].shape[0])

    try:
        # Save video using imageio
        imageio.mimsave(output_file, video_frames, fps=fps,
                       format='FFMPEG', codec='libx264',
                       quality=8)  # quality 0-10, 10 is best
        print(f"✓ Video saved successfully: {output_file}")
        print(f"  Duration: {len(video_frames)/fps:.1f} seconds")
        print(f"  Frames: {len(video_frames)}")
        print(f"  FPS: {fps}")
        return True

    except Exception as e:
        print(f"Error saving video: {e}")
        print("Make sure ffmpeg is installed: sudo apt-get install ffmpeg")
        return False

def detect_simulation_parameters(output_dir='output'):
    """
    Try to detect simulation parameters from output files
    """
    # Try to read simulation log if available
    log_file = Path(output_dir) / 'simulation_log.txt'

    # Default values
    weld_process = 'TIG'
    use_gas = True

    # Try to detect from results file metadata
    results_file = Path(output_dir) / 'simulation_results.csv'
    if results_file.exists():
        # Could add metadata parsing here if needed
        pass

    return weld_process, use_gas

if __name__ == '__main__':
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description='Generate video from welding simulation frames')
    parser.add_argument('--frames_dir', type=str, default='output/video_frames',
                       help='Directory containing frame CSV files')
    parser.add_argument('--output', type=str, default='output/welding_simulation.mp4',
                       help='Output video file path')
    parser.add_argument('--fps', type=int, default=10,
                       help='Frames per second for video (default: 10)')
    parser.add_argument('--weld_process', type=str, default='TIG',
                       choices=['TIG', 'Electrode'],
                       help='Welding process name for title')
    parser.add_argument('--use_gas', action='store_true', default=False,
                       help='Whether gas shielding was used')
    parser.add_argument('--no-gas', dest='use_gas', action='store_false',
                       help='Gas shielding was not used')

    args = parser.parse_args()

    # Generate video
    success = generate_video_from_frames(
        frames_dir=args.frames_dir,
        output_file=args.output,
        fps=args.fps,
        weld_process=args.weld_process,
        use_gas=args.use_gas
    )

    sys.exit(0 if success else 1)
