# item-durability

装备耐久：损耗累积、破损禁用、按实际损耗收修理费，只用 Python 标准库。

```
python3 -m durability.cli --sample wear
python3 -m durability.cli --sample broken
python3 -m durability.cli --sample repair
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **损耗累积**：每次使用把耐久减去 `wear`，下限为 0；耐久到 0 之后不能再使用
  （`use` 返回 `False`），`usable` 只在耐久大于 0 时为真。
- **修理费按实际损耗**：`repair_cost = (max_durability - durability) * price_per_point`。
- **修理校验**：金币不足时拒绝并返回 `False`（不改耐久）；够的话扣掉费用并把耐久回满。
- **查询代价**：`usable` 不许每次全表扫描，`scanned_count()` 不随装备数线性增长。
- **规模**：单个角色 5000 件装备、每秒 10 万次使用与查询，单次 O(1)，内存 O(装备数)。

## 输出契约（不改格式）

```
durability=40
ok=false durability=0
cost=120
scanned<=2000
```

## 目录

```
durability/core.py   耐久、修理与查询
durability/cli.py    命令行入口
tests/               unittest 用例
```
