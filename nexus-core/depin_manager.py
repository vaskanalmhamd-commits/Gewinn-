import os
import subprocess
import logging
from dotenv import load_dotenv

# Set up logging for DePIN
logging.basicConfig(filename='depin.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DePINManager')

class DePINManager:
    def __init__(self):
        self.processes = {}
        load_dotenv('config/keys.env')

    def start_grass(self):
        """Start GRASS node worker."""
        user_id = os.getenv('GRASS_USER_ID')
        if not user_id:
            logger.warning("GRASS_USER_ID not found. Skipping GRASS start.")
            return False

        try:
            cmd = ["python3", "grass_worker.py"]
            # Start background worker process
            self.processes['GRASS'] = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
            logger.info(f"Started GRASS worker process (PID: {self.processes['GRASS'].pid}) for user ID: {user_id[:5]}...")
            return True
        except Exception as e:
            logger.error(f"Error starting GRASS: {str(e)}")
            return False

    def start_honeygain(self):
        """Start Honeygain CLI."""
        email = os.getenv('HONEYGAIN_EMAIL')
        password = os.getenv('HONEYGAIN_PASSWORD')
        if not (email and password):
            logger.warning("Honeygain credentials not found. Skipping Honeygain start.")
            return False

        try:
            cmd = ["python3", "honeygain_worker.py"]
            self.processes['Honeygain'] = subprocess.Popen(cmd, cwd=os.path.dirname(__file__))
            logger.info(f"Started Honeygain worker (PID: {self.processes['Honeygain'].pid})")
            return True
        except Exception as e:
            logger.error(f"Error starting Honeygain: {str(e)}")
            return False

    def start_uprock(self):
        """Start UPROCK node."""
        token = os.getenv('UPROCK_API_TOKEN')
        if not token:
            logger.warning("UPROCK_API_TOKEN not found. Skipping UPROCK start.")
            return False

        try:
            # uprock-node would be an external binary if installed
            # For now, we simulate calling it but don't fail if binary is missing
            # logger.info("Starting functional UPROCK node...")
            # self.processes['UPROCK'] = subprocess.Popen(["uprock-node", "--token", token])
            self.processes['UPROCK'] = "Configured (Awaiting Binary)"
            return True
        except Exception as e:
            logger.error(f"Error starting UPROCK: {str(e)}")
            return False

    def start_multiple(self):
        """Start Multiple Network node."""
        node_id = os.getenv('MULTIPLE_NOD_ID')
        if not node_id:
            logger.warning("MULTIPLE_NOD_ID not found. Skipping Multiple start.")
            return False

        try:
            # logger.info(f"Starting functional Multiple Network node ID: {node_id}...")
            # self.processes['Multiple'] = subprocess.Popen(["multiple-cli", "start", "--id", node_id])
            self.processes['Multiple'] = "Configured (Awaiting Binary)"
            return True
        except Exception as e:
            logger.error(f"Error starting Multiple: {str(e)}")
            return False

    def start_all(self):
        """Initialize and start all DePIN networks in Phase 1."""
        logger.info("Initializing Phase 1 DePIN networks...")
        self.start_grass()
        self.start_honeygain()
        self.start_uprock()
        self.start_multiple()

    def get_status(self):
        """Return status of all DePIN processes."""
        status = {}
        networks = ['GRASS', 'Honeygain', 'UPROCK', 'Multiple']
        for net in networks:
            if net in self.processes:
                if hasattr(self.processes[net], 'poll'):
                    if self.processes[net].poll() is None:
                        status[net] = f"Active (PID: {self.processes[net].pid})"
                    else:
                        status[net] = f"Exited (Code: {self.processes[net].returncode})"
                else:
                    status[net] = str(self.processes[net])
            else:
                env_keys = {
                    'GRASS': 'GRASS_USER_ID',
                    'Honeygain': 'HONEYGAIN_EMAIL',
                    'UPROCK': 'UPROCK_API_TOKEN',
                    'Multiple': 'MULTIPLE_NOD_ID'
                }
                status[net] = "Stopped" if os.getenv(env_keys[net]) else "Missing Config"
        return status

depin_manager = DePINManager()
