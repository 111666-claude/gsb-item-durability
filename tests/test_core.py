import random
import unittest

from durability.core import Gear, Item, ItemError


class RegisterTest(unittest.TestCase):
    def test_register_keeps_full_durability(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertEqual(gear.items["sword"].durability, 100)

    def test_unknown_item_raises(self):
        with self.assertRaises(ItemError):
            Gear().use("missing", 10)


class UseTest(unittest.TestCase):
    def test_use_returns_true(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertTrue(gear.use("sword", 10))

    def test_use_reduces_durability(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 10)
        self.assertLess(gear.items["sword"].durability, 100)


class RepairTest(unittest.TestCase):
    def test_repair_restores_durability(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.repair("sword", 1000)
        self.assertEqual(gear.items["sword"].durability, 100)


class CumulativeWearTest(unittest.TestCase):
    def test_wear_accumulates_across_uses(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertTrue(gear.use("sword", 30))
        self.assertTrue(gear.use("sword", 30))
        self.assertEqual(gear.items["sword"].durability, 40)

    def test_wear_is_floored_at_zero(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 80)
        self.assertEqual(gear.items["sword"].durability, 20)
        self.assertFalse(gear.use("sword", 70))
        self.assertEqual(gear.items["sword"].durability, 0)


class BrokenItemTest(unittest.TestCase):
    def test_breaking_use_returns_false(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertFalse(gear.use("sword", 150))
        self.assertEqual(gear.items["sword"].durability, 0)

    def test_broken_item_stays_useless(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 100)
        self.assertFalse(gear.use("sword", 10))
        self.assertEqual(gear.items["sword"].durability, 0)
        self.assertFalse(gear.usable("sword"))

    def test_usable_only_above_zero(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertTrue(gear.usable("sword"))
        gear.use("sword", 99)
        self.assertTrue(gear.usable("sword"))
        gear.use("sword", 1)
        self.assertFalse(gear.usable("sword"))

    def test_unknown_item_is_not_usable(self):
        self.assertFalse(Gear().usable("missing"))


class RepairCostTest(unittest.TestCase):
    def test_cost_proportional_to_actual_loss(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertEqual(gear.repair_cost("sword"), 120)

    def test_full_durability_repairs_free(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        self.assertEqual(gear.repair_cost("sword"), 0)


class RepairValidationTest(unittest.TestCase):
    def test_insufficient_gold_rejected_without_change(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertFalse(gear.repair("sword", 119))
        self.assertEqual(gear.items["sword"].durability, 40)

    def test_exact_gold_charges_and_restores(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertEqual(gear.repair("sword", 120), 0)
        self.assertEqual(gear.items["sword"].durability, 100)

    def test_surplus_gold_returns_remainder(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertEqual(gear.repair("sword", 200), 80)
        self.assertEqual(gear.items["sword"].durability, 100)


class ScanCostTest(unittest.TestCase):
    def test_scanned_does_not_grow_with_item_count(self):
        gear = Gear()
        for index in range(5000):
            gear.register(Item("item-%d" % index, 100))
        for _ in range(2000):
            self.assertTrue(gear.usable("item-4999"))
        self.assertLessEqual(gear.scanned_count(), 2000)


class ReferenceGear:
    """独立参考实现：损耗累积 + 破损禁用 + 按损耗收费。"""

    def __init__(self, max_durability, price_per_point):
        self.max_durability = max_durability
        self.price_per_point = price_per_point
        self.durability = max_durability

    def use(self, wear):
        if self.durability == 0:
            return False
        self.durability = max(0, self.durability - wear)
        return self.durability > 0

    def repair_cost(self):
        return (self.max_durability - self.durability) * self.price_per_point

    def repair(self, gold):
        cost = self.repair_cost()
        if gold < cost:
            return False
        self.durability = self.max_durability
        return gold - cost


class ReferenceComparisonTest(unittest.TestCase):
    def test_random_sequences_match_reference(self):
        rng = random.Random(20260930)
        for _ in range(200):
            max_durability = rng.randint(1, 500)
            price_per_point = rng.randint(1, 5)
            gear = Gear(price_per_point=price_per_point)
            gear.register(Item("sword", max_durability))
            ref = ReferenceGear(max_durability, price_per_point)
            for _ in range(rng.randint(1, 60)):
                action = rng.choice(("use", "repair", "poor_repair"))
                if action == "use":
                    wear = rng.randint(0, max_durability * 2)
                    self.assertEqual(gear.use("sword", wear), ref.use(wear))
                else:
                    cost = gear.repair_cost("sword")
                    self.assertEqual(cost, ref.repair_cost())
                    if action == "poor_repair" and cost > 0:
                        gold = rng.randint(0, cost - 1)
                    else:
                        gold = rng.randint(cost, cost + 500)
                    self.assertEqual(gear.repair("sword", gold), ref.repair(gold))
                durability = gear.items["sword"].durability
                self.assertEqual(durability, ref.durability)
                self.assertGreaterEqual(durability, 0)
                self.assertLessEqual(durability, max_durability)
                self.assertEqual(gear.usable("sword"), ref.durability > 0)


if __name__ == "__main__":
    unittest.main()
