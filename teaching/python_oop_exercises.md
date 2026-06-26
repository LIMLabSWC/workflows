# Python OOP exercises — from variables to dataclasses

A hands-on path for OOP ideas used in `bg_viz_pipeline` (`@dataclass`,
`frozen`, `@classmethod`, type hints, settings bundles).

**Which code does this track?** The pipeline uses a **`SETTINGS` dict** in
`interactive_render.py` and **`settings_from_preset()`** in `lib/core.py`.
Parts 0–10 build up to that pattern (dicts in Part 0/8/10; Part 11 reads the
real files). Parts 6–10 also teach **dataclasses** as the same idea in a
stricter form.

**Learning branch:** A modular **`ViewConfig`** dataclass version lives on
`refactor-to-batch-and-interactive` (`lib/view_config.py`, `scene_pipeline.py`).
Use that branch if you want to trace frozen dataclasses in production code.

**How to use this file**

1. Create a folder, e.g. `teaching/my_practice/`.
2. For each exercise, make a new file (`ex01_car.py`, `ex02_house.py`, …).
3. Run with: `python ex01_car.py`
4. Only peek at the “Example answer” sections after you’ve tried yourself.

You do **not** need brainrender or the atlas for any of this.

---

## Part 0 — Warm-up (5 minutes)

If these feel shaky, spend a day here before Part 1.

### Exercise 0.1 — Variables and functions

```python
# ex00_warmup.py

def describe_pet(name: str, age: int) -> str:
  # TODO: return a sentence like "Bella is 3 years old."
  pass

print(describe_pet("Bella", 3))
```

### Exercise 0.2 — Dicts (like JSON presets)

```python
preset = {
    "CAMERA_ROTATION_DEG": -45.0,
    "SLICE_MODE": "custom",
}

# TODO: print rotation, or -999 if the key is missing (use .get)
```

### Exercise 0.3 — Lists and loops

```python
regions = ["M2", "VLO", "LO"]

# TODO: print each region on its own line with a for loop
```

---

## Part 1 — What is a class? (Car, no magic)

A **class** is a blueprint. An **object** (or **instance**) is one concrete thing
built from that blueprint.

Think: `Car` = blueprint, `my_car` = your actual car.

### Exercise 1.1 — Empty car blueprint

```python
# ex01_car_class.py

class Car:
    pass  # empty for now


my_car = Car()
your_car = Car()

print(type(my_car))   # should say <class '__main__.Car'>
print(my_car is your_car)  # False — two different objects
```

**Question:** Why are `my_car` and `your_car` not the same object?

### Exercise 1.2 — Attach data to a car (the naive way)

Before `__init__`, people sometimes set attributes by hand:

```python
class Car:
    pass

my_car = Car()
my_car.brand = "Toyota"
my_car.color = "red"

# TODO: create your_car with brand "Volvo" and color "blue"
# TODO: print both colors
```

This works but gets repetitive — that’s why we use `__init__` next.

---

## Part 2 — `__init__` and `self`

`__init__` runs when you **construct** a new object: `Car(...)`.

`self` means **“this particular car”** inside the class.

### Exercise 2.1 — Car with constructor

```python
# ex02_car_init.py

class Car:
    def __init__(self, brand: str, color: str):
        self.brand = brand
        self.color = color


my_car = Car("Toyota", "red")

# TODO: create two more cars
# TODO: print my_car.brand and my_car.color
```

### Exercise 2.2 — House class

```python
# ex02_house.py

class House:
    def __init__(self, address: str, rooms: int, has_garden: bool):
        # TODO: save address, rooms, has_garden on self
        pass


home = House("12 Oak Street", 4, True)

# TODO: print a sentence describing the house
```

---

## Part 3 — Methods (functions on the object)

A **method** is a function defined inside a class. First argument is always `self`.

### Exercise 3.1 — Car methods

```python
# ex03_car_methods.py

class Car:
    def __init__(self, brand: str, fuel_liters: float):
        self.brand = brand
        self.fuel_liters = fuel_liters

    def drive(self, kilometers: float) -> None:
        # Pretend: 1 liter per 10 km
        used = kilometers / 10.0
        self.fuel_liters -= used
        print(f"Drove {kilometers} km. Fuel left: {self.fuel_liters:.1f} L")

    def describe(self) -> str:
        # TODO: return f"{self.brand}, fuel: {self.fuel_liters} L"
        pass


car = Car("Toyota", 40.0)
car.drive(50)
print(car.describe())
```

