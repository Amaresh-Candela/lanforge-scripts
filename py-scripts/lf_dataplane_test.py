#!/usr/bin/env python3
"""
# lf_dataplane_test.py

## Purpose
`lf_dataplane_test.py` runs LANforge Chamber View Dataplane tests with command-line or JSON configuration. It supports multiple test combinations by varying traffic direction, traffic type, WiFi settings, and attenuation settings.

## How the script works
The script builds a Chamber View Dataplane configuration, applies command-line or JSON overrides, runs the test, and then checks whether KPI results were generated. JSON input overrides matching CLI values.

## Practical inputs you usually need
The script does not mark most arguments as strictly required in `argparse`, but a meaningful Dataplane test normally needs:

- `--upstream` — upstream Ethernet port
- `--station` — station interface under test
- `--direction` — traffic direction relative to the DUT
- `--type` — traffic protocol
- `--speed` — requested traffic rate

Depending on the test setup, you may also need LANforge manager and login values from the common Chamber View base parser, such as manager IP, port, username, and password.

## Canonical argument names
Use these names in documentation and examples. The script also accepts aliases for backward compatibility.

| Functionality | Canonical name | Common aliases |
|---|---|---|
| Upstream port | `--upstream` | `-u` |
| Station | `--station` | — |
| DUT name | `--dut` | — |
| Traffic direction | `--direction` | `--directions`, `--traffic_direction`, `--traffic_directions` |
| Traffic type | `--type` | `--types`, `--traffic_type`, `--traffic_types` |
| Traffic rate | `--speed` | `--rate`, `--download_speed`, `--download_rate` |
| Opposite traffic rate | `--opposite_speed` | `--opposite_rate`, `--upload_speed`, `--upload_rate` |
| Duration | `--duration` | — |
| Spatial streams | `--nss` | `--spatial_streams` |
| Bandwidth | `--bandwidth` | `--bandwidths` |
| Channel | `--channel` | `--channels` |
| First attenuator | `--attenuator` | `--attenuator1` |
| Second attenuator | `--attenuator2` | — |
| Simplified attenuation min | `--atten_min` | `--atten1_min` |
| Simplified attenuation step | `--atten_step` | `--atten1_step` |
| Simplified attenuation max | `--atten_max` | `--atten1_max` |
| Direct attenuation values | `--attenuations` | `--attenuations1` |
| Second direct attenuation values | `--attenuations2` | — |
| JSON config | `--json` | — |
| Verbosity | `--verbosity` | — |

## Argument details

### Traffic configuration
`--direction`
: Direction of generated traffic relative to the DUT.
  Supported values: `DUT-TX`, `DUT-RX`
  Example: `DUT-TX,DUT-RX`

`--type`
: Traffic protocol.
  Supported values: `UDP`, `TCP`
  Example: `UDP,TCP`

`--speed`
: Primary traffic rate for the selected direction.
  Examples: `70%`, `250Mbps`, `1Gbps`

`--opposite_speed`
: Traffic rate for the opposite direction when bidirectional behavior is needed.

`--duration`
: Duration of each traffic run.
  Examples: `30s`, `1m`, `5m`

### WiFi configuration
`--nss`
: Spatial stream configuration.
  Examples: `1`, `2`, `AUTO`, `1,2,3,4`

`--bandwidth`
: WiFi bandwidth selection.
  Supported values: `20`, `40`, `80`, `160`, `320`
  Examples: `20,40,80`

`--channel`
: Channel selection.
  Examples: `6`, `36`, `6,36`

### Attenuator configuration
`--attenuator`
: EID of the first attenuator.

`--attenuator2`
: EID of the second attenuator.

`--atten_min`, `--atten_step`, `--atten_max`
: Simplified attenuation controls in dB for the first attenuator. These are converted internally to the GUI format.

`--attenuations`
: Direct attenuation values for the first attenuator in ddB.
  Format: `START..STEP..STOP`
  Example: `0..+100..955`

`--attenuations2`
: Direct attenuation values for the second attenuator in ddB.

### Other options
`--dut`
: DUT name already configured in Chamber View.

`--verbosity`
: Report verbosity level.
  Default: `5`

`--json`
: JSON configuration file. Values in the JSON file override matching CLI values.

`--graph_groups`
: Local file path used to save graph group data.

`--local_lf_report_dir`
: Local directory where reports will be downloaded. Use with `--pull_report`.

`--help_summary`
: Prints a short summary of what the script does.

## Example commands

### Basic UDP test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-TX     --type UDP     --speed 70%
```

### TCP test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-RX     --type TCP     --speed 1Gbps
```

### Bidirectional test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-TX,DUT-RX     --type UDP,TCP     --speed 250Mbps
```

### Multiple NSS values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --type UDP     --speed 100Mbps     --nss 1,2,3,4
```

### Multiple bandwidth values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --type UDP     --speed 100Mbps     --bandwidth 80,160,320
```

### Channel selection
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --channel 36
```

### Simplified attenuation
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --atten_min 10     --atten_step 10     --atten_max 95
```

### Direct attenuation values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --attenuations "0..+100..955"
```

### Two attenuators
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --attenuations "0..+100..955"     --attenuator2 1.1.3281     --attenuations2 "0..+100..955"
```

### JSON configuration
```bash
./lf_dataplane_test.py --json test.json
```

Example JSON:
```json
{
  "upstream": "1.1.eth1",
  "station": "1.1.wlan0",
  "direction": "DUT-TX",
  "type": "UDP",
  "speed": "1Gbps"
}
```

## Notes
- JSON values override matching command-line values.
- Comma-separated values create multiple test combinations.
- `--atten_min`, `--atten_step`, and `--atten_max` are interpreted in dB.
- `--attenuations` and `--attenuations2` use ddB format with `START..STEP..STOP`.
- Multiple traffic types, directions, NSS values, bandwidths, and channels are combined automatically into test scenarios.
- `--speed` may be given as an absolute rate or a percentage of theoretical throughput.
- The script uses the Chamber View base parser, so common connection settings such as manager IP and login credentials may also be needed depending on your environment.

"""
import sys
import os
import importlib
import argparse
import time
import json
import logging


