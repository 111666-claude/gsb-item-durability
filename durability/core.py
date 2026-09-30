"""装备耐久：损耗累积、破损禁用、按实际损耗收修理费。

缺陷：每次使用都把损耗重置、破损之后还能用、修理费按满耐久算、耐久会扣成负数、查询全表扫描。
"""


class ItemError(ValueError):
    """装备操作不合法。"""


class Item:
    """一件装备。"""

    def __init__(self, item_id, max_durability):
        self.item_id = item_id
        self.max_durability = max_durability
        self.durability = max_durability


class Gear:
    """装备台账。"""

    def __init__(self, price_per_point=2):
        self.price_per_point = price_per_point
        self.items = {}
        self.scanned = 0

    def register(self, item):
        self.items[item.item_id] = item

    def use(self, item_id, wear):
        """使用一次。缺陷：把耐久重置成 max 减 wear（损耗不累积），破损后也返回 True。"""
        item = self.items.get(item_id)
        if item is None:
            raise ItemError("没有这件装备：%s" % item_id)
        item.durability = item.max_durability - wear
        return True

    def usable(self, item_id):
        """缺陷：只看装备在不在，不看耐久。"""
        self.scanned += len(self.items)
        return item_id in self.items

    def repair_cost(self, item_id):
        """修理费。缺陷：按满耐久算，与实际损耗无关。"""
        item = self.items.get(item_id)
        if item is None:
            raise ItemError("没有这件装备：%s" % item_id)
        return item.max_durability * self.price_per_point

    def repair(self, item_id, gold):
        """修理。缺陷：不看金币够不够，也不按实际损耗收费。"""
        cost = self.repair_cost(item_id)
        self.items[item_id].durability = self.items[item_id].max_durability
        return gold - cost

    def scanned_count(self):
        return self.scanned
