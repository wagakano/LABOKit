import sys
import os
from pathlib import Path

# Try to import rembg and load a session
try:
    print("Importing rembg...", flush=True)
    import rembg
    from rembg import new_session
    print("Imported successfully! Now creating new_session (General u2net)...", flush=True)
    
    # We use a dummy run or check u2net.
    # Note: downloading model might take time, but let's check if it creates model/session.
    # We can try to load u2net_human or u2net_only or the default model
    session = new_session("u2net")
    print("Created u2net session successfully!", flush=True)
    
except Exception as e:
    print(f"Error: {e}", flush=True)
    import traceback
    traceback.print_exc()

print("Rembg test complete.", flush=True)
