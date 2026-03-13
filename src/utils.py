import os
import sys
import stat

def check_env_permissions(env_file='.env'):
    """Checks if the .env file has secure permissions (chmod 600)."""
    if not os.path.exists(env_file):
        return # Skip if file doesn't exist (e.g. using real env vars)

    # st_mode contains the file type and permissions
    file_stats = os.stat(env_file)
    # Mask to get only the permission bits
    permissions = stat.S_IMODE(file_stats.st_mode)
    
    # Check if permissions are exactly 600 (owner read/write only)
    if permissions != 0o600:
        print(f"ERROR: Secure permissions required for {env_file}.")
        print(f"Current permissions: {oct(permissions)}")
        print(f"Please run: chmod 600 {env_file}")
        sys.exit(1)