if sys.version_info[0] != 3:
    print("This script requires Python 3")
    exit(1)

sys.path.append(os.path.join(os.path.abspath(__file__ + "../../../")))

cv_test_manager = importlib.import_module("py-json.cv_test_manager")
cv_test = cv_test_manager.cv_test
cv_add_base_parser = cv_test_manager.cv_add_base_parser
cv_base_adjust_parser = cv_test_manager.cv_base_adjust_parser

lf_logger_config = importlib.import_module("py-scripts.lf_logger_config")

logger = logging.getLogger(__name__)


class DataplaneTest(cv_test):
    SPATIAL_STREAMS_MAP = {
        "AUTO": "AUTO",
        "auto": "AUTO",
        "1": "1",
        "2": "2",
        "3": "3",
        "4": "4",
        "1x1": "1",
        "2x2": "2",
        "3x3": "3",
        "4x4": "4",
    }

    BANDWIDTH_MAP = {
        "No-Change": "No-Change",
        "no-change": "no-change",
        "AUTO": "AUTO",
        "auto": "AUTO",
        "20": "20",
        "40": "40",
        "80": "80",
        "160": "160",
        "320": "320",
        "20MHz": "20",
        "40MHz": "40",
        "80MHz": "80",
        "160MHz": "160",
        "320MHz": "320",
    }

    TRAFFIC_DIRECTION_MAP = {
        "DUT-TX": "DUT Transmit",
        "dut-tx": "DUT Transmit",
        "transmit": "DUT Transmit",
        "DUT-RX": "DUT Receive",
        "dut-rx": "DUT Receive",
        "receive": "DUT Receive",
    }

    TRAFFIC_TYPE_MAP = {
        "UDP": "UDP",
        "udp": "UDP",
        "lf_udp": "UDP",
        "TCP": "TCP",
        "tcp": "TCP",
        "lf_tcp": "TCP",
    }

    def __init__(self,
                 lf_host="localhost",
                 lf_port=8080,
                 lf_user="lanforge",
                 lf_password="lanforge",
                 ssh_port=22,
                 local_lf_report_dir="",
                 instance_name="dpt_instance",
                 config_name="dpt_config",
                 upstream="1.1.eth2",
                 pull_report=False,
                 load_old_cfg=False,
                 spatial_streams=None,
                 bandwidths=None,
                 channels=None,
                 traffic_directions=None,
                 traffic_types=None,
                 opposite_speed="0",
                 speed="85%",
                 duration="15s",
                 station="1.1.sta01500",
                 dut="NA",
                 attenuator=None,
                 attenuator2=None,
                 atten_min=None,
                 atten_step=None,
                 atten_max=None,
                 atten2_min=None,
                 atten2_step=None,
                 atten2_max=None,
                 attenuations=None,
                 attenuations2=None,
                 enables=None,
                 disables=None,
                 raw_lines=None,
                 raw_lines_file="",
                 sets=None,
                 graph_groups=None,
                 test_rig="",
                 test_tag="",
                 verbosity='5',
                 **kwargs):
        super().__init__(lfclient_host=lf_host, lfclient_port=lf_port)

        # From CV base argument parser
        self.lf_host = lf_host
        self.lf_port = lf_port
        self.lf_user = lf_user
        self.lf_password = lf_password
        self.ssh_port = ssh_port
        self.instance_name = instance_name
        self.config_name = config_name
        self.pull_report = pull_report
        self.load_old_cfg = load_old_cfg
        self.enables = enables
        self.disables = disables
        self.sets = sets
        self.raw_lines = raw_lines
        self.raw_lines_file = raw_lines_file
        self.test_rig = test_rig
        self.test_tag = test_tag

        # Specific to this test script
        self.test_name = "Dataplane"

        self.upstream = upstream
        self.station = station
        self.dut = dut
        self.opposite_speed = opposite_speed
        self.speed = speed
        self.duration = duration
        self.verbosity = verbosity
        self.graph_groups = graph_groups
        self.local_lf_report_dir = local_lf_report_dir

        # WiFi configuration
        self.spatial_streams = DataplaneTest._prepare_as_rawline(spatial_streams, self.SPATIAL_STREAMS_MAP)
        self.bandwidths = DataplaneTest._prepare_as_rawline(bandwidths, self.BANDWIDTH_MAP)
        self.channels = DataplaneTest._prepare_as_rawline(channels, None)

        # Traffic configuration
        self.traffic_directions = DataplaneTest._prepare_as_rawline(traffic_directions, self.TRAFFIC_DIRECTION_MAP)
        self.traffic_types = DataplaneTest._prepare_as_rawline(traffic_types, self.TRAFFIC_TYPE_MAP)

        # Attenuator configuration
        self.attenuator = attenuator
        self.attenuator2 = attenuator2

        self.atten_min = atten_min
        self.atten2_min = atten2_min

        self.atten_step = atten_step
        self.atten2_step = atten2_step

        self.atten_max = atten_max
        self.atten2_max = atten2_max

        self.attenuations = attenuations
        self.attenuations2 = attenuations2
        self._apply_simplified_atten_cli()

    def _prepare_as_rawline(value: str, map: dict) -> str:
        """Convert from script execution-friendly configuration to that expected by the GUI.

        Assumes provided string is a comma-separated list of values or None.
        Expected that values have already been verified to be valid for the test.
        Output is semi-colon (';') separated values, as expected by the GUI,
        or None, in which case test logic will ignore this as part of the config.

        Args:
            value (str): Comma-separated string to convert
            map (dict): Optional mapping of strings to strings, where the mapped value
                        corresponds to that expected by the GUI (e.g. 'lf_udp' -> 'UDP').

        Returns:
            str: Converted semi-colon-separated string or None
        """
        ret = None

        if value:
            if map is None:
                ret = ";".join(value.split(","))
            else:
                converted_values = [map[key] for key in value.split(",")]
                ret = ";".join(converted_values)

        return ret

    def _apply_simplified_atten_cli(self):
        """If specified, configure test attenuations using simplified CLI."""
        if self.atten_min or self.atten_step or self.atten_max:
            # Something is specified, set defaults, then apply what is specified.
            amin = 0
            astep = 50
            amax = 950
            if self.atten_min:
                amin = int(self.atten_min * 10)
            if self.atten_step:
                astep = int(self.atten_step * 10)
            if self.atten_max:
                amax = int(self.atten_max * 10)

            # Multiply as value is in dB but GUI expectes ddB
            self.attenuations = f"{amin}..+{astep}..{amax}"

        if self.atten2_min or self.atten2_step or self.atten2_max:
            # Something is specified, set defaults, then apply what is specified.
            amin = 0
            astep = 50
            amax = 950
            if self.atten2_min:
                amin = int(self.atten2_min * 10)
            if self.atten2_step:
                astep = int(self.atten2_step * 10)
            if self.atten2_max:
                amax = int(self.atten2_max * 10)

            # Multiply as value is in dB but GUI expectes ddB
            self.attenuations2 = f"{amin}..+{astep}..{amax}"

    def setup(self):
        # Nothing to do at this time.
        return

    def run(self):
        self.sync_cv()
        time.sleep(2)
        self.sync_cv()

        blob_test = "dataplane-test-latest-"

        # To delete old config with same name
        self.rm_text_blob(config_name=self.config_name,
                          blob_test_name=blob_test)
        self.show_text_blob(config_name=None,
                            blob_test_name=None,
                            brief=False)

        # Test related settings
        cfg_options = []

        self.apply_cfg_options(cfg_options=cfg_options,
                               enables=self.enables,
                               disables=self.disables,
                               raw_lines=self.raw_lines,
                               raw_lines_file=self.raw_lines_file)

        # NOTE: Exercise caution when adding new arguments here,
        #       as it is very easy to break previous functionality
        #
        # Command line args take precedence over enables, disables, and raw lines,
        # so adjust here after config options were applied
        #
        # General test configuration
        if self.upstream != "":
            cfg_options.append("upstream_port: " + self.upstream)
        if self.station != "":
            cfg_options.append("traffic_port: " + self.station)
        if self.duration != "":
            cfg_options.append("duration: " + self.duration)

        # WiFi configuration
        if self.spatial_streams:
            cfg_options.append("spatial_streams: " + self.spatial_streams)
        if self.bandwidths:
            cfg_options.append("bandw_options: " + self.bandwidths)
        if self.channels:
            cfg_options.append("channels: " + self.channels)

        # Traffic configuration
        if self.traffic_directions:
            cfg_options.append("directions: " + self.traffic_directions)
        if self.traffic_types:
            cfg_options.append("traffic_types: " + self.traffic_types)
        if self.speed != "":
            cfg_options.append("speed: " + self.speed)
        if self.opposite_speed != "":
            cfg_options.append("speed2: " + self.opposite_speed)

        # Attenuator configuration
        if self.attenuator:
            cfg_options.append("attenuator: " + self.attenuator)
        if self.attenuator2:
            cfg_options.append("attenuator2: " + self.attenuator2)
        if self.attenuations:
            cfg_options.append("attenuations: " + self.attenuations)
        if self.attenuations2:
            cfg_options.append("attenuations2: " + self.attenuations2)

        # Reporting configuration
        if self.dut != "":
            cfg_options.append("selected_dut: " + self.dut)
        if self.test_rig != "":
            cfg_options.append("test_rig: " + self.test_rig)
        if self.test_tag != "":
            cfg_options.append("test_tag: " + self.test_tag)

        # We deleted the scenario earlier, now re-build new one line at a time.
        self.build_cfg(config_name=self.config_name,
                       blob_test=blob_test,
                       cfg_options=cfg_options)

        cv_cmds = []

        cmd = "cv set '%s' 'VERBOSITY' '%s'" % (self.instance_name, self.verbosity)
        cv_cmds.append(cmd)

        self.create_and_run_test(load_old_cfg=self.load_old_cfg,
                                 test_name=self.test_name,
                                 instance_name=self.instance_name,
                                 config_name=self.config_name,
                                 sets=self.sets,
                                 pull_report=self.pull_report,
                                 lf_host=self.lf_host,
                                 lf_user=self.lf_user,
                                 lf_password=self.lf_password,
                                 cv_cmds=cv_cmds,
                                 ssh_port=self.ssh_port,
                                 local_lf_report_dir=self.local_lf_report_dir,
                                 graph_groups_file=self.graph_groups)
        # To delete old config with same name
        self.rm_text_blob(config_name=self.config_name,
                          blob_test_name=blob_test)


