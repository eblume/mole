import subprocess


def run_airflow(port: int) -> None:
    process = subprocess.Popen(f"airflow webserver -p {port}", shell=True)
    process.communicate()