### Exercise 3.2 — House method

Add `def total_area(self, sqm_per_room: float) -> float` that returns
`rooms * sqm_per_room`.

---

## Part 4 — Type hints (labels, not rules)

Type hints describe intent. Python **does not** enforce them at runtime.

```python
age: int = 25
name: str = "Alex"
maybe_name: str | None = None   # string or None
```

### Exercise 4.1 — Annotate the car

Add type hints to your `Car.__init__` and methods (`-> str`, `-> None`, etc.).

Run the file — behaviour should be identical.

### Exercise 4.2 — Literal (only these strings allowed)

```python
from typing import Literal

FuelType = Literal["petrol", "diesel", "electric"]

class Car:
    def __init__(self, brand: str, fuel: FuelType):
        self.brand = brand
        self.fuel = fuel
```

**Question:** In `lib/core.py`, preset JSON uses keys like `"MESH_MODE": "root"`.
In `interactive_render.py`, the same idea is `"mesh_mode": "root"` in `SETTINGS`.
On branch `refactor-to-batch-and-interactive`, `view_config.py` uses
`MeshMode = Literal["root", "regions"]` — why might you prefer `Literal` over
plain `str`?

---

## Part 5 — What is a decorator? (`@something`)

A **decorator** wraps a function or class to add behaviour.

You’ve seen:

```python
@dataclass
class ViewConfig:
    ...
```

Read `@dataclass` as: **“Python, please generate extra boilerplate for this class.”**

(On this branch, render settings are a plain dict; on
`refactor-to-batch-and-interactive` they are a `@dataclass(frozen=True)` called
`ViewConfig` — same role, different packaging.)

### Exercise 5.1 — A tiny decorator (read first, then type)

```python
# ex05_decorator.py

def shout(func):
    """Call func, but print 'START' and 'END' around it."""
    def wrapper():
        print("START")
        func()
        print("END")
    return wrapper


@shout
def greet():
    print("Hello!")


greet()
# Expected output:
# START
# Hello!
# END
```

**Question:** What would happen if you removed `@shout` and only called `greet()`?

### Exercise 5.2 — Decorator with arguments (optional stretch)

Skip if tired — come back later. Decorators are sugar; you can always write
the long form.

---

## Part 6 — Dataclass — less boilerplate

Compare **manual class** vs **dataclass** for the same data.

### Exercise 6.1 — House without dataclass (feel the pain)

```python
# ex06_house_manual.py

class House:
    def __init__(self, address: str, rooms: int):
        self.address = address
        self.rooms = rooms

    def __repr__(self):
        return f"House(address={self.address!r}, rooms={self.rooms})"


h = House("12 Oak", 3)
print(h)
```

### Exercise 6.2 — Same house with `@dataclass`

```python
# ex06_house_dataclass.py

from dataclasses import dataclass


@dataclass
class House:
    address: str
    rooms: int


h = House("12 Oak", 3)
print(h)  # dataclass gives you a nice print for free
```

**TODO:** Add `has_garden: bool = False` (default = optional when constructing).

**Question:** How many lines did `@dataclass` save you?

### Exercise 6.3 — Car as dataclass

```python
from dataclasses import dataclass

@dataclass
class Car:
    brand: str
    color: str
    fuel_liters: float = 50.0

# TODO: create two cars, print them
```

---

## Part 7 — `frozen=True` (immutable config)

`frozen=True` means: after creation, you **cannot** change fields.

Like a preset snapshot — good for “settings for this one render”.

### Exercise 7.1 — Try to break it

```python
# ex07_frozen.py

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraSettings:
    distance: float
    rotation_deg: float
    elevation_deg: float


cam = CameraSettings(4.0, -45.0, -30.0)
print(cam.rotation_deg)

# TODO: uncomment the next line and run — what error do you get?
# cam.rotation_deg = 0.0
```

