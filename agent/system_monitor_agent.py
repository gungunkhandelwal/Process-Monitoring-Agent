import psutil
import requests
import json
import time
import socket
import sys
import os
import platform
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitorAgent:
    # Configuration
    def __init__(self, config_file: str = 'config.json'):
        self.config = self.load_config(config_file)
        self.api_url = self.config.get('api_url', 'http://localhost:8000/api')
        self.api_key = self.config.get('api_key', 'your-secret-api-key-here')
        self.hostname = socket.gethostname()
        self.collection_interval = self.config.get('collection_interval', 60)
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        default_config = {
            'api_url': 'http://localhost:8000/api',
            'api_key': 'your-secret-api-key-here',
            'collection_interval': 60,
            'include_system_processes': True,
            'max_processes': 1000
        }
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        return default_config
    
    def collect_system_data(self) -> Dict[str, Any]:
        '''Collect System Information'''
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        memory_percent = memory.percent
        try:
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_used_gb = disk.used / (1024**3)
            disk_free_gb = disk.free / (1024**3)
        except Exception:
            disk_total_gb = disk_used_gb = disk_free_gb = 0
        platform_system = platform.system()
        platform_release = platform.release()
        platform_version = platform.version()
        cpu_brand = "Unknown"
        if hasattr(psutil, 'cpu_info'):
            cpu_info = psutil.cpu_info()
            if hasattr(cpu_info, 'brand'):
                cpu_brand = cpu_info.brand
        return {
            'operating_system': f"{platform_system}-{platform_release}-{platform_version}",
            'processor': cpu_brand,
            'processor_cores': cpu_count,
            'processor_threads': cpu_count_logical,
            'ram_total_gb': round(memory_total_gb, 2),
            'ram_used_gb': round(memory_used_gb, 2),
            'ram_available_gb': round(memory_available_gb, 2),
            'storage_total_gb': round(disk_total_gb, 2),
            'storage_used_gb': round(disk_used_gb, 2),
            'storage_free_gb': round(disk_free_gb, 2)
        }

    def collect_process_data(self) -> List[Dict[str, Any]]:
        ''' Collect process info'''
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'ppid', 'cpu_percent', 'memory_percent', 
                                         'memory_info', 'status', 'username', 'cmdline', 'create_time']):
            try:
                proc_info = proc.info
                if not all(key in proc_info for key in ['pid', 'name']):
                    continue
                memory_mb = 0
                if proc_info['memory_info']:
                    memory_mb = proc_info['memory_info'].rss / (1024 * 1024)
                
                # Ensure memory_mb is a valid number
                if memory_mb is None or not isinstance(memory_mb, (int, float)):
                    memory_mb = 0.0
                
                cmdline = proc_info.get('cmdline', [])
                command_line = ' '.join(cmdline) if cmdline else proc_info['name']
                if len(command_line) > 500:
                    command_line = command_line[:500] + '...'
                username = proc_info.get('username', 'Unknown')
                if username and len(username) > 100:
                    username = username[:100]
                cpu_percent = proc_info.get('cpu_percent', 0.0)
                memory_percent = proc_info.get('memory_percent', 0.0)
                
                # Handle None values for cpu_percent and memory_percent
                if cpu_percent is None:
                    cpu_percent = 0.0
                if memory_percent is None:
                    memory_percent = 0.0
                
                process_data = {
                    'pid': proc_info['pid'],
                    'name': proc_info['name'][:255],
                    'parent_pid': proc_info.get('ppid') if proc_info.get('ppid') is not None else None,
                    'cpu_percent': round(float(cpu_percent), 2),
                    'memory_percent': round(float(memory_percent), 2),
                    'memory_mb': round(memory_mb, 2),
                    'status': proc_info.get('status', 'running'),
                    'username': username,
                    'command_line': command_line,
                    'created_time': datetime.fromtimestamp(proc_info.get('create_time', 0)).isoformat() if proc_info.get('create_time') and isinstance(proc_info['create_time'], (int, float)) else None
                }
                processes.append(process_data)
            except Exception as e:
                logger.warning(f"Error processing process {getattr(proc, 'pid', '?')}: {e}")
                continue
        return processes

    def send_data_to_backend(self, system_data: Dict[str, Any], process_data: List[Dict[str, Any]]) -> bool:
        '''Send data to Backend'''
        payload = {
            'hostname': self.hostname,
            'timestamp': datetime.now().isoformat(),
            'system_info': system_data,
            'processes': process_data
        }
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        }
        try:
            response = requests.post(
                f"{self.api_url}/submit/",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending data: {e}")
            return False

    def run_once(self) -> bool:
        '''Run the data'''
        logger.info("Starting data collection...")
        system_data = self.collect_system_data()
        process_data = self.collect_process_data()
        if not process_data:
            logger.warning("No process data collected")
            return False
        success = self.send_data_to_backend(system_data, process_data)
        if success:
            logger.info("Data collection and sending completed successfully")
        else:
            logger.error("Failed to send data to backend")
        return success

    def run_continuous(self):
        logger.info(f"Starting System Monitor Agent for {self.hostname}")
        logger.info(f"API endpoint: {self.api_url}")
        logger.info(f"Collection interval: {self.collection_interval} seconds")
        try:
            while True:
                self.run_once()
                time.sleep(self.collection_interval)
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")

def main():
    agent = SystemMonitorAgent()
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        success = agent.run_once()
        sys.exit(0 if success else 1)
    else:
        agent.run_continuous()

if __name__ == "__main__":
    main()