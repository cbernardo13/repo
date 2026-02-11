
import re
import datetime
import os
try:
    import calendar_sync
except ImportError:
    calendar_sync = None # Fallback if setup isn't complete

# Configuration Paths
# Configuration Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(BASE_DIR, "openclaw_tasks.md")
PRIORITIES_FILE = os.path.join(BASE_DIR, "life_priorities.md")
OUTPUT_FILE = os.path.join(BASE_DIR, "daily_schedule.md")
try:
    import llm_brain
    USE_LLM = True 
except ImportError:
    USE_LLM = False


# Priority Weights
PRIORITY_MAP = {
    "High": 3,
    "Med": 2,
    "Low": 1
}

def parse_duration(duration_str):
    """Converts '30m', '1h' to minutes."""
    match = re.search(r'(\d+)(m|h)', duration_str)
    if not match:
        return 30 # Default to 30m if unclear
    
    val, unit = match.groups()
    val = int(val)
    if unit == 'h':
        return val * 60
    return val

def read_priorities():
    """Reads priorities file to get keywords for boosting score."""
    keywords = []
    try:
        with open(PRIORITIES_FILE, 'r') as f:
            content = f.read().lower()
            # Simple keyword extraction based on the known structure or just common words in the file
            # For now, we'll hardcode some known North Star keywords based on the file creation
            if "growth" in content: keywords.append("growth")
            if "client" in content: keywords.append("client")
            if "health" in content: keywords.append("health")
            if "revenue" in content: keywords.append("revenue")
    except FileNotFoundError:
        print(f"Warning: {PRIORITIES_FILE} not found.")
    return keywords

