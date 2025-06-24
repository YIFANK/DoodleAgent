#!/usr/bin/env python3
"""
Demo script for generating a video from the drawing agent session log - LITE VERSION.
This uses imageio instead of OpenCV for much faster installation.
"""

import os
from generate_drawing_video_lite import DrawingVideoGeneratorLite

def main():
    """Generate a video from the provided session log using the lite version."""
    
    # Path to the session log file
    log_file = "output/log/session_responses_20250622_181203.txt"
    
    # Check if log file exists
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        print("Make sure you have a session log file in the output/log directory.")
        return
    
    print("🎬 DoodleAgent Video Generator Demo (Lite Version)")
    print("=" * 55)
    print("✨ No OpenCV required - fast installation!")
    print(f"📁 Input log: {log_file}")
    
    # Create video generator with custom settings
    generator = DrawingVideoGeneratorLite(
        fps=8,  # 8 frames per second (slower for better viewing)
        frame_duration=1.0  # Hold each step for 1 second
    )
    
    try:
        # Generate the video
        output_path = generator.generate_video(log_file)
        
        if output_path:
            print("\n🎉 Success! Video has been generated.")
            print(f"📁 Video location: {output_path}")
            
            # Get file info
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"📊 File size: {file_size:.1f} MB")
            
            print("\n🎥 You can now play the video to see the drawing process!")
            print("The video shows each step of the agent's creative process with:")
            print("  • Step numbers and descriptions")
            print("  • Mood and reasoning for each stroke")
            print("  • Progressive artwork development")
            print("  • High-quality MP4 output using imageio")
            
        else:
            print("\n❌ Video generation failed. Check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n⚠️ Video generation interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        
        # Check for common issues
        if "codec" in str(e).lower() or "ffmpeg" in str(e).lower():
            print("\n💡 Tip: Make sure ffmpeg is installed on your system:")
            print("  • macOS: brew install ffmpeg")
            print("  • Ubuntu/Debian: apt install ffmpeg")
            print("  • Windows: Download from https://ffmpeg.org/")
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 