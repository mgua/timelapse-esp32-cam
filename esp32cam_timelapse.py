#!/usr/bin/env python3
"""
ESP32-CAM Timelapse Capture with Adaptive LED Control

Captures a specified number of images from ESP32-CAM at regular intervals.
All camera parameters controllable via command line.
Adaptive LED brightness maintains consistent exposure across varying ambient light.

Usage:
    python esp32cam_timelapse.py --host 172.30.13.113 --frames 100 --interval 20  --output ./timelapses --basename microgreens
    python esp32cam_timelapse.py --host 172.30.13.113 --resolution FHD --vflip --frames 100 --interval 10  --output ./timelapses --basename microgreens
    python esp32cam_timelapse.py --host 172.30.13.113 --resolution FHD --vflip --frames 600 --start-frame 516 --interval 60  --output ./timelapses --basename microgreens
    python esp32cam_timelapse.py --host 172.30.13.113 --resolution FHD --vflip --frames 1200 --start-frame 1116 --interval 60  --output ./timelapses --basename microgreens

Requirements:
    python -m pip install pillow numpy requests

Author: Claude (Anthropic) for mgua
Date: 2025-01-17

to be added: better control on output image quality, so to avoid half dark pictures
(a possible approach could be to validate horizontal dark bands, and discard frames that do not 
present uniform average brightness in horizontal bands)


"""

import requests
import time
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from io import BytesIO

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Required packages missing. Install with:")
    print("  pip install pillow numpy requests")
    sys.exit(1)


# Resolution mapping: name -> framesize value
RESOLUTIONS = {
    "96x96": 0,
    "QQVGA": 1,      # 160x120
    "128x128": 2,
    "QCIF": 3,       # 176x144
    "HQVGA": 4,      # 240x176
    "240x240": 5,
    "QVGA": 6,       # 320x240
    "320x320": 7,
    "CIF": 8,        # 400x296
    "HVGA": 9,       # 480x320
    "VGA": 10,       # 640x480
    "SVGA": 11,      # 800x600
    "XGA": 12,       # 1024x768
    "HD": 13,        # 1280x720
    "SXGA": 14,      # 1280x1024
    "UXGA": 15,      # 1600x1200
    "FHD": 16,       # 1920x1080
    "PHD": 17,       # 720x1280 (portrait)
    "P3MP": 18,      # 864x1564
    "QXGA": 19,      # 2048x1564
}