**Question:** Why treat render settings as fixed for one run (dict you don’t
mutate mid-pipeline, or a `frozen` dataclass on the learning branch)?

### Exercise 7.2 — New object instead of mutation

If you need different settings, build a **new** instance:

```python
cam2 = CameraSettings(cam.distance, 0.0, cam.elevation_deg)
```

---

## Part 8 — `@classmethod` (factory on the class)

A normal method uses `self` (one instance).
A **classmethod** uses `cls` (the class itself) — often to **construct** objects
from different sources.

### Exercise 8.1 — House from a dict (like JSON preset)

```python
# ex08_classmethod.py

from dataclasses import dataclass


@dataclass(frozen=True)
class House:
    address: str
    rooms: int
    has_garden: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "House":
        # cls is House — calling cls(...) builds a new House
        return cls(
            address=data["address"],
            rooms=int(data["rooms"]),
            has_garden=bool(data.get("has_garden", False)),
        )


raw = {"address": "12 Oak", "rooms": 4, "has_garden": True}
h = House.from_dict(raw)
print(h)
```

**TODO:** Add `from_csv_row(cls, row: list[str])` that expects
`[address, rooms, "yes"|"no"]`.

**Link to pipeline:** `core.settings_from_preset(...)` in `lib/core.py` does
the same job for `viewer_presets.json` (JSON UPPER_SNAKE → `SETTINGS`-style
lower_snake keys).

---

## Part 9 — `from __future__ import annotations`

Put at the **top** of a file (before other imports):

```python
from __future__ import annotations
```

It tells Python: **store type hints as text**, don’t evaluate them immediately.

### Exercise 9.1 — See the difference (optional)

File A — without future:

```python
class Node:
    def child(self) -> Node:  # may error on some Python versions
        ...
```

File B — with future:

```python
from __future__ import annotations

class Node:
    def child(self) -> Node:  # fine — "Node" is just a label here
        ...
```

**Takeaway:** It’s a convenience for type hints. Your viz code runs the same.

---

## Part 10 — Put it together — mini settings bundle

Build a tiny version of the preset → settings translation. In the pipeline this
is a plain dict + `settings_from_preset()`; here you practice the same idea with
a dataclass (same pattern as `ViewConfig` on `refactor-to-batch-and-interactive`).

### Exercise 10.1 — `RenderSettings` dataclass

```python
# ex10_mini_view_config.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderSettings:
    camera_distance: float = 4.0
    camera_rotation_deg: float = -45.0
    slice_mode: str = "none"

    def describe(self) -> str:
        # TODO: one-line summary of all three fields
        pass

    @classmethod
    def from_preset(cls, preset: dict) -> RenderSettings:
        # TODO: read CAMERA_DISTANCE_FACTOR, CAMERA_ROTATION_DEG, SLICE_MODE
        # use .get with defaults matching the fields above
        pass


# --- interactive path (like interactive_render.py SETTINGS dict) ---
interactive = RenderSettings(
    camera_distance=4.0,
    camera_rotation_deg=-45.0,
    slice_mode="custom",
)

# --- batch path (like viewer_presets.json) ---
preset = {
    "CAMERA_DISTANCE_FACTOR": 3.5,
    "CAMERA_ROTATION_DEG": -30.0,
    "SLICE_MODE": "frontal",
}
batch = RenderSettings.from_preset(preset)

print(interactive)
print(batch)
print(interactive.describe())
```

### Exercise 10.2 — Map names like the real pipeline

Presets use `CAMERA_DISTANCE_FACTOR` in JSON; `SETTINGS` in
`interactive_render.py` uses `camera_distance_factor`. Your `from_preset` is the
**translation layer** (same job as `settings_from_preset()` in `core.py`).

**TODO:** Add a comment in your file listing 3 field pairs (JSON name → Python name).

---

## Part 11 — Read real code (guided)

Open these files **after** Parts 1–10:

| File | Look for |
|------|----------|
| `bg_viz_pipeline/lib/core.py` | constants, `settings_from_preset`, `apply_view` |
| `bg_viz_pipeline/scripts/interactive_render.py` | `SETTINGS` dict at top |
| `bg_viz_pipeline/scripts/batch_render.py` | reads JSON → `settings_from_preset` |

