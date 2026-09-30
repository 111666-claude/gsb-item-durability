"""装备耐久：损耗累积、破损禁用、按实际损耗收修理费。"""


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
        """使用一次：耐久减去 wear，下限 0；耐久为 0 时返回 False。"""
        item = self.items.get(item_id)
        if item is None:
            raise ItemError("没有这件装备：%s" % item_id)
        if item.durability <= 0:
            return False
        item.durability = min(item.max_durability, max(0, item.durability - wear))
        return item.durability > 0

    def usable(self, item_id):
        """O(1) 查询：装备存在且耐久大于 0 才可用。"""
        self.scanned += 1
        item = self.items.get(item_id)
        return item is not None and item.durability > 0

    def repair_cost(self, item_id):
        """修理费：按实际损耗 (max_durability - durability) * price_per_point。"""
        item = self.items.get(item_id)
        if item is None:
            raise ItemError("没有这件装备：%s" % item_id)
        return (item.max_durability - item.durability) * self.price_per_point

    def repair(self, item_id, gold):
        """修理：金币不足返回 False 且不改耐久；够的话扣费并把耐久回满。"""
        cost = self.repair_cost(item_id)
        if gold < cost:
            return False
        self.items[item_id].durability = self.items[item_id].max_durability
        return gold - cost

    def scanned_count(self):
        return self.scanned
