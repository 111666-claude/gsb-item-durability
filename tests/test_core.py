import random
import time
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


if __name__ == "__main__":
    unittest.main()


class AccumulatedWearTest(unittest.TestCase):
    def test_wear_accumulates_across_uses(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 30)
        gear.use("sword", 30)
        self.assertEqual(gear.items["sword"].durability, 40)

    def test_wear_many_uses_never_negative(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        for _ in range(20):
            gear.use("sword", 15)
        self.assertEqual(gear.items["sword"].durability, 0)

    def test_last_use_that_breaks_returns_false(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertTrue(gear.use("sword", 40))
        self.assertTrue(gear.use("sword", 40))
        self.assertFalse(gear.use("sword", 40))

    def test_wear_larger_than_durability_clamps_to_zero(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        self.assertFalse(gear.use("sword", 150))
        self.assertEqual(gear.items["sword"].durability, 0)


class BrokenItemTest(unittest.TestCase):
    def test_broken_item_is_not_usable(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 100)
        self.assertFalse(gear.usable("sword"))

    def test_broken_item_cannot_be_used_again(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        gear.use("sword", 100)
        self.assertFalse(gear.use("sword", 10))
        self.assertEqual(gear.items["sword"].durability, 0)

    def test_unknown_item_is_not_usable(self):
        self.assertFalse(Gear().usable("missing"))


class RepairCostTest(unittest.TestCase):
    def test_cost_matches_actual_loss(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertEqual(gear.repair_cost("sword"), 120)

    def test_cost_zero_at_full_durability(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        self.assertEqual(gear.repair_cost("sword"), 0)

    def test_cost_full_after_break(self):
        gear = Gear(price_per_point=3)
        gear.register(Item("sword", 100))
        gear.use("sword", 100)
        self.assertEqual(gear.repair_cost("sword"), 300)


class RepairValidationTest(unittest.TestCase):
    def test_repair_deducts_only_actual_cost(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        gold = 1000
        cost = gear.repair_cost("sword")
        self.assertTrue(gear.repair("sword", gold))
        self.assertEqual(gold - cost, 880)

    def test_repair_with_exact_gold_succeeds(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertTrue(gear.repair("sword", 120))
        self.assertEqual(gear.items["sword"].durability, 100)

    def test_repair_with_insufficient_gold_is_rejected(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 60)
        self.assertFalse(gear.repair("sword", 119))
        self.assertEqual(gear.items["sword"].durability, 40)

    def test_broken_item_can_be_repaired_then_used(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 100))
        gear.use("sword", 100)
        self.assertTrue(gear.repair("sword", 200))
        self.assertEqual(gear.items["sword"].durability, 100)
        self.assertTrue(gear.use("sword", 10))


class InvariantTest(unittest.TestCase):
    def test_durability_always_within_bounds(self):
        gear = Gear(price_per_point=2)
        gear.register(Item("sword", 50))
        for wear in (0, 20, 40, 1, 99):
            gear.use("sword", wear)
            durability = gear.items["sword"].durability
            self.assertGreaterEqual(durability, 0)
            self.assertLessEqual(durability, 50)
            gear.repair("sword", 10000)

    def test_non_positive_max_durability_rejected(self):
        with self.assertRaises(ItemError):
            Item("bad", 0)

    def test_negative_wear_rejected(self):
        gear = Gear()
        gear.register(Item("sword", 100))
        with self.assertRaises(ItemError):
            gear.use("sword", -1)


class QueryCostTest(unittest.TestCase):
    def test_single_query_costs_one_scan(self):
        gear = Gear()
        for index in range(2000):
            gear.register(Item("item-%d" % index, 100))
        before = gear.scanned_count()
        gear.usable("item-1999")
        self.assertEqual(gear.scanned_count() - before, 1)

    def test_scan_count_does_not_grow_with_item_count(self):
        counts = []
        for total in (500, 2000, 5000):
            gear = Gear()
            for index in range(total):
                gear.register(Item("item-%d" % index, 100))
            gear.usable("item-0")
            counts.append(gear.scanned_count())
        self.assertEqual(len(set(counts)), 1)


class ScaleTest(unittest.TestCase):
    def test_5000_items_handles_100k_ops_per_second(self):
        gear = Gear(price_per_point=2)
        for index in range(5000):
            gear.register(Item("item-%d" % index, 100))
        start = time.perf_counter()
        for step in range(100000):
            item_id = "item-%d" % (step % 5000)
            if step % 2 == 0:
                gear.use(item_id, 1)
            else:
                gear.usable(item_id)
            if step % 5000 == 4999:
                gear.repair(item_id, 1000000)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 2.0)


class ReferenceModelTest(unittest.TestCase):
    def test_random_sequences_match_reference(self):
        rng = random.Random(20260930)
        sequences = 200
        for _ in range(sequences):
            gear = Gear(price_per_point=rng.randint(1, 5))
            max_durability = rng.randint(1, 120)
            gear.register(Item("sword", max_durability))
            ref_durability = max_durability
            gold = rng.randint(0, 400)

            for _ in range(rng.randint(5, 40)):
                action = rng.random()
                if action < 0.55:
                    wear = rng.randint(0, max_durability * 2)
                    got = gear.use("sword", wear)
                    if ref_durability > 0:
                        ref_durability = max(0, ref_durability - wear)
                        want = ref_durability > 0
                    else:
                        want = False
                    self.assertIs(got, want)
                elif action < 0.8:
                    cost = gear.repair_cost("sword")
                    want_cost = (max_durability - ref_durability) * gear.price_per_point
                    self.assertEqual(cost, want_cost)
                    got = gear.repair("sword", gold)
                    want = gold >= want_cost
                    self.assertIs(got, want)
                    if want:
                        gold -= want_cost
                        ref_durability = max_durability
                else:
                    self.assertIs(gear.usable("sword"), ref_durability > 0)
                self.assertEqual(gear.items["sword"].durability, ref_durability)

    def test_repeated_sequence_is_deterministic(self):
        def run():
            gear = Gear(price_per_point=2)
            gear.register(Item("sword", 100))
            results = []
            gold = 300
            for wear in (30, 30, 50, 10):
                results.append(gear.use("sword", wear))
            results.append(gear.repair_cost("sword"))
            results.append(gear.repair("sword", gold))
            gold -= results[-2] if results[-1] else 0
            results.append(gear.repair("sword", gold))
            results.append(gear.items["sword"].durability)
            results.append(gear.usable("sword"))
            return results
        self.assertEqual(run(), run())