### Exercise 11.1 — Trace one value (interactive)

Pick `camera_rotation_deg` in the `SETTINGS` dict in `interactive_render.py`
and write the path:

1. Dict key in `SETTINGS` (and its value)
2. Which function in `main()` receives the whole `SETTINGS` dict first?
3. Which function in `core.py` reads `config["camera_rotation_deg"]` when
   building the camera?

### Exercise 11.2 — Trace one preset key (batch)

Pick `CAMERA_ROTATION_DEG` in one object in `viewer_presets.json`. Same three
steps, but start from JSON → `settings_from_preset()` → the settings dict passed
to `apply_view`.

<details>
<summary>Exercise 11.1 — sketch answer (interactive)</summary>

1. `SETTINGS["camera_rotation_deg"]` (e.g. `-45.0`)
2. `core.apply_view(scene, SETTINGS)` (after `create_scene` / `add_atlas_content`)
3. `make_camera` → `create_camera` (both in `core.py`; rotation used in
   `create_camera` as `rotation_deg`)

</details>

<details>
<summary>Exercise 11.2 — sketch answer (batch)</summary>

1. e.g. `"CAMERA_ROTATION_DEG": -45.0` in `viewer_presets.json`
2. `core.settings_from_preset(preset)` in `batch_render.render_one` →
   `settings["camera_rotation_deg"]`
3. `core.apply_view(scene, settings)` → `make_camera` → `create_camera`

</details>

### Optional — ViewConfig on the learning branch

If you checked out `refactor-to-batch-and-interactive`, repeat 11.1–11.2 using
`ViewConfig` / `scene_pipeline.apply_view` instead of `SETTINGS` / `core.apply_view`.

---

## Cheat sheet

| Concept | One sentence |
|---------|----------------|
| Class | Blueprint for grouped data + behaviour |
| `self` | This instance inside a method |
| `__init__` | Runs when you call `MyClass(...)` |
| Method | Function on an object; first arg `self` |
| Type hint | Label for humans/tools; optional at runtime |
| `@decorator` | Wraps function/class to add behaviour |
| `@dataclass` | Auto-writes `__init__`, `__repr__`, etc. |
| `frozen=True` | Fields cannot change after creation |
| `@classmethod` | Method on the class; often builds instances |
| `cls` | The class inside a classmethod (like `House`) |
| `.get(key, default)` | Dict lookup with fallback |
| `from __future__ import annotations` | Type hints stored as text |

---

## Suggested schedule

| Day | Parts | Time |
|-----|-------|------|
| 1 | 0–2 | 1–2 h |
| 2 | 3–5 | 1–2 h |
| 3 | 6–8 | 1–2 h |
| 4 | 9–11 | 1 h + reading real code |

Stop when tired. Re-do exercises without looking at answers — muscle memory matters
more than speed.

---

## Example answers (peek only after trying)

<details>
<summary>Exercise 2.1 — Car __init__</summary>

```python
class Car:
    def __init__(self, brand: str, color: str):
        self.brand = brand
        self.color = color
```
</details>

<details>
<summary>Exercise 6.2 — House dataclass with default</summary>

```python
@dataclass
class House:
    address: str
    rooms: int
    has_garden: bool = False
```
</details>

<details>
<summary>Exercise 10.1 — from_preset sketch</summary>

```python
@classmethod
def from_preset(cls, preset: dict) -> RenderSettings:
    return cls(
        camera_distance=float(preset.get("CAMERA_DISTANCE_FACTOR", 4.0)),
        camera_rotation_deg=float(preset.get("CAMERA_ROTATION_DEG", -45.0)),
        slice_mode=str(preset.get("SLICE_MODE", "none")),
    )

def describe(self) -> str:
    return (
        f"dist={self.camera_distance}, "
        f"rot={self.camera_rotation_deg}, "
        f"slice={self.slice_mode}"
    )
```
</details>

---

## When you’re ready

- Add the **live camera HUD** to `interactive_render` (orbit → read knob values).
- Change one preset field and re-run `batch_render` — you’ll recognize every step.

You don’t need to memorize decorators. You need to recognize: **settings
bundled in a dict (or dataclass) built from `SETTINGS` or JSON.** Everything
else is detail around that idea.
