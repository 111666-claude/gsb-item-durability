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
