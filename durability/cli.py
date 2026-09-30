"""命令行入口：跑装备耐久样例。"""

import argparse

from .core import Gear, Item


def build_parser():
    parser = argparse.ArgumentParser(prog="item-durability", description="装备耐久")
    parser.add_argument("--sample", default="wear", help="wear / broken / repair / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "wear":
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 30)
        gear.use("sword", 30)
        print("durability=%d" % gear.items["sword"].durability)
    elif args.sample == "broken":
        gear = Gear()
        gear.register(Item("sword", 100))
        ok = gear.use("sword", 150)
        print("ok=%s durability=%d" % (str(ok).lower(), gear.items["sword"].durability))
    elif args.sample == "repair":
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        print("cost=%d" % gear.repair_cost("sword"))
    elif args.sample == "scan":
        gear = Gear()
        for index in range(2000):
            gear.register(Item("item-%d" % index, 100))
        for _ in range(2000):
            gear.usable("item-1999")
        print("scanned=%d" % gear.scanned_count())
    else:
        raise SystemExit("需要 --sample wear|broken|repair|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
