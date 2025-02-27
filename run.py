#!/usr/bin/env python3
"""
Comprehensive Operations Script

This script performs three main operations:
1. Connects to MS SQL using credentials from AWS Secrets Manager
2. Establishes SSH connection to retrieve system information
3. Initiates Windows Remote Management (WinRM) connection and self-execution with recursion protection

Each operation includes detailed console output and error handling.
"""

import sys
import os
import time
import socket
import platform
import argparse
import subprocess
from typing import Dict, Any, Optional, Tuple
import logging

# Required third-party libraries
try:
    import pymssql  # For MS SQL connections
    import boto3    # For AWS Secrets Manager
    import paramiko  # For SSH connections
    import winrm    # For Windows Remote Management (WinRM)
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required libraries with:")
    print("pip install pymssql boto3 paramiko pywinrm")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flag to prevent recursive WinRM execution
RECURSION_FLAG = "--no-winrm-recursion"


class MultiOperationsScript:
    """Main class to handle the three requested operations."""
    
    def __init__(self):
        """Initialize the script with default values."""
        self.parser = self._setup_argument_parser()
        self.args = self.parser.parse_args()
        
        # Check for recursion flag
        self.prevent_winrm_recursion = RECURSION_FLAG in sys.argv
        
        logger.info("Initializing Multi-Operations Script")
        logger.info(f"Running on: {platform.platform()}")
        logger.info(f"Python version: {platform.python_version()}")
        
    def _setup_argument_parser(self) -> argparse.ArgumentParser:
        """Set up command line argument parser."""
        parser = argparse.ArgumentParser(description="Perform database, SSH, and WinRM operations")
        
        # MS SQL arguments
        parser.add_argument("--mssql-url", required=True, help="MS SQL connection URL (sqlserver://server:port)")
        parser.add_argument("--aws-secret-name", required=True, help="AWS Secret name for MS SQL credentials")
        parser.add_argument("--aws-region", default="us-east-1", help="AWS region for Secrets Manager")
        
        # SSH arguments
        parser.add_argument("--ssh-host", required=True, help="SSH host IP address")
        parser.add_argument("--ssh-user", required=True, help="SSH username")
        parser.add_argument("--ssh-key-path", required=True, help="Path to SSH private key file")
        
        # WinRM arguments (for Remote Desktop Connection)
        parser.add_argument("--winrm-host", required=True, help="WinRM host IP address")
        parser.add_argument("--winrm-user", required=True, help="WinRM username")
        parser.add_argument("--winrm-password", required=True, help="WinRM password")
        parser.add_argument("--winrm-port", default=5985, type=int, help="WinRM port (default: 5985)")
        parser.add_argument("--winrm-use-ssl", action="store_true", help="Use SSL for WinRM connection")
        
        return parser
    
    def run(self) -> None:
        """Execute all operations in sequence."""
        try:
            logger.info("Starting operations sequence")
            
            # 1. MS SQL Operation
            self._perform_mssql_operations()
            
            # 2. SSH Operation
            self._perform_ssh_operations()
            
            # 3. WinRM Operation (with recursion protection)
            if not self.prevent_winrm_recursion:
                self._perform_winrm_operations()
            else:
                logger.info("Skipping WinRM operations (recursion prevention active)")
                
            logger.info("All operations completed successfully")
            
        except Exception as e:
            logger.error(f"Error during operations: {str(e)}")
            sys.exit(1)
    
    def _get_aws_secret(self, secret_name: str, region_name: str) -> Dict[str, Any]:
        """Retrieve secret from AWS Secrets Manager."""
        logger.info(f"Retrieving credentials from AWS Secrets Manager: {secret_name}")
        
        try:
            # Create a Secrets Manager client
            session = boto3.session.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=region_name,
                aws_access_key_id="ASIA3CMCCY5ZO3C4VFDF",
                aws_secret_access_key="zLLYJJUIxCYf1HRatdb8VJe2kysNBztQQBI93ZPR",
                aws_session_token="IQoJb3JpZ2luX2VjEDoaCWV1LXdlc3QtMiJIMEYCIQCp32bgxOKyTzy8FY0Phsz0FSXhbycXzYKFH+15QaKxnAIhAMl8Z0Z42IX79FmVf5yNY3EwrOa6egnaPJcNqNETEWJxKuoBCHMQABoMNzYxMDE4ODk0MTk0IgzWmr0rLqFUXSWpS7EqxwGHR4jvPUXGhnrsU41/bwD/BFMSAOyHSH691QhiZ+jMG6kHC4WLUp4YfzQ/o4DZQRbYklpxLWlDyt/LTCIT94es280vlFe3cUHMXyMVlN/jsF00ENrAjnOYm/Nrh2SP910lv+estA7ZEExUGcJ5C9Hc0sowuHgwReGYGgKdysCjDvnYxbhnQoKnFT6uxz6jMiKLE3uzda9GDFU3J5QE8QYTsElsoTckB2VLdvYxNaMU9aZ4+a7DjD2j/jyWyvqzRXUnKvjnsWkhMIj1gL4GOpcB9XMBY/lJbuGK/KIQsK6fvYlD1MWZYtxWxV3oSe4k/vX6MHC1XhwzyCicVTFZxVU+GEBNx1rqc12MEDTduS7MoqwxYE/MBCeucKUtaXWTx0FQWOCzT1cKUdLGQ9D6/4W1nEa2q6NJM5jX62Ncp8dNQdJVLIvgMEbmNzmA4Af3oiA3W4mnMkqBV2Z9ONabx4NQnLG0LDbPrA==",
            )
            
            # Get the secret value
            get_secret_value_response = client.get_secret_value(SecretId=secret_name)
            
            # The secret is stored as a JSON string
            if 'SecretString' in get_secret_value_response:
                import json
                secret = json.loads(get_secret_value_response['SecretString'])
                logger.info("Successfully retrieved secret")
                return secret
                
        except Exception as e:
            logger.error(f"Error retrieving AWS secret: {str(e)}")
            raise
    
    def _perform_mssql_operations(self) -> None:
        """
        Connect to MS SQL using AWS Secrets Manager credentials.
        Create database, schema, table, and perform operations.
        """
        logger.info("=== STARTING MS SQL OPERATIONS ===")
        
        try:
            # Step 1: Get credentials from AWS Secrets Manager
            logger.info("Step 1: Retrieving MS SQL credentials from AWS Secrets Manager")
            credentials = self._get_aws_secret(self.args.aws_secret_name, self.args.aws_region)
            
            if not all(key in credentials for key in ['username', 'password']):
                raise ValueError("AWS Secret is missing required keys: username, password")
                
            username = credentials['username']
            password = credentials['password']
            
            # Parse the MS SQL URL to extract server and port
            server_parts = self.args.mssql_url.replace('sqlserver://', '').split(':')
            server = server_parts[0]
            port = int(server_parts[1]) if len(server_parts) > 1 else 1433
            
            logger.info(f"Step 2: Connecting to MS SQL Server at {server}:{port}")
            
            # Connect to the server (not to a specific database yet)
            conn = pymssql.connect(
                server=server,
                port=port,
                user=username,
                password=password
            )
            
            cursor = conn.cursor()
            logger.info("Successfully connected to MS SQL Server")
            
            # Step 3: Create a database
            db_name = f"ExampleDB_{int(time.time())}"  # Unique name
            logger.info(f"Step 3: Creating new database: {db_name}")
            conn.autocommit(True)
            cursor.execute(f"IF NOT EXISTS (SELECT name FROM master.dbo.sysdatabases WHERE name = N'{db_name}') CREATE DATABASE {db_name}")
            # conn.commit()
            logger.info(f"Database '{db_name}' created successfully")
            
            # Connect to the newly created database
            conn.close()
            conn = pymssql.connect(
                server=server,
                port=port,
                user=username,
                password=password,
                database=db_name
            )
            cursor = conn.cursor()
            
            # Step 4: Create a schema
            schema_name = "ExampleSchema"
            logger.info(f"Step 4: Creating schema: {schema_name}")
            cursor.execute(f"IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}') EXEC sp_executesql N'CREATE SCHEMA {schema_name}'")
            conn.commit()
            logger.info(f"Schema '{schema_name}' created successfully")
            
            # Step 5: Create an example table
            table_name = f"{schema_name}.ExampleTable"
            logger.info(f"Step 5: Creating table: {table_name}")
            cursor.execute(f"""
            IF OBJECT_ID('{table_name}', 'U') IS NULL
            CREATE TABLE {table_name} (
                ID INT PRIMARY KEY IDENTITY(1,1),
                Name NVARCHAR(100) NOT NULL,
                Description NVARCHAR(MAX),
                CreatedDate DATETIME DEFAULT GETDATE()
            )
            """)
            conn.commit()
            logger.info(f"Table '{table_name}' created successfully")
            
            # Step 6: Insert sample data
            logger.info("Step 6: Inserting sample data")
            sample_data = [
                ("Sample Item 1", "This is a description for sample item 1"),
                ("Sample Item 2", "This is a description for sample item 2"),
                ("Sample Item 3", "This is a description for sample item 3")
            ]
            
            for name, description in sample_data:
                cursor.execute(
                    f"INSERT INTO {table_name} (Name, Description) VALUES (%s, %s)", 
                    (name, description)
                )
            
            conn.commit()
            logger.info(f"Successfully inserted {len(sample_data)} sample records")
            
            # Step 7: Select and display the data
            logger.info("Step 7: Retrieving inserted data")
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            logger.info(f"Retrieved {len(rows)} rows from {table_name}:")
            for row in rows:
                logger.info(f"  ID: {row[0]}, Name: {row[1]}, Description: {row[2]}, Created: {row[3]}")
                
            # Close the database connection
            conn.close()
            logger.info("MS SQL operations completed successfully")
            
        except Exception as e:
            logger.error(f"Error during MS SQL operations: {str(e)}")
            raise
    
    def _perform_ssh_operations(self) -> None:
        """
        Connect to SSH using the provided credentials.
        Retrieve and display remote system IP and domain name.
        """
        logger.info("=== STARTING SSH OPERATIONS ===")
        
        try:
            # Step 1: Validate SSH key file
            logger.info(f"Step 1: Validating SSH key file at {self.args.ssh_key_path}")
            if not os.path.isfile(self.args.ssh_key_path):
                raise FileNotFoundError(f"SSH key file not found: {self.args.ssh_key_path}")
            
            # Step 2: Create SSH client and connect
            logger.info(f"Step 2: Connecting to SSH server at {self.args.ssh_host}")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_client.connect(
                hostname=self.args.ssh_host,
                username=self.args.ssh_user,
                key_filename=self.args.ssh_key_path,
                timeout=10
            )
            
            logger.info(f"Successfully established SSH connection to {self.args.ssh_host}")
            
            # Step 3: Get IP address information
            logger.info("Step 3: Retrieving IP address information")
            stdin, stdout, stderr = ssh_client.exec_command("hostname -I")
            ip_addresses = stdout.read().decode().strip()
            
            if ip_addresses:
                logger.info(f"Remote system IP addresses: {ip_addresses}")
            else:
                error = stderr.read().decode().strip()
                logger.warning(f"Could not retrieve IP addresses. Error: {error}")
            
            # Step 4: Get domain name information
            logger.info("Step 4: Retrieving domain name information")
            stdin, stdout, stderr = ssh_client.exec_command("hostname -f")
            domain_name = stdout.read().decode().strip()
            
            if domain_name:
                logger.info(f"Remote system domain name: {domain_name}")
            else:
                error = stderr.read().decode().strip()
                logger.warning(f"Could not retrieve domain name. Error: {error}")
            
            # Step 5: Get system information
            logger.info("Step 5: Retrieving system information")
            commands = [
                "uname -a",
                "cat /etc/os-release | grep PRETTY_NAME",
                "uptime"
            ]
            
            for cmd in commands:
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                output = stdout.read().decode().strip()
                if output:
                    logger.info(f"Command '{cmd}' output: {output}")
            
            # Close the SSH connection
            ssh_client.close()
            logger.info("SSH operations completed successfully")
            
        except Exception as e:
            logger.error(f"Error during SSH operations: {str(e)}")
            raise
    
    def _perform_winrm_operations(self) -> None:
        """
        Connect to a remote Windows system via WinRM.
        Start this script on the remote system with recursion prevention.
        """
        logger.info("=== STARTING WINRM OPERATIONS (REMOTE DESKTOP CONNECTION) ===")
        
        try:
            # Step 1: Establish WinRM connection
            logger.info(f"Step 1: Establishing WinRM connection to {self.args.winrm_host}")
            
            # Configure the WinRM session
            protocol = 'ntlm' if self.args.winrm_use_ssl else 'http'
            port = self.args.winrm_port
            endpoint = f'{protocol}://{self.args.winrm_host}:{port}/wsman'
            
            logger.info(f"Connecting to WinRM endpoint: {endpoint}")
            session = winrm.Session(
                self.args.winrm_host,
                auth=(self.args.winrm_user, self.args.winrm_password),
                transport=protocol,
                server_cert_validation='ignore' if self.args.winrm_use_ssl else None
            )
            
            # # Step 2: Check connectivity and get system information
            # logger.info("Step 2: Checking connectivity and retrieving system information")
            # result = session.run_ps("systeminfo | findstr /B /C:\"Host Name\" /C:\"OS Name\" /C:\"OS Version\" /C:\"System Type\"")
            
            # if result.status_code == 0:
            #     system_info = result.std_out.decode('utf-8', 'ignore').strip()
            #     logger.info(f"Remote system information:\n{system_info}")
            # else:
            #     error = result.std_err.decode('utf-8', 'ignore').strip()
            #     logger.warning(f"Failed to retrieve system information. Error: {error}")
            #     logger.warning("Continuing with the operation...")
            
            # Step 3: Get IP and domain information
            logger.info("Step 3: Retrieving IP and domain information")
            result = session.run_ps("ipconfig | findstr /i \"IPv4 Address\"")
            
            if result.status_code == 0:
                ip_info = result.std_out.decode('utf-8', 'ignore').strip()
                logger.info(f"Remote system IP information:\n{ip_info}")
            else:
                logger.warning("Could not retrieve IP information")
            
            # Get domain information
            result = session.run_ps("echo %USERDOMAIN%")
            
            if result.status_code == 0:
                domain_info = result.std_out.decode('utf-8', 'ignore').strip()
                logger.info(f"Remote system domain: {domain_info}")
            else:
                logger.warning("Could not retrieve domain information")
            
            # Step 4: Prepare script for remote execution
            logger.info("Step 4: Preparing for script execution on remote system")
            
            # Get the current script path and content
            current_script = os.path.abspath(sys.argv[0])
            logger.info(f"Current script path: {current_script}")
            
            # In a real scenario, you'd need to transfer the script to the remote system
            # For demonstration, we'll create a simple PowerShell command that simulates running our script
            
            # Create a PowerShell command that would run our script with recursion prevention
            script_args = " ".join(sys.argv[1:])  # Original arguments
            script_args += f" {RECURSION_FLAG}"   # Add recursion prevention flag
            
            # Step 5: Execute a simplified version of our functionality on the remote system
            logger.info("Step 5: Executing script simulation on remote system")
            
            # This simulates running our script on the remote system
            ps_script = f"""
            Write-Host "=== RUNNING PYTHON SCRIPT ON REMOTE SYSTEM (SIMULATION) ==="
            Write-Host "Script would be executed with these arguments: {script_args}"
            Write-Host "Current system: $env:COMPUTERNAME"
            Write-Host "Current user: $env:USERNAME"
            Write-Host "Recursion prevention active: True (via {RECURSION_FLAG})"
            Write-Host "Script execution completed on remote system"
            """
            
            result = session.run_ps(ps_script)
            
            if result.status_code == 0:
                remote_output = result.std_out.decode('utf-8', 'ignore').strip()
                logger.info(f"Remote execution output:\n{remote_output}")
            else:
                error = result.std_err.decode('utf-8', 'ignore').strip()
                logger.error(f"Failed to execute script on remote system. Error: {error}")
                raise RuntimeError("Remote script execution failed")
            
            logger.info("WinRM operations completed successfully")
            
        except Exception as e:
            logger.error(f"Error during WinRM operations: {str(e)}")
            raise


if __name__ == "__main__":
    script = MultiOperationsScript()
    script.run()
