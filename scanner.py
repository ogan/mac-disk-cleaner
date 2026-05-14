import os
import shutil
import plistlib
from pathlib import Path

def get_size(path):
    total_size = 0
    try:
        if os.path.isfile(path):
            total_size = os.path.getsize(path)
        elif os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            pass
    except OSError:
        pass
    return total_size

def format_size(size_in_bytes):
    if size_in_bytes == 0:
        return "0.00 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

class Scanner:
    def __init__(self):
        self.targets = {
            "System Caches": os.path.expanduser("~/Library/Caches"),
            "System Logs": os.path.expanduser("~/Library/Logs"),
            "Trash Bin": os.path.expanduser("~/.Trash"),
            "Media Analysis Data": os.path.expanduser("~/Library/Containers/com.apple.mediaanalysisd/Data")
        }
        self.categories = list(self.targets.keys()) + ["App Leftovers"]

    def find_leftovers(self):
        leftover_paths = []
        app_support_dir = os.path.expanduser("~/Library/Application Support")
        
        installed_bundle_ids = set()
        installed_app_names = set()
        for apps_dir in ["/Applications", os.path.expanduser("~/Applications"), "/System/Applications", "/System/Applications/Utilities"]:
            if os.path.exists(apps_dir):
                for item in os.listdir(apps_dir):
                    if item.endswith(".app"):
                        app_path = os.path.join(apps_dir, item)
                        plist_path = os.path.join(app_path, "Contents", "Info.plist")
                        installed_app_names.add(item[:-4].lower())
                        if os.path.isfile(plist_path):
                            try:
                                with open(plist_path, 'rb') as f:
                                    plist = plistlib.load(f)
                                    bundle_id = plist.get('CFBundleIdentifier')
                                    if bundle_id:
                                        installed_bundle_ids.add(bundle_id.lower())
                            except Exception:
                                pass
        
        safe_prefixes = [
            "com.apple.", "com.microsoft.", "com.google.", "com.adobe.", 
            "com.mozilla.", "com.skype.", "com.valvesoftware.steam", "com.epicgames."
        ]
        safe_exact = [
            "crashreporter", "mobilesync", "syncservices", "addressbook", 
            "clouddocs", "iclouddrive", "knowledge"
        ]
        
        if os.path.exists(app_support_dir):
            try:
                for folder in os.listdir(app_support_dir):
                    if folder.startswith("."):
                        continue
                        
                    folder_path = os.path.join(app_support_dir, folder)
                    if os.path.isdir(folder_path):
                        folder_lower = folder.lower()
                        
                        is_safe = False
                        for prefix in safe_prefixes:
                            if folder_lower.startswith(prefix):
                                is_safe = True
                                break
                        if not is_safe:
                            for exact in safe_exact:
                                if folder_lower == exact:
                                    is_safe = True
                                    break
                                    
                        if is_safe:
                            continue
                            
                        is_installed = False
                        if folder_lower in installed_bundle_ids or folder_lower in installed_app_names:
                            is_installed = True
                        else:
                            for bid in installed_bundle_ids:
                                if folder_lower.startswith(bid):
                                    is_installed = True
                                    break
                                    
                        if not is_installed:
                            leftover_paths.append(folder_path)
            except OSError:
                pass
        
        return leftover_paths

    def scan(self):
        results = {}
        total_size = 0
        for name, path in self.targets.items():
            size = 0
            if os.path.exists(path):
                size = get_size(path)
            results[name] = {"size": size, "formatted": format_size(size)}
            total_size += size
            
        # Leftovers
        leftover_paths = self.find_leftovers()
        leftovers_size = sum(get_size(p) for p in leftover_paths)
        results["App Leftovers"] = {"size": leftovers_size, "formatted": format_size(leftovers_size), "paths": leftover_paths}
        total_size += leftovers_size
        
        return results, total_size

    def clean(self, categories_to_clean):
        freed_space = 0
        errors = []
        
        def safe_delete(path_to_delete, base_dir=None):
            nonlocal freed_space
            try:
                if os.path.islink(path_to_delete):
                    size = os.path.getsize(path_to_delete) if not os.path.isdir(path_to_delete) else 0
                    os.unlink(path_to_delete)
                    freed_space += size
                    return
                
                real_path = os.path.realpath(path_to_delete)
                if base_dir and os.path.exists(real_path):
                    real_base = os.path.realpath(base_dir)
                    if os.path.commonpath([real_base, real_path]) != real_base:
                        errors.append(f"Security error: {path_to_delete} resolves outside {base_dir}")
                        return

                if os.path.isfile(path_to_delete):
                    size = os.path.getsize(path_to_delete)
                    os.unlink(path_to_delete)
                    freed_space += size
                elif os.path.isdir(path_to_delete):
                    for root, dirs, files in os.walk(path_to_delete, topdown=False):
                        for name in files:
                            fp = os.path.join(root, name)
                            if not os.path.islink(fp):
                                try:
                                    s = os.path.getsize(fp)
                                    os.unlink(fp)
                                    freed_space += s
                                except OSError as e:
                                    errors.append(f"Failed to delete {fp}: {e}")
                            else:
                                try:
                                    os.unlink(fp)
                                except OSError as e:
                                    errors.append(f"Failed to delete symlink {fp}: {e}")
                        for name in dirs:
                            dp = os.path.join(root, name)
                            if not os.path.islink(dp):
                                try:
                                    os.rmdir(dp)
                                except OSError as e:
                                    errors.append(f"Failed to remove directory {dp}: {e}")
                            else:
                                try:
                                    os.unlink(dp)
                                except OSError as e:
                                    errors.append(f"Failed to delete symlink dir {dp}: {e}")
                    try:
                        os.rmdir(path_to_delete)
                    except OSError as e:
                        errors.append(f"Failed to remove base directory {path_to_delete}: {e}")
            except OSError as e:
                errors.append(f"Failed to process {path_to_delete}: {e}")
            except Exception as e:
                errors.append(f"Unexpected error on {path_to_delete}: {e}")

        for category in categories_to_clean:
            if category == "App Leftovers":
                leftovers = self.find_leftovers()
                app_support_dir = os.path.expanduser("~/Library/Application Support")
                for item_path in leftovers:
                    safe_delete(item_path, base_dir=app_support_dir)
            elif category in self.targets:
                path = self.targets[category]
                if os.path.exists(path):
                    try:
                        for item in os.listdir(path):
                            item_path = os.path.join(path, item)
                            safe_delete(item_path, base_dir=path)
                    except OSError as e:
                        errors.append(f"Failed to clean {path}. Reason: {e}")
        return freed_space, errors
