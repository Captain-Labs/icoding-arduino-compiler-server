# library_manager.py
import subprocess
import json
import re
from config import ARDUINO_CLI_CMD

class LibraryManager:
    @staticmethod
    def _sanitize_name(name: str) -> bool:
        """
        Validate library name.
        Only allow alphanumeric, spaces, hyphens, and underscores.
        """
        if not name or not isinstance(name, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9 _-]+$', name))

    @staticmethod
    def install(library_name: str) -> dict:
        """Installs a library via Arduino CLI."""
        if not LibraryManager._sanitize_name(library_name):
            return {
                'success': False,
                'error': 'Invalid library name format. Only alphanumeric characters, spaces, hyphens, and underscores are allowed.'
            }
            
        try:
            result = subprocess.run(
                ARDUINO_CLI_CMD + ['lib', 'install', library_name],
                capture_output=True,
                text=True,
                timeout=120  # Installing can take time
            )
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f"Library '{library_name}' installed successfully.",
                    'details': result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to install library: {result.stderr.strip() or result.stdout.strip()}",
                    'details': result.stderr.strip()
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception during installation: {str(e)}"
            }

    @staticmethod
    def uninstall(library_name: str) -> dict:
        """Uninstalls a library via Arduino CLI."""
        if not LibraryManager._sanitize_name(library_name):
            return {
                'success': False,
                'error': 'Invalid library name format.'
            }
            
        try:
            result = subprocess.run(
                ARDUINO_CLI_CMD + ['lib', 'uninstall', library_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f"Library '{library_name}' uninstalled successfully."
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to uninstall library: {result.stderr.strip() or result.stdout.strip()}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception during uninstallation: {str(e)}"
            }

    @staticmethod
    def search(query: str) -> dict:
        """Searches for libraries matching the query and returns formatted results."""
        if not LibraryManager._sanitize_name(query):
            return {
                'success': False,
                'error': 'Invalid search query format.'
            }
            
        try:
            # We use global --json flag for robust JSON output
            result = subprocess.run(
                ARDUINO_CLI_CMD + ['lib', 'search', query, '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'results': []}
                    
                libs = data.get('libraries', [])
                formatted_libs = []
                for item in libs:
                    # Parse name, version, and description
                    name = item.get('name', '')
                    latest = item.get('latest', {})
                    version = latest.get('version', '')
                    description = latest.get('sentence', '') or latest.get('paragraph', '') or ''
                    
                    formatted_libs.append({
                        'name': name,
                        'version': version,
                        'description': description
                    })
                return {'results': formatted_libs}
            else:
                return {
                    'success': False,
                    'error': f"Library search failed: {result.stderr.strip()}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception during search: {str(e)}"
            }

    @staticmethod
    def list_installed() -> dict:
        """Lists all installed libraries on the system."""
        try:
            result = subprocess.run(
                ARDUINO_CLI_CMD + ['lib', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'libraries': []}
                    
                libs = data.get('installed_libraries', [])
                formatted_libs = []
                for item in libs:
                    lib_detail = item.get('library', {})
                    name = lib_detail.get('name') or item.get('name', '')
                    version = lib_detail.get('version') or item.get('version', '')
                    location = lib_detail.get('location') or item.get('location', 'unknown')
                    
                    formatted_libs.append({
                        'name': name,
                        'version': version,
                        'location': location
                    })
                return {'libraries': formatted_libs}
            else:
                return {
                    'success': False,
                    'error': f"Failed to list libraries: {result.stderr.strip()}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception listing libraries: {str(e)}"
            }

    @staticmethod
    def update_index() -> dict:
        """Updates the local index of available Arduino libraries."""
        try:
            result = subprocess.run(
                ARDUINO_CLI_CMD + ['lib', 'update-index'],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Index updated successfully.'
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to update index: {result.stderr.strip()}"
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception updating library index: {str(e)}"
            }
