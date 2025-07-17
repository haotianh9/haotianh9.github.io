#!/usr/bin/env python3
import subprocess, os, argparse


def get_video_resolution(input_path):
    """Use ffprobe to get the width and height of the first video stream."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=p=0:s=x",
        input_path,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error:\n{result.stderr}")
    w, h = result.stdout.strip().split("x")
    return int(w), int(h)


def convert_to_gif(input_path, output_path, fps=None, width=None):
    """Run ffmpeg to convert to GIF, with optional fps and scaling."""
    vf = []
    if fps:
        vf.append(f"fps={fps}")
    if width:
        vf.append(f"scale={width}:-1:flags=lanczos")
    cmd = ["ffmpeg", "-y", "-i", input_path]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += [output_path]
    subprocess.run(cmd, check=True)


def file_size_mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def main():
    p = argparse.ArgumentParser(description="Convert MP4→GIF under a size limit")
    p.add_argument("input", help="Input MP4 file")
    p.add_argument("output", help="Output GIF file")
    p.add_argument(
        "--max_size", type=float, default=100.0, help="Maximum GIF size in megabytes"
    )
    p.add_argument("--fps", type=int, default=15, help="Frame rate for the GIF")
    p.add_argument(
        "--scale_step",
        type=float,
        default=0.9,
        help="Fractional width reduction each iteration",
    )
    args = p.parse_args()

    # 1) Naïve conversion
    print("⏳ Performing naïve conversion…")
    convert_to_gif(args.input, args.output, fps=args.fps)
    size = file_size_mb(args.output)
    print(f"Naïve GIF size: {size:.2f} MB")

    if size <= args.max_size:
        print("✅ Within size limit—done.")
        return

    # 2) Too big: get original dimensions
    print("⚠️  Too large! Probing original resolution…")
    orig_w, _ = get_video_resolution(args.input)
    curr_w = orig_w

    # 3) Iteratively downscale
    while size > args.max_size and curr_w > 100:
        curr_w = int(curr_w * args.scale_step)
        print(f"🔄 Trying width={curr_w}px…")
        convert_to_gif(args.input, args.output, fps=args.fps, width=curr_w)
        size = file_size_mb(args.output)
        print(f"   → Size now: {size:.2f} MB")

    if size <= args.max_size:
        print("✅ Achieved size limit!")
    else:
        print("❗Reached minimum width without hitting target size.")


if __name__ == "__main__":
    main()
