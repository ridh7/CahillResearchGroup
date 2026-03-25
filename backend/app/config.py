"""
Application configuration using Pydantic Settings.

All configurable parameters are centralized here and can be overridden
via environment variables with the TOPS_ prefix.
"""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    Settings can be overridden via environment variables with TOPS_ prefix.
    Example: TOPS_STAGE_SERIAL=12345678

    Attributes:
        stage_serial: Thorlabs stage serial number for device identification
        multimeter_serial: BK Precision multimeter serial number
        lockin_pid: SR865A lock-in amplifier USB Product ID
        thorlabs_kinesis_path: Installation path for Thorlabs Kinesis DLLs
        data_directory: Directory for storing measurement data files
        cors_origins: Comma-separated list of allowed CORS origins
    """

    # Hardware Device Identifiers
    stage_serial: str = "103387864"
    multimeter_serial: str = "W114239033"
    lockin_pid: str = "3769"

    # Thorlabs Kinesis Path
    thorlabs_kinesis_path: str = r"C:\Program Files\Thorlabs\Kinesis"

    # Data Directory
    data_directory: str = "./data"

    # Server Configuration
    cors_origins: str = ""  # Comma-separated list of allowed origins

    # Computed Properties
    @property
    def kinesis_device_manager_dll(self) -> str:
        """Path to Thorlabs DeviceManager DLL."""
        return os.path.join(
            self.thorlabs_kinesis_path, "Thorlabs.MotionControl.DeviceManagerCLI.dll"
        )

    @property
    def kinesis_generic_motor_dll(self) -> str:
        """Path to Thorlabs GenericMotor DLL."""
        return os.path.join(
            self.thorlabs_kinesis_path,
            "Thorlabs.MotionControl.GenericMotorCLI.dll",
        )

    @property
    def kinesis_brushless_motor_dll(self) -> str:
        """Path to Thorlabs BrushlessMotor DLL."""
        return os.path.join(
            self.thorlabs_kinesis_path,
            "ThorLabs.MotionControl.Benchtop.BrushlessMotorCLI.dll",
        )

    class Config:
        env_prefix = "TOPS_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