def load_tasks(priority_keywords):
    tasks = []
    try:
        with open(TASKS_FILE, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            # Look for incomplete tasks: "- [ ] Task Name (Priority: X) (Duration: Y) #tag"
            if line.strip().startswith("- [ ]"):
                task = {}
                task['raw'] = line.strip()
                
                # Extract Name
                name_match = re.search(r'- \[ \] (.*?)\(', line)
                if name_match:
                    task['name'] = name_match.group(1).strip()
                else:
                    task['name'] = line.strip()[6:] # Fallback
                
                # Extract Priority
                p_match = re.search(r'\(Priority: (High|Med|Low)\)', line, re.IGNORECASE)
                task['priority_label'] = p_match.group(1) if p_match else "Med"
                task['base_score'] = PRIORITY_MAP.get(task['priority_label'].capitalize(), 1)
                
                # Extract Duration
                d_match = re.search(r'\(Duration: (\d+[mh])\)', line)
                task['duration_str'] = d_match.group(1) if d_match else "30m"
                task['duration_mins'] = parse_duration(task['duration_str'])
                
                # Extract Tags
                tags = re.findall(r'#(\w+)', line)
                task['tags'] = tags
                
                # Calculate Final Score
                # Boost if tag matches priority keywords
                boost = 0
                for tag in tags:
                    if tag.lower() in priority_keywords:
                        boost += 1
                    # Double boost for specific CTRM growth tags
                    if tag.lower() in ['growth', 'marketing'] and 'client' in priority_keywords:
                         boost += 1
                         
                task['score'] = task['base_score'] + (boost * 0.5)
                
                tasks.append(task)
                
    except FileNotFoundError:
        print(f"Error: {TASKS_FILE} not found.")
        return []
        
    return sorted(tasks, key=lambda x: x['score'], reverse=True)

def generate_schedule(tasks):
    # Determine Start Time (Next day or today if early?) 
    # Let's assume scheduling for "Tomorrow" or "Today" starting at 9 AM
    # Determine Start Time (Next day or today if early?)
    # Adjust for EST (UTC-5)
    # Server is UTC, User is EST (-5 hours)
    utc_now = datetime.datetime.utcnow()
    est_now = utc_now - datetime.timedelta(hours=5)
    
    start_time = est_now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    if start_time < est_now:
         start_time += datetime.timedelta(days=1)
    
    # Get Busy Slots from Calendar
    busy_slots = []
    if calendar_sync:
        try:
             print("Syncing with Google Calendar...")
             busy_slots = calendar_sync.get_busy_slots()
        except Exception as e:
             print(f"Calendar Sync Failed: {e}")
         
    current_time = start_time
    schedule = []
    
    # Simple constraints: Work until 5 PM (17:00), Lunch at 12
    end_time = start_time.replace(hour=17)
    lunch_start = start_time.replace(hour=12)
    lunch_end = start_time.replace(hour=13)
    
    
    # --- LLM Integration ---
    if USE_LLM:
        print("Using Dual-Model Brain for scheduling (Gemini)...")
        # Prepare context data for the LLM
        context_data = {
            "date": start_time.strftime('%A, %B %d'),
            "tasks": tasks,
            "busy_slots": busy_slots
        }
        # Call Gemini (Simple)
        try:
             llm_schedule = llm_brain.generate_schedule(str(context_data))
             if not "Error" in llm_schedule:
                  return llm_schedule + "\n\n---\n*Generated by OpenClaw Brain (Gemini 3 Flash)*"
             else:
                  print(f"LLM Fallback: {llm_schedule}")
        except Exception as e:
             print(f"LLM Error: {e}")
    # -----------------------

    schedule_markdown = f"# Daily Schedule for {start_time.strftime('%A, %B %d')}\n\n"
    schedule_markdown += f"**Focus**: Leveraging high-priority tasks first.\n\n"
    
    # Add external events to view?
    if busy_slots:
         schedule_markdown += "**Calendar Events (Fixed):**\n"
         for slot in busy_slots:
              s_time = slot['start'].strftime('%I:%M %p')
              e_time = slot['end'].strftime('%I:%M %p')
              schedule_markdown += f"- 📅 {slot['summary']} ({s_time} - {e_time})\n"
         schedule_markdown += "\n"
    
    for task in tasks:
        # Check if we have time
        if current_time >= end_time:
            break
            
        # 1. Check for Calendar Conflicts
        # Iterate until we find a free slot for this task
        while True:
            conflict = None
            task_end_check = current_time + datetime.timedelta(minutes=task['duration_mins'])
            
            for slot in busy_slots:
                # Check overlap: (StartA < EndB) and (EndA > StartB)
                if (current_time < slot['end']) and (task_end_check > slot['start']):
                    conflict = slot
                    break
            
            if conflict:
                # Jump to end of conflict
                current_time = conflict['end']
            else:
                break # No conflict, proceed
            
            # Boundary check after jump
            if current_time >= end_time:
                break

        if current_time >= end_time:
             break

        # 2. Check Lunch
        if current_time < lunch_end and (current_time + datetime.timedelta(minutes=task['duration_mins'])) > lunch_start:
             # If task overlaps lunch, jump to after lunch
             if current_time < lunch_start:
                 current_time = lunch_end
             else:
                 current_time = lunch_end

        task_end = current_time + datetime.timedelta(minutes=task['duration_mins'])
        
        if task_end > end_time:
            continue
            
        time_str = f"{current_time.strftime('%I:%M %p')} - {task_end.strftime('%I:%M %p')}"
        
        # Add visual emphasis for High priority
        icon = "🔴" if task['priority_label'] == 'High' else "🔵"
        if "growth" in task['tags'] or "marketing" in task['tags']:
            icon = "🚀" # Special icon for Growth
            
        schedule.append(f"- **{time_str}**: {icon} {task['name']} ({task['duration_str']})")
        
        current_time = task_end
        
        # Add 5 min buffer
        current_time += datetime.timedelta(minutes=5)
        
    if not schedule:
        schedule_markdown += "No tasks scheduled. Relax or check your task list!\n"
    else:
        schedule_markdown += "\n".join(schedule)
        
    schedule_markdown += "\n\n---\n*Generated by OpenClaw Scheduler*"
    
    return schedule_markdown

def main():
    print("Reading priorities...")
    keywords = read_priorities()
    print(f"North Star keywords: {keywords}")
    
    print("Loading tasks...")
    tasks = load_tasks(keywords)
    print(f"Found {len(tasks)} tasks.")
    
    print("Generating schedule...")
    schedule_content = generate_schedule(tasks)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(schedule_content)
        
    print(f"Schedule written to {OUTPUT_FILE}")
    print("\n--- Preview ---\n")
    print(schedule_content)

if __name__ == "__main__":
    main()
