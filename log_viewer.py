#!/usr/bin/env python3
"""
Log Viewer for Free Drawing Agent
This utility helps view and analyze the logged agent responses.
"""

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Optional

class AgentLogViewer:
    """Utility class for viewing and analyzing agent logs"""
    
    def __init__(self, log_directory: str = "output/log"):
        self.log_directory = log_directory
        
    def list_log_files(self, limit: int = None) -> List[str]:
        """List all log files, sorted by timestamp (newest first)"""
        pattern = os.path.join(self.log_directory, "agent_response_*.json")
        log_files = glob.glob(pattern)
        log_files.sort(reverse=True)  # Newest first
        
        if limit:
            log_files = log_files[:limit]
            
        return log_files
    
    def load_log(self, log_file: str) -> Optional[Dict]:
        """Load a single log file"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading log file {log_file}: {e}")
            return None
    
    def show_recent_logs(self, count: int = 10):
        """Show summary of recent log files"""
        log_files = self.list_log_files(limit=count)
        
        if not log_files:
            print("No log files found.")
            return
        
        print(f"📋 Recent {len(log_files)} Agent Interactions:")
        print("=" * 60)
        
        for i, log_file in enumerate(log_files, 1):
            log_data = self.load_log(log_file)
            if log_data:
                timestamp = log_data.get('timestamp', 'Unknown')
                question = log_data.get('input', {}).get('user_question', 'No question')
                success = log_data.get('parsing', {}).get('success', False)
                brush = log_data.get('parsed_instruction', {}).get('brush', 'Unknown')
                reasoning = log_data.get('parsed_instruction', {}).get('reasoning', 'No reasoning')
                
                print(f"{i:2d}. {timestamp}")
                print(f"    Question: {question[:50]}{'...' if len(question) > 50 else ''}")
                print(f"    Parsing: {'✅ Success' if success else '❌ Failed'}")
                print(f"    Brush: {brush}")
                print(f"    Reasoning: {reasoning[:50]}{'...' if len(reasoning) > 50 else ''}")
                print(f"    File: {os.path.basename(log_file)}")
                print()
    
    def show_detailed_log(self, log_file: str):
        """Show detailed view of a specific log file"""
        log_data = self.load_log(log_file)
        if not log_data:
            return
        
        print(f"🔍 Detailed Log: {os.path.basename(log_file)}")
        print("=" * 60)
        
        # Basic info
        print(f"Timestamp: {log_data.get('timestamp', 'Unknown')}")
        print(f"Model: {log_data.get('model', 'Unknown')}")
        print()
        
        # Input info
        input_data = log_data.get('input', {})
        print("📥 INPUT:")
        print(f"  Canvas: {input_data.get('canvas_image_path', 'Unknown')}")
        print(f"  Exists: {input_data.get('canvas_image_exists', False)}")
        print(f"  Size: {input_data.get('canvas_image_size', 'Unknown')} bytes")
        print(f"  Question: {input_data.get('user_question', 'No question')}")
        print()
        
        # Raw response
        raw_response = log_data.get('raw_response', {})
        response_content = raw_response.get('content', 'No content')
        print("🤖 RAW RESPONSE:")
        print(f"  Length: {raw_response.get('length', 0)} characters")
        print("  Content:")
        print("  " + "-" * 58)
        # Show response with line numbers for easier analysis
        for i, line in enumerate(response_content.split('\n'), 1):
            print(f"  {i:2d}| {line}")
        print("  " + "-" * 58)
        print()
        
        # Parsing info
        parsing = log_data.get('parsing', {})
        print("🔧 PARSING:")
        print(f"  Success: {'✅ Yes' if parsing.get('success') else '❌ No'}")
        if parsing.get('error_info'):
            print(f"  Error: {parsing.get('error_info')}")
        print()
        
        # Parsed instruction
        instruction = log_data.get('parsed_instruction')
        if instruction:
            print("🎨 PARSED INSTRUCTION:")
            print(f"  Brush: {instruction.get('brush', 'Unknown')}")
            print(f"  Color: {instruction.get('color', 'Unknown')}")
            print(f"  Strokes: {instruction.get('num_strokes', 0)}")
            print(f"  Reasoning: {instruction.get('reasoning', 'No reasoning')}")
            print()
            
            # Show stroke details
            strokes = instruction.get('strokes', [])
            if strokes:
                print("  Stroke Details:")
                for i, stroke in enumerate(strokes, 1):
                    x_coords = stroke.get('x', [])
                    y_coords = stroke.get('y', [])
                    original_x = stroke.get('original_x', x_coords)
                    original_y = stroke.get('original_y', y_coords)
                    timing = stroke.get('timing', [])
                    desc = stroke.get('description', 'No description')
                    
                    print(f"    {i}. {desc}")
                    print(f"       Original points: {len(original_x)} (X: {original_x}, Y: {original_y})")
                    print(f"       Interpolated points: {len(x_coords)}")
                    if timing:
                        print(f"       Timing: {timing} (controls speed between segments)")
                    print(f"       Final X: {x_coords}")
                    print(f"       Final Y: {y_coords}")
        else:
            print("❌ No parsed instruction available")
    
    def analyze_parsing_success_rate(self, limit: int = 50):
        """Analyze parsing success rate over recent logs"""
        log_files = self.list_log_files(limit=limit)
        
        if not log_files:
            print("No log files found for analysis.")
            return
        
        success_count = 0
        total_count = len(log_files)
        error_types = {}
        
        for log_file in log_files:
            log_data = self.load_log(log_file)
            if log_data:
                parsing = log_data.get('parsing', {})
                if parsing.get('success'):
                    success_count += 1
                else:
                    error_info = parsing.get('error_info', 'Unknown error')
                    error_types[error_info] = error_types.get(error_info, 0) + 1
        
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        
        print(f"📊 Parsing Success Analysis (Last {total_count} interactions):")
        print("=" * 60)
        print(f"Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
        print()
        
        if error_types:
            print("Error Types:")
            for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_count) * 100
                print(f"  • {error}: {count} times ({percentage:.1f}%)")
        else:
            print("🎉 No parsing errors found!")
    
    def export_responses_to_text(self, output_file: str = "output/agent_responses_export.txt", limit: int = 20):
        """Export raw responses to a text file for easier reading"""
        log_files = self.list_log_files(limit=limit)
        
        if not log_files:
            print("No log files found for export.")
            return
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Agent Responses Export - {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, log_file in enumerate(log_files, 1):
                log_data = self.load_log(log_file)
                if log_data:
                    f.write(f"Response #{i} - {log_data.get('timestamp', 'Unknown')}\n")
                    f.write("-" * 60 + "\n")
                    f.write(f"Question: {log_data.get('input', {}).get('user_question', 'No question')}\n")
                    f.write(f"Model: {log_data.get('model', 'Unknown')}\n")
                    f.write(f"Success: {log_data.get('parsing', {}).get('success', False)}\n")
                    f.write("\nRaw Response:\n")
                    f.write(log_data.get('raw_response', {}).get('content', 'No content'))
                    f.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"📄 Exported {len(log_files)} responses to: {output_file}")

def main():
    """Interactive log viewer"""
    viewer = AgentLogViewer()
    
    while True:
        print("\n🔍 Agent Log Viewer")
        print("=" * 30)
        print("1. Show recent logs summary")
        print("2. View detailed log")
        print("3. Analyze parsing success rate")
        print("4. Export responses to text file")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            count = input("Number of recent logs to show (default 10): ").strip()
            count = int(count) if count.isdigit() else 10
            viewer.show_recent_logs(count)
            
        elif choice == "2":
            log_files = viewer.list_log_files(limit=20)
            if not log_files:
                print("No log files found.")
                continue
                
            print("\nAvailable log files:")
            for i, log_file in enumerate(log_files, 1):
                print(f"{i:2d}. {os.path.basename(log_file)}")
            
            try:
                file_choice = int(input("\nSelect file number: ")) - 1
                if 0 <= file_choice < len(log_files):
                    viewer.show_detailed_log(log_files[file_choice])
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Invalid input.")
                
        elif choice == "3":
            limit = input("Number of recent logs to analyze (default 50): ").strip()
            limit = int(limit) if limit.isdigit() else 50
            viewer.analyze_parsing_success_rate(limit)
            
        elif choice == "4":
            limit = input("Number of responses to export (default 20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            viewer.export_responses_to_text(limit=limit)
            
        elif choice == "5":
            print("👋 Goodbye!")
            break
            
        else:
            print("Invalid choice. Please select 1-5.")

if __name__ == "__main__":
    main() 