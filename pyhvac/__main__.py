#!/usr/bin/python3

import argparse
import base64
import importlib
import sys
from pathlib import Path


def main():

    # Let's get the plugins
    dir_path = Path(__file__).parent / "plugins"
    plugs = {}
    for filename in dir_path.iterdir():
        if filename.name == "hvaclib.py":
            continue
        if filename.suffix == ".py" and not filename.stem.startswith("__"):
            mod = importlib.import_module(".plugins." + filename.stem, package="pyhvac")
            thisplug = mod.PluginObject()
            plugs[thisplug.brand] = thisplug

    parser = argparse.ArgumentParser(description="Decode LIRC IR code into frames.")
    # version="%prog " + __version__ + "/" + bl.__version__)
    parser.add_argument(
        "-c",
        "--manufacturer",
        type=str.lower,
        default=None,
        help="Specify the A/C brand.",
    )
    parser.add_argument(
        "-M",
        "--model",
        type=str,
        default="generic",
        help="Set the A/C model. (default generic).",
    )
    parser.add_argument(
        "-L",
        "--list",
        action="store_true",
        default=False,
        help="List known models and return.",
    )
    parser.add_argument(
        "-t", "--temp", type=int, default=25, help="Temperature (°C). (default 25)."
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["auto", "cool", "dry", "fan", "off"],
        default="cool",
        help="Mode to set. (default 'cool').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "highest", "high", "medium", "low", "lowest"],
        default="auto",
        help="Fan mode. (default 'auto').",
    )
    parser.add_argument(
        "-s", "--swing", action="store_true", default=False, help="Set swing"
    )
    parser.add_argument(
        "-p", "--powerfull", action="store_true", default=False, help="Set powerfull"
    )
    parser.add_argument(
        "-e",
        "--economy",
        choices=["on", "off", "80", "60", "40"],
        default="off",
        help="Economy mode. (default 'off').",
    )
    parser.add_argument(
        "-n",
        "--filter",
        action="store_true",
        default=False,
        help="Particulate filter mode",
    )
    parser.add_argument(
        "-o", "--clean", action="store_true", default=False, help="Odour filter mode"
    )
    parser.add_argument(
        "-l",
        "--lirc",
        action="store_true",
        default=False,
        help="Output LIRC compatible timing",
    )
    parser.add_argument(
        "-b",
        "--broadlink",
        action="store_true",
        default=False,
        help="Output Broadlink timing",
    )
    parser.add_argument(
        "-B",
        "--base64",
        action="store_true",
        default=False,
        help="Output Broadlink timing in base64 encoded",
    )

    try:
        opts = parser.parse_args()
    except Exception as e:
        parser.error("Error: " + str(e))

    if opts.list:
        lofm = {}
        for m in plugs:
            lofm[m] = [x for x in plugs[m].MODELS.keys()]
        print("Available Brand/models are:")
        for b, l in sorted(lofm.items()):
            allspaces = len(b) + 2
            addme = " "
            print(f"{b}:", end="")
            for m in l:
                print(f"{addme}{m}")
                addme = " " * allspaces
        sys.exit(0)

    if opts.manufacturer in plugs:
        device = plugs[opts.manufacturer].get_device(opts.model)
    else:
        print(f"Error: Manufacturer {opts.manufacturer} is not supported.")
        sys.exit(2)

    frames = []
    device.set_value("set_temperature", opts.temp)
    device.set_value("set_fan", opts.fan)
    device.set_value("set_swing", opts.swing)
    device.set_value("set_powerfull", (opts.powerfull and "on") or "off")
    device.set_value("set_purifier", (opts.filter and "on") or "off")
    device.set_value("set_cleaning", (opts.clean and "on") or "off")
    device.set_value("set_economy", opts.economy)
    device.set_mode(opts.mode)

    frames = device.build_ircode()

    if opts.lirc:
        lircf = device.to_lirc(frames)
        while lircf:
            print("\t".join(["%d" % x for x in lircf[:6]]))
            lircf = lircf[6:]
    elif opts.broadlink or opts.base64:
        bframe = device.to_broadlink(frames)
        if opts.base64:
            print("{}".format(str(base64.b64encode(bframe), "ascii")))
        else:
            print("{}".format(bframe.hex()))
    else:
        for f in frames:
            print(" ".join([hex(x) for x in f]))
