#!/usr/bin/python3

import argparse
import base64
import importlib
from pathlib import Path


def main():

    # Let's get the plugins
    dir_path = Path(__file__) / "plugins"
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
        "-M", "--manufacturer", type=str, default=None, help="Specify the"
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
        choices=["cool", "dry", "fan", "off"],
        default="cool",
        help="Mode to set. (default 'cool').",
    )
    parser.add_argument(
        "-f",
        "--fan",
        choices=["auto", "highest", "high", "middle", "low", "lowest"],
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
        "-o", "--clear", action="store_true", default=False, help="Odour filter mode"
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
        print(f"Available modelas are: {PluginObject().MODELS.keys()}")

    device = PluginObject().factory(opts.model)

    frames = []
    device.set_temperature(opts.temp)
    device.set_fan(opts.fan)
    device.set_swing(opts.swing)
    device.set_powerfull((opts.powerfull and "on") or "off")
    device.set_purifier((opts.filter and "on") or "off")
    device.set_odourwash((opts.clear and "on") or "off")
    device.set_economy(opts.economy)
    device.set_mode(opts.mode)

    frames = device.build_ircode()

    if opts.lirc:
        lircf = device.to_lirc(frames)
        while lircf:
            print("\t".join(["%d" % x for x in lircf[:6]]))
            lircf = lircf[6:]
    elif opts.broadlink or opts.base64:
        lircf = device.to_lirc(frames)
        bframe = device.to_broadlink([int(x) for x in lircf])
        if opts.base64:
            print("{}".format(str(base64.b64encode(bframe), "ascii")))
        else:
            print("{}".format(bframe))
    else:
        for f in frames:
            print(" ".join([hex(x) for x in f]))