class ESP32CamTimelapse:
    """ESP32-CAM timelapse controller with adaptive LED."""
    
    def __init__(self, args):
        self.args = args
        self.base_url = f"http://{args.host}:{args.port}"
        self.session = requests.Session()
        self.session.timeout = 15
        
        # Adaptive LED state
        self.current_led = args.led_initial
        self.brightness_history: list[float] = []
        
        # Capture state - start from specified frame number
        self.frame_number = args.start_frame
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging."""
        log_format = '%(asctime)s [%(levelname)s] %(message)s'
        
        handlers = [logging.StreamHandler(sys.stdout)]
        
        # Add file handler if output dir specified
        if self.args.output:
            output_dir = Path(self.args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(output_dir / 'capture.log'))
        
        logging.basicConfig(
            level=logging.DEBUG if self.args.verbose else logging.INFO,
            format=log_format,
            handlers=handlers
        )
        self.logger = logging.getLogger("ESP32Cam")

    def set_control(self, var: str, val) -> bool:
        """Set a camera control parameter."""
        try:
            url = f"{self.base_url}/control?var={var}&val={val}"
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                self.logger.debug(f"Set {var}={val}")
                return True
            else:
                self.logger.warning(f"Failed to set {var}: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            self.logger.error(f"Error setting {var}: {e}")
            return False

    def configure_camera(self):
        """Apply all camera settings from command line arguments."""
        self.logger.info("Configuring camera parameters...")
        
        settings = [
            ("framesize", RESOLUTIONS.get(self.args.resolution, 16)),
            ("quality", self.args.quality),
            ("brightness", self.args.brightness),
            ("contrast", self.args.contrast),
            ("saturation", self.args.saturation),
            ("sharpness", self.args.sharpness),
            ("denoise", self.args.denoise),
            ("ae_level", self.args.ae_level),
            ("gainceiling", self.args.gainceiling),
            ("special_effect", self.args.special_effect),
            ("awb", 1 if self.args.awb else 0),
            ("dcw", 1 if self.args.dcw else 0),
            ("awb_gain", 1 if self.args.awb_gain else 0),
            ("wb_mode", self.args.wb_mode),
            ("aec", 1 if self.args.aec else 0),
            ("aec_value", self.args.aec_value),
            ("aec2", 1 if self.args.aec2 else 0),
            ("agc", 1 if self.args.agc else 0),
            ("agc_gain", self.args.agc_gain),
            ("raw_gma", 1 if self.args.gma else 0),
            ("lenc", 1 if self.args.lenc else 0),
            ("hmirror", 1 if self.args.hmirror else 0),
            ("vflip", 1 if self.args.vflip else 0),
            ("bpc", 1 if self.args.bpc else 0),
            ("wpc", 1 if self.args.wpc else 0),
            ("colorbar", 1 if self.args.colorbar else 0),
        ]
        
        for var, val in settings:
            self.set_control(var, val)
            time.sleep(0.05)  # Small delay between settings
        
        # Set initial LED
        self.set_control("led_intensity", self.current_led)
        
        self.logger.info("Camera configuration complete")

    def capture_image(self) -> Tuple[Optional[Image.Image], str]:
        """Capture a single image from the ESP32-CAM."""
        try:
            url = f"{self.base_url}/capture?_cb={int(time.time() * 1000)}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                return image, ""
            else:
                return None, f"HTTP {response.status_code}"
                
        except requests.RequestException as e:
            return None, f"Request error: {e}"
        except Exception as e:
            return None, f"Image processing error: {e}"

    def calculate_brightness(self, image: Image.Image) -> float:
        """Calculate average brightness of an image."""
        grayscale = image.convert('L')
        np_image = np.array(grayscale)
        return float(np.mean(np_image))

    def get_running_average(self) -> Optional[float]:
        """Get running average brightness."""
        if not self.brightness_history:
            return None
        return sum(self.brightness_history) / len(self.brightness_history)

    def update_brightness_history(self, brightness: float):
        """Update brightness history."""
        self.brightness_history.append(brightness)
        if len(self.brightness_history) > 10:
            self.brightness_history.pop(0)

    def is_consistent(self, brightness: float) -> bool:
        """Check if brightness is consistent with history."""
        avg = self.get_running_average()
        if avg is None:
            return True
        return abs(brightness - avg) <= self.args.consistency_tolerance

    def calculate_led_adjustment(self, brightness: float) -> int:
        """Calculate LED adjustment based on brightness."""
        deviation = self.args.target_brightness - brightness
        
        if abs(deviation) <= self.args.brightness_tolerance:
            return 0
        
        # Proportional adjustment
        adjustment = int(deviation / 8)
        adjustment = max(-20, min(20, adjustment))
        return adjustment

    def capture_with_adaptive_led(self) -> Tuple[Optional[Image.Image], float, int]:
        """Capture image with adaptive LED control and consistency checking."""
        for attempt in range(self.args.max_retries):
            # Set LED before capture
            self.set_control("led_intensity", self.current_led)
            time.sleep(0.2)
            
            # Capture
            image, error = self.capture_image()
            
            # Turn off LED after capture
            if not self.args.led_always_on:
                self.set_control("led_intensity", 0)
            
            if image is None:
                self.logger.warning(f"Capture attempt {attempt+1} failed: {error}")
                time.sleep(1)
                continue
            
            brightness = self.calculate_brightness(image)
            
            # Check consistency
            if not self.is_consistent(brightness):
                avg = self.get_running_average()
                self.logger.warning(
                    f"Inconsistent brightness {brightness:.1f} vs avg {avg:.1f}, retrying..."
                )
                time.sleep(0.5)
                continue
            
            return image, brightness, self.current_led
        
        return None, 0.0, self.current_led

    def generate_filename(self) -> str:
        """Generate filename with 5-digit frame number."""
        return f"{self.args.basename}_{self.frame_number:05d}.jpg"

    def save_image(self, image: Image.Image, brightness: float, led: int) -> str:
        """Save image and metadata."""
        output_dir = Path(self.args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = self.generate_filename()
        filepath = output_dir / filename
        
        # Save image
        image.save(filepath, "JPEG", quality=95)
        
        # Save metadata
        if self.args.save_metadata:
            metadata = {
                'frame': self.frame_number,
                'timestamp': datetime.now().isoformat(),
                'brightness': brightness,
                'led_intensity': led,
                'running_avg': self.get_running_average(),
            }
            meta_path = output_dir / f"{self.args.basename}_{self.frame_number:05d}.json"
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        
        return str(filepath)

    def test_connection(self) -> bool:
        """Test connection to ESP32-CAM."""
        self.logger.info(f"Testing connection to {self.args.host}...")
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                self.logger.info("Connection successful!")
                return True
            else:
                self.logger.error(f"Connection failed: HTTP {response.status_code}")
                return False
        except requests.RequestException as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def run(self):
        """Main capture loop."""
        # Test connection
        if not self.test_connection():
            self.logger.error("Cannot connect to ESP32-CAM. Exiting.")
            return False
        
        # Configure camera
        self.configure_camera()
        
        # Give camera time to apply settings
        time.sleep(1)
        
        # Calculate frame range
        start_frame = self.args.start_frame
        frames_to_capture = self.args.frames
        end_frame = start_frame + frames_to_capture
        
        self.logger.info(f"Starting timelapse: {frames_to_capture} frames, {self.args.interval}s interval")
        self.logger.info(f"Frame range: {start_frame:05d} to {end_frame - 1:05d}")
        self.logger.info(f"Output: {self.args.output}/{self.args.basename}_XXXXX.jpg")
        
        captured_count = 0
        
        try:
            while self.frame_number < end_frame:
                cycle_start = time.time()
                
                progress = self.frame_number - start_frame + 1
                self.logger.info(f"--- Frame {self.frame_number:05d} ({progress}/{frames_to_capture}) ---")
                
                # Capture with adaptive LED
                image, brightness, led = self.capture_with_adaptive_led()
                
                if image is None:
                    self.logger.error("Capture failed after retries, skipping frame")
                    self.frame_number += 1
                    time.sleep(self.args.interval)
                    continue
                
                # Save
                filepath = self.save_image(image, brightness, led)
                self.logger.info(f"Saved: {filepath} (brightness: {brightness:.1f}, LED: {led})")
                
                # Update history
                self.update_brightness_history(brightness)
                
                # Adjust LED for next frame
                adjustment = self.calculate_led_adjustment(brightness)
                if adjustment != 0:
                    new_led = max(0, min(255, self.current_led + adjustment))
                    self.logger.info(f"LED adjustment: {self.current_led} -> {new_led}")
                    self.current_led = new_led
                
                self.frame_number += 1
                captured_count += 1
                
                # Wait for next capture
                if self.frame_number < end_frame:
                    elapsed = time.time() - cycle_start
                    wait_time = max(0, self.args.interval - elapsed)
                    if wait_time > 0:
                        self.logger.info(f"Next capture in {wait_time:.0f}s")
                        time.sleep(wait_time)
                        
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        
        self.logger.info(f"Timelapse complete: {captured_count} frames captured (last frame: {self.frame_number - 1:05d})")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="ESP32-CAM Timelapse with Adaptive LED Control",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Connection
    conn = parser.add_argument_group('Connection')
    conn.add_argument('--host', '-H', default='172.30.13.113',
                      help='ESP32-CAM IP address')
    conn.add_argument('--port', type=int, default=80,
                      help='ESP32-CAM port')
    
    # Capture settings
    capture = parser.add_argument_group('Capture')
    capture.add_argument('--frames', '-n', type=int, default=100,
                         help='Total number of frames to capture')
    capture.add_argument('--start-frame', '-s', type=int, default=0,
                         help='Starting frame number (for resuming interrupted capture)')
    capture.add_argument('--interval', '-i', type=int, default=300,
                         help='Interval between captures in seconds')
    capture.add_argument('--output', '-o', default='./timelapse',
                         help='Output directory')
    capture.add_argument('--basename', '-b', default='frame',
                         help='Base filename (frame number appended as 5 digits)')
    capture.add_argument('--save-metadata', action='store_true', default=True,
                         help='Save JSON metadata alongside images')
    capture.add_argument('--no-metadata', dest='save_metadata', action='store_false',
                         help='Do not save JSON metadata')
    
    # Camera resolution and quality
    cam = parser.add_argument_group('Camera Settings')
    cam.add_argument('--resolution', '-r', default='FHD',
                     choices=list(RESOLUTIONS.keys()),
                     help='Resolution preset')
    cam.add_argument('--quality', type=int, default=10,
                     help='JPEG quality (4-63, lower=better)')
    
    # Image adjustments
    img = parser.add_argument_group('Image Adjustments')
    img.add_argument('--brightness', type=int, default=0,
                     help='Brightness (-3 to 3)')
    img.add_argument('--contrast', type=int, default=0,
                     help='Contrast (-3 to 3)')
    img.add_argument('--saturation', type=int, default=0,
                     help='Saturation (-4 to 4)')
    img.add_argument('--sharpness', type=int, default=2,
                     help='Sharpness (-3 to 3)')
    img.add_argument('--denoise', type=int, default=0,
                     help='De-noise (0=auto, 1-8)')
    img.add_argument('--special-effect', type=int, default=0,
                     help='Special effect (0=none, 1=negative, 2=grayscale, etc)')
    
    # Exposure
    exp = parser.add_argument_group('Exposure')
    exp.add_argument('--ae-level', type=int, default=0,
                     help='Auto exposure level (-5 to 5)')
    exp.add_argument('--gainceiling', type=int, default=0,
                     help='Gain ceiling (0-511)')
    exp.add_argument('--aec', action='store_true', default=True,
                     help='Enable auto exposure control')
    exp.add_argument('--no-aec', dest='aec', action='store_false',
                     help='Disable auto exposure control')
    exp.add_argument('--aec-value', type=int, default=320,
                     help='Manual exposure value (0-1536)')
    exp.add_argument('--aec2', action='store_true', default=False,
                     help='Enable night mode')
    exp.add_argument('--agc', action='store_true', default=False,
                     help='Enable auto gain control')
    exp.add_argument('--agc-gain', type=int, default=5,
                     help='Manual gain (0-64)')
    
    # White balance
    wb = parser.add_argument_group('White Balance')
    wb.add_argument('--awb', action='store_true', default=True,
                    help='Enable auto white balance')
    wb.add_argument('--no-awb', dest='awb', action='store_false',
                    help='Disable auto white balance')
    wb.add_argument('--dcw', action='store_true', default=True,
                    help='Enable advanced AWB')
    wb.add_argument('--awb-gain', action='store_true', default=False,
                    help='Enable manual AWB gain')
    wb.add_argument('--wb-mode', type=int, default=0,
                    help='WB mode (0=auto, 1=sunny, 2=cloudy, 3=office, 4=home)')
    
    # Corrections
    corr = parser.add_argument_group('Corrections')
    corr.add_argument('--gma', action='store_true', default=False,
                      help='Enable gamma correction')
    corr.add_argument('--lenc', action='store_true', default=True,
                      help='Enable lens correction')
    corr.add_argument('--no-lenc', dest='lenc', action='store_false',
                      help='Disable lens correction')
    corr.add_argument('--bpc', action='store_true', default=False,
                      help='Enable black pixel correction')
    corr.add_argument('--wpc', action='store_true', default=True,
                      help='Enable white pixel correction')
    
    # Orientation
    orient = parser.add_argument_group('Orientation')
    orient.add_argument('--hmirror', action='store_true', default=False,
                        help='Horizontal mirror')
    orient.add_argument('--vflip', action='store_true', default=False,
                        help='Vertical flip')
    orient.add_argument('--colorbar', action='store_true', default=False,
                        help='Show color bar (for testing)')
    
    # LED and adaptive brightness
    led = parser.add_argument_group('LED / Adaptive Brightness')
    led.add_argument('--led-initial', type=int, default=50,
                     help='Initial LED intensity (0-255)')
    led.add_argument('--led-always-on', action='store_true', default=False,
                     help='Keep LED on between captures')
    led.add_argument('--target-brightness', type=int, default=128,
                     help='Target image brightness (0-255)')
    led.add_argument('--brightness-tolerance', type=int, default=30,
                     help='Acceptable brightness deviation from target')
    led.add_argument('--consistency-tolerance', type=int, default=40,
                     help='Max deviation from running average before retry')
    led.add_argument('--max-retries', type=int, default=3,
                     help='Max capture retries per frame')
    
    # Debug
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--test', action='store_true',
                        help='Test connection and capture single frame')
    
    args = parser.parse_args()
    
    # Create controller
    controller = ESP32CamTimelapse(args)
    
    if args.test:
        # Test mode
        if controller.test_connection():
            controller.configure_camera()
            time.sleep(1)
            controller.args.frames = 1
            controller.run()
        sys.exit(0)
    
    # Run timelapse
    controller.run()


if __name__ == "__main__":
    main()