def parse_args():
    """Parse test script arguments."""
    parser = argparse.ArgumentParser(
        prog='lf_dataplane_test',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''\
         Data Plane Test
            ''',
        description=r"""
# lf_dataplane_test.py

## Purpose
`lf_dataplane_test.py` runs LANforge Chamber View Dataplane tests with command-line or JSON configuration. It supports multiple test combinations by varying traffic direction, traffic type, WiFi settings, and attenuation settings.

## How the script works
The script builds a Chamber View Dataplane configuration, applies command-line or JSON overrides, runs the test, and then checks whether KPI results were generated. JSON input overrides matching CLI values.

## Practical inputs you usually need
The script does not mark most arguments as strictly required in `argparse`, but a meaningful Dataplane test normally needs:

- `--upstream` — upstream Ethernet port
- `--station` — station interface under test
- `--direction` — traffic direction relative to the DUT
- `--type` — traffic protocol
- `--speed` — requested traffic rate

Depending on the test setup, you may also need LANforge manager and login values from the common Chamber View base parser, such as manager IP, port, username, and password.

## Canonical argument names
Use these names in documentation and examples. The script also accepts aliases for backward compatibility.

| Functionality | Canonical name | Common aliases |
|---|---|---|
| Upstream port | `--upstream` | `-u` |
| Station | `--station` | — |
| DUT name | `--dut` | — |
| Traffic direction | `--direction` | `--directions`, `--traffic_direction`, `--traffic_directions` |
| Traffic type | `--type` | `--types`, `--traffic_type`, `--traffic_types` |
| Traffic rate | `--speed` | `--rate`, `--download_speed`, `--download_rate` |
| Opposite traffic rate | `--opposite_speed` | `--opposite_rate`, `--upload_speed`, `--upload_rate` |
| Duration | `--duration` | — |
| Spatial streams | `--nss` | `--spatial_streams` |
| Bandwidth | `--bandwidth` | `--bandwidths` |
| Channel | `--channel` | `--channels` |
| First attenuator | `--attenuator` | `--attenuator1` |
| Second attenuator | `--attenuator2` | — |
| Simplified attenuation min | `--atten_min` | `--atten1_min` |
| Simplified attenuation step | `--atten_step` | `--atten1_step` |
| Simplified attenuation max | `--atten_max` | `--atten1_max` |
| Direct attenuation values | `--attenuations` | `--attenuations1` |
| Second direct attenuation values | `--attenuations2` | — |
| JSON config | `--json` | — |
| Verbosity | `--verbosity` | — |

## Argument details

### Traffic configuration
`--direction`
: Direction of generated traffic relative to the DUT.
  Supported values: `DUT-TX`, `DUT-RX`
  Example: `DUT-TX,DUT-RX`

`--type`
: Traffic protocol.
  Supported values: `UDP`, `TCP`
  Example: `UDP,TCP`

`--speed`
: Primary traffic rate for the selected direction.
  Examples: `70%`, `250Mbps`, `1Gbps`

`--opposite_speed`
: Traffic rate for the opposite direction when bidirectional behavior is needed.

`--duration`
: Duration of each traffic run.
  Examples: `30s`, `1m`, `5m`

### WiFi configuration
`--nss`
: Spatial stream configuration.
  Examples: `1`, `2`, `AUTO`, `1,2,3,4`

`--bandwidth`
: WiFi bandwidth selection.
  Supported values: `20`, `40`, `80`, `160`, `320`
  Examples: `20,40,80`

`--channel`
: Channel selection.
  Examples: `6`, `36`, `6,36`

### Attenuator configuration
`--attenuator`
: EID of the first attenuator.

`--attenuator2`
: EID of the second attenuator.

`--atten_min`, `--atten_step`, `--atten_max`
: Simplified attenuation controls in dB for the first attenuator. These are converted internally to the GUI format.

`--attenuations`
: Direct attenuation values for the first attenuator in ddB.
  Format: `START..STEP..STOP`
  Example: `0..+100..955`

`--attenuations2`
: Direct attenuation values for the second attenuator in ddB.

### Other options
`--dut`
: DUT name already configured in Chamber View.

`--verbosity`
: Report verbosity level.
  Default: `5`

`--json`
: JSON configuration file. Values in the JSON file override matching CLI values.

`--graph_groups`
: Local file path used to save graph group data.

`--local_lf_report_dir`
: Local directory where reports will be downloaded. Use with `--pull_report`.

`--help_summary`
: Prints a short summary of what the script does.

## Example commands

### Basic UDP test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-TX     --type UDP     --speed 70%
```

### TCP test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-RX     --type TCP     --speed 1Gbps
```

### Bidirectional test
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --direction DUT-TX,DUT-RX     --type UDP,TCP     --speed 250Mbps
```

### Multiple NSS values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --type UDP     --speed 100Mbps     --nss 1,2,3,4
```

### Multiple bandwidth values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --type UDP     --speed 100Mbps     --bandwidth 80,160,320
```

### Channel selection
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --channel 36
```

### Simplified attenuation
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --atten_min 10     --atten_step 10     --atten_max 95
```

### Direct attenuation values
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --attenuations "0..+100..955"
```

### Two attenuators
```bash
./lf_dataplane_test.py     --upstream 1.1.eth1     --station 1.1.wlan0     --speed 100Mbps     --attenuator 1.1.3273     --attenuations "0..+100..955"     --attenuator2 1.1.3281     --attenuations2 "0..+100..955"
```

### JSON configuration
```bash
./lf_dataplane_test.py --json test.json
```

Example JSON:
```json
{
  "upstream": "1.1.eth1",
  "station": "1.1.wlan0",
  "direction": "DUT-TX",
  "type": "UDP",
  "speed": "1Gbps"
}
```

## Notes
- JSON values override matching command-line values.
- Comma-separated values create multiple test combinations.
- `--atten_min`, `--atten_step`, and `--atten_max` are interpreted in dB.
- `--attenuations` and `--attenuations2` use ddB format with `START..STEP..STOP`.
- Multiple traffic types, directions, NSS values, bandwidths, and channels are combined automatically into test scenarios.
- `--speed` may be given as an absolute rate or a percentage of theoretical throughput.
- The script uses the Chamber View base parser, so common connection settings such as manager IP and login credentials may also be needed depending on your environment.

""")

    cv_add_base_parser(parser)  # see cv_test_manager.py

    # Test configuration
    parser.add_argument(
    '--json',
    help="Path to a JSON configuration file. When provided, JSON values override matching command-line arguments.",
    default=""
    )

    parser.add_argument(
        "-u", "--upstream",
        dest="upstream",
        type=str,
        default="",
        help="Upstream Ethernet port used for traffic generation. Example: 1.1.eth2"
    )

    parser.add_argument(
        "--station",
        type=str,
        default="",
        help="Station interface used for the test. Example: 1.1.sta01500"
    )

    parser.add_argument(
        "--dut",
        default="",
        help="Name of the DUT configured in Chamber View. Example: linksys-8450"
    )

    # WiFi Configuration
    parser.add_argument(
        "--nss", "--spatial_streams",
        dest="spatial_streams",
        default=None,
        type=str,
        help="WiFi spatial stream (NSS) configuration. Multiple values may be provided as a comma-separated list. Example: 1,2,3,4"
    )

    parser.add_argument(
        "--bandwidth", "--bandwidths",
        dest="bandwidths",
        default=None,
        type=str,
        help="WiFi channel bandwidth in MHz. Multiple values may be provided. Supported values: 20,40,80,160,320"
    )

    parser.add_argument(
        "--channel", "--channels",
        dest="channels",
        default=None,
        type=str,
        help="WiFi channel(s) used during the test. Multiple values may be provided. Example: 6,36"
    )

    # Traffic Configuration
    parser.add_argument(
        "--direction", "--directions",
        "--traffic_direction", "--traffic_directions",
        dest="traffic_directions",
        default=None,
        type=str,
        help="Traffic direction relative to the DUT. Supported values: DUT-TX, DUT-RX. Multiple values allowed."
    )

    parser.add_argument(
        "--type", "--types",
        "--traffic_type", "--traffic_types",
        dest="traffic_types",
        default=None,
        type=str,
        help="Traffic protocol to generate. Supported values: UDP, TCP. Multiple values allowed."
    )

    parser.add_argument(
        "--speed", "--rate",
        "--download_speed", "--download_rate",
        dest="speed",
        default="",
        help="Primary traffic rate. Supports Mbps, Gbps, or percentage of theoretical throughput. Default: 85%%"
    )

    parser.add_argument(
        "--opposite_speed", "--opposite_rate",
        "--upload_speed", "--upload_rate",
        dest="opposite_speed",
        default="",
        help="Traffic rate for the opposite direction. Supports Mbps, Gbps, or percentage. Default: 0"
    )

    parser.add_argument(
        "--duration",
        default="",
        help="Duration of each traffic run. Example: 30s, 1m, 5m"
    )

    parser.add_argument(
        "--verbosity",
        default="5",
        help="Report verbosity level (1-11). Higher values generate more detailed reports. Default: 5"
    )

    # Attenuator Configuration
    parser.add_argument(
        "--attenuator", "--attenuator1",
        dest="attenuator",
        default=None,
        help="EID of the first attenuator. Example: 1.1.3384"
    )

    parser.add_argument(
        "--attenuator2",
        dest="attenuator2",
        default=None,
        help="EID of the second attenuator."
    )

    parser.add_argument(
        "--atten_min", "--atten1_min",
        dest="atten_min",
        default=None,
        type=int,
        help="Minimum attenuation (dB) for the first attenuator. Overrides --attenuations."
    )

    parser.add_argument(
        "--atten_step", "--atten1_step",
        dest="atten_step",
        default=None,
        type=int,
        help="Attenuation step size (dB) for the first attenuator. Overrides --attenuations."
    )

    parser.add_argument(
        "--atten_max", "--atten1_max",
        dest="atten_max",
        default=None,
        type=int,
        help="Maximum attenuation (dB) for the first attenuator. Overrides --attenuations."
    )

    parser.add_argument(
        "--atten2_min",
        dest="atten2_min",
        default=None,
        type=int,
        help="Minimum attenuation (dB) for the second attenuator. Overrides --attenuations2."
    )

    parser.add_argument(
        "--atten2_step",
        dest="atten2_step",
        default=None,
        type=int,
        help="Attenuation step size (dB) for the second attenuator. Overrides --attenuations2."
    )

    parser.add_argument(
        "--atten2_max",
        dest="atten2_max",
        default=None,
        type=int,
        help="Maximum attenuation (dB) for the second attenuator. Overrides --attenuations2."
    )

    parser.add_argument(
        "--attenuations", "--attenuations1",
        dest="attenuations",
        default=None,
        help="Direct attenuation values for the first attenuator in ddB format. Example: 0..+100..955"
    )

    parser.add_argument(
        "--attenuations2",
        dest="attenuations2",
        default=None,
        help="Direct attenuation values for the second attenuator in ddB format."
    )

    # Report Generation
    parser.add_argument(
        "--graph_groups",
        default=None,
        help="Path to save graph group information."
    )

    parser.add_argument(
        "--local_lf_report_dir",
        help="Local directory where reports are downloaded. Requires --pull_report."
    )

    # Logging
    parser.add_argument(
        "--lf_logger_config_json",
        help="Path to a custom logger configuration JSON file."
    )

    parser.add_argument(
        "--logger_no_file",
        default=None,
        action="store_true",
        help="Display log messages without file names or line numbers."
    )

    parser.add_argument(
        "--help_summary",
        default=None,
        action="store_true",
        help="Display a brief overview of the script and its functionality."
    )

    return parser.parse_args()


def validate_args(args):
    """
    Sanity check specified script arguments.

    This should be run after JSON overrides are applied.
    """
    if not args.pull_report and args.local_lf_report_dir is not None:
        logger.warning("""local_lf_report_dir set and --pull_report not set,
              reports will not be pulled to the local_lf_report_dir
              unless --pull_report also set""")
    if args.local_lf_report_dir is None:
        args.local_report_dir = ""

    # TODO: Can properly move some of this code to a helper, specifically mapping checks
    # Traffic configuration
    if args.traffic_directions:
        traffic_directions = args.traffic_directions.split(",")

        if len(traffic_directions) > 2:
            logger.error("Only two traffic directions are possible, DUT transmit and DUT receive")
            exit(1)

        for direction in traffic_directions:
            if direction not in DataplaneTest.TRAFFIC_DIRECTION_MAP:
                logger.error(f"Unexpected traffic direction {direction}, supported are: {DataplaneTest.TRAFFIC_DIRECTION_MAP.keys()}")
                exit(1)

    if args.traffic_types:
        traffic_types = args.traffic_types.split(",")

        for traffic_type in traffic_types:
            if traffic_type not in DataplaneTest.TRAFFIC_TYPE_MAP:
                logger.error(f"Unexpected traffic type {traffic_type}, supported are: {DataplaneTest.TRAFFIC_TYPE_MAP.keys()}. "
                             "Other traffic types are supported in the GUI. If you're interested in using them in this script, "
                             "please contact 'support@candelatech.com'.")
                exit(1)

        if len(traffic_types) > 2:
            logger.error("Unexpected number of traffic types. Expected two, UDP and/or TCP.")
            exit(1)

    # WiFi configuration
    if args.spatial_streams:
        spatial_streams = args.spatial_streams.split(",")

        for spatial_stream in spatial_streams:
            if spatial_stream not in DataplaneTest.SPATIAL_STREAMS_MAP:
                logger.error(f"Unexpected spatial streams configuration {spatial_stream}, supported are: {DataplaneTest.SPATIAL_STREAMS_MAP.keys()}.")
                exit(1)

        if len(spatial_streams) > 4:
            logger.error("Unexpected number of traffic types. Expected two, UDP and/or TCP.")
            exit(1)
        elif len(spatial_streams) > 1 and "AUTO" in spatial_streams or "auto" in spatial_streams:
            # GUI won't prevent you from doing this, but likely doesn't make sense. Check here to prevent potential confusion
            logger.error("Cannot specify automatic spatial stream configuration with other spatial streams "
                         "configuration selected.")
            exit(1)

    if args.bandwidths:
        bandwidths = args.bandwidths.split(",")

        for bandwidth in bandwidths:
            if bandwidth not in DataplaneTest.BANDWIDTH_MAP:
                logger.error(f"Unexpected bandwidths configuration {bandwidth}, supported are: {DataplaneTest.BANDWIDTH_MAP.keys()}.")
                exit(1)


def configure_logging(args):
    """
    Configure logging for execution of this script.

    Any specified JSON configuration takes precedence.
    """
    logger_config = lf_logger_config.lf_logger_config()

    if args.lf_logger_config_json:
        logger_config.lf_logger_config_json = args.lf_logger_config_json
        logger_config.load_lf_logger_config()

    if args.logger_no_file:
        f = '%(created)f %(levelname)-8s %(message)s'
        ff = logging.Formatter(fmt=f)
        for handler in logging.getLogger().handlers:
            handler.setFormatter(ff)


def apply_json_configuration(args):
    """
    Apply JSON configuration, if specified.

    JSON configuration takes precedent over arguments specified on the command line.
    """
    if not args.json:
        return

    if os.path.exists(args.json):
        with open(args.json, 'r') as json_config:
            json_data = json.load(json_config)
    else:
        logger.error(f"Error reading JSON configuration file '{args.json}'")
        exit(1)

    if "mgr" in json_data:
        args.mgr = json_data["mgr"]
    if "port" in json_data:
        args.port = json_data["port"]
    if "lf_user" in json_data:
        args.lf_user = json_data["lf_user"]
    if "lf_password" in json_data:
        args.lf_password = json_data["lf_password"]
    if "instance_name" in json_data:
        args.instance_name = json_data["instance_name"]
    if "config_name" in json_data:
        args.config_name = json_data["config_name"]
    if "upstream" in json_data:
        args.upstream = json_data["upstream"]
    if "dut" in json_data:
        args.dut = json_data["dut"]
    if "duration" in json_data:
        args.duration = json_data["duration"]
    if "station" in json_data:
        args.station = json_data["station"]

    # Traffic configuration
    for key in ["speed", "rate", "download_speed", "download_rate"]:
        if key in json_data:
            args.speed = json_data[key]

    for key in ["opposite_speed", "opposite_rate", "upload_speed", "upload_rate"]:
        if key in json_data:
            args.opposite_speed = json_data[key]

    args.traffic_directions = __apply_csv_json(
        json_data=json_data,
        arg_value=args.traffic_directions,
        keys=["direction", "directions", "traffic_direction", "traffic_directions"]
    )
    args.traffic_types = __apply_csv_json(
        json_data=json_data,
        arg_value=args.traffic_types,
        keys=["type", "types", "traffic_type", "traffic_types"]
    )

    # WiFi configuration
    args.spatial_streams = __apply_csv_json(
        json_data=json_data,
        arg_value=args.spatial_streams,
        keys=["nss", "spatial_streams"]
    )
    args.bandwidths = __apply_csv_json(
        json_data=json_data,
        arg_value=args.bandwidths,
        keys=["bandwidth", "bandwidths"]
    )
    args.channels = __apply_csv_json(
        json_data=json_data,
        arg_value=args.channels,
        keys=["channel", "channels"]
    )

    # Attenuators configuration
    for key in ["attenuator", "attenuator1"]:
        if key in json_data:
            args.attenuator = json_data[key]

    if "attenuator2" in json_data:
        args.attenuator2 = json_data["attenuator2"]

    for key in ["attenuations", "attenuations1"]:
        if key in json_data:
            args.attenuations = json_data[key]

    if "attenuations2" in json_data:
        args.attenuations2 = json_data["attenuations2"]

    # Other
    if "pull_report" in json_data:
        args.pull_report = json_data["pull_report"]
    if "raw_line" in json_data:
        # the json_data is a list , need to make into a list of lists, to match command line raw_line paramaters
        # https://www.tutorialspoint.com/convert-list-into-list-of-lists-in-python
        json_data_tmp = [[x] for x in json_data["raw_line"]]
        args.raw_line = json_data_tmp


def __apply_csv_json(arg_value: str, json_data: dict, keys: list) -> str:
    """Check and apply JSON for specified argument, overriding as necessary

    In case that user specifies an argument value and JSON value, JSON value
    takes precedence. However, same logic used when no CLI value passed and
    argument takes default value.

    Args:
        arg_value (str): CLI arguments value to be overriden by JSON
        json_data (dict): Full JSON data containing test settings/overrides
        keys (list): Possible keys for configuration item, matching CLI

    Returns:
        str: Configuration item value, overriden by JSON if present
    """
    json_item_data = None
    for key in keys:
        if key in json_data:
            json_item_data = json_data[key]

    if json_item_data:
        if not isinstance(json_item_data, str):
            logger.error("Unexpected data format in JSON data. Expected comma separated string "
                         f"found '{type(json_item_data)}'")
            exit(1)
        return json_item_data
    else:
        return arg_value


def main():
    args = parse_args()

    help_summary = (
    "The Dataplane test automates LANforge Chamber View throughput testing by "
    "generating traffic between a configured station and an upstream interface. "
    "It supports configurable traffic direction, traffic type, traffic rate, "
    "WiFi parameters (NSS, bandwidth, channel), attenuation profiles, and report "
    "generation. Multiple comma-separated values may be provided for supported "
    "parameters to automatically execute all valid test combinations. Test "
    "configuration can be supplied through command-line arguments or a JSON "
    "configuration file, with JSON values taking precedence."
)
    if args.help_summary:
        print(help_summary)
        exit(0)

    configure_logging(args)
    cv_base_adjust_parser(args)

    apply_json_configuration(args)
    validate_args(args)

    CV_Test = DataplaneTest(lf_host=args.mgr,
                            lf_port=args.port,
                            ssh_port=args.lf_ssh_port,
                            enables=args.enable,
                            disables=args.disable,
                            sets=args.set,
                            raw_lines=args.raw_line,
                            **vars(args))
    CV_Test.setup()
    CV_Test.run()

    if CV_Test.kpi_results_present():
        logger.info("lf_dataplane_test generated kpi.csv")
    else:
        logger.error('''\
        The test has finished but did not complete successfully,
        and no KPI.csv file could be generated. Possible causes
        could be displayed by the GUI CV test, a station could
        have the wrong SSID, passphrase or attempting to connect
        to the wrong BSSID. Please check error messages outputted
        earlier by this script, or check for exceptions in journalctl.
        ''')
        exit(1)

    if CV_Test.passes():
        CV_Test.exit_success()
    else:
        CV_Test.exit_fail()


if __name__ == "__main__":
    main()